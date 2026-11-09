"""Start the local chatbot with readable dependency/port diagnostics."""
from __future__ import annotations

import argparse
import json
import socket
from urllib.request import ProxyHandler, build_opener

from tools.chatbot_doctor import inspect_workspace, print_checks


def existing_bonescope(port):
    try:
        with build_opener(ProxyHandler({})).open(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            body = json.loads(response.read(4096))
        return body.get("app") == "bonescope-chatbot" and body.get("status") == "ok"
    except (OSError, ValueError, AttributeError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    report = inspect_workspace()
    if report["status"] == "ERROR":
        print_checks(report)
        print("Startup stopped. Run: python -m tools.chatbot_doctor")
        return 1
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Do not use SO_REUSEADDR: another Windows process may own this port.
        listener.bind(("127.0.0.1", args.port))
    except OSError:
        listener.close()
        if existing_bonescope(args.port):
            print(f"BoneScope is already running: http://127.0.0.1:{args.port}/")
            print("Stop the earlier server (Shift+F5 or Ctrl+C) before restarting to load code changes.")
            return 0
        print(f"Port {args.port} is occupied or unavailable. No process was stopped.")
        print(f"Choose a free port, for example: python -m tools.run_chatbot --port {args.port + 1 if args.port < 65535 else 8765}")
        return 2
    try:
        import uvicorn
        class LocalServer(uvicorn.Server):
            async def startup(self, sockets=None):
                await super().startup(sockets=sockets)
                if self.started:
                    # Uvicorn omits its URL startup log for supplied sockets.
                    print(f"BoneScope ready at http://127.0.0.1:{args.port}/", flush=True)

        server = LocalServer(uvicorn.Config("rag.demo_api:app", host="127.0.0.1", port=args.port, workers=1, ws="none"))
        print(f"Starting BoneScope on port {args.port} | Stop with Ctrl+C", flush=True)
        for check in report["checks"]:
            if check["status"] == "WARN":
                print(f"[WARN] {check['name']}: {check['detail']}", flush=True)
        # Keep the reserved socket so a second process cannot take it between
        # the port check and uvicorn startup.
        server.run(sockets=[listener])
        return 0 if server.started else 1
    finally:
        listener.close()


if __name__ == "__main__":
    raise SystemExit(main())
