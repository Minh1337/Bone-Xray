"""Real Chrome smoke test with a temporary SQLite DB and offline AI fixtures.

Run with: python -m pytest ui_tests/test_chatbot_browser.py -q
Set BONESCOPE_TEST_CHROME to an installed Chrome/Chromium executable if needed.
No user browser profile, API credential, image, or chat database is used.
"""
import asyncio
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time
from urllib.request import urlopen

from PIL import Image
import pytest
import uvicorn

from rag import chat_history, demo_api
from rag.generation import DraftError


def chrome_path():
    candidates = [os.getenv("BONESCOPE_TEST_CHROME"), shutil.which("chromium"),
                  shutil.which("google-chrome"), shutil.which("chrome"),
                  r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)


class ChromePage:
    def __init__(self, connection):
        self.connection = connection
        self.sequence = 0
        self.errors = []

    async def call(self, method, **params):
        self.sequence += 1
        identifier = self.sequence
        await self.connection.send(json.dumps({"id": identifier, "method": method, "params": params}))
        while True:
            message = json.loads(await asyncio.wait_for(self.connection.recv(), 12))
            if message.get("method") == "Runtime.exceptionThrown":
                self.errors.append(message["params"]["exceptionDetails"])
            if message.get("id") != identifier:
                continue
            assert "error" not in message, message
            return message.get("result", {})

    async def evaluate(self, expression):
        result = await self.call("Runtime.evaluate", expression=expression,
                                 awaitPromise=True, returnByValue=True)
        assert "exceptionDetails" not in result, result
        return result["result"].get("value")

    async def wait(self, predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if await self.evaluate(predicate):
                return
            await asyncio.sleep(.05)
        raise AssertionError(f"Browser state did not settle: {predicate}")

    async def click(self, selector):
        await self.evaluate(f"document.querySelector({json.dumps(selector)}).click()")

    async def send(self, question):
        await self.evaluate(f"document.querySelector('#question').value={json.dumps(question)};"
                            "document.querySelector('#question-form').requestSubmit()")
        await self.wait("!document.querySelector('#submit').disabled")

    async def open_chat(self, title):
        await self.wait(f"[...document.querySelectorAll('.saved-open')].some(n=>n.textContent==={json.dumps(title)})")
        await self.evaluate(f"[...document.querySelectorAll('.saved-open')].find(n=>n.textContent==={json.dumps(title)}).click()")
        await self.wait(f"document.querySelector('#messages .user p')?.textContent.startsWith({json.dumps(title)})")


@pytest.fixture
def offline_chatbot(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-no-network")
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/free")
    monkeypatch.setattr(demo_api, "btxrd_hash_index", lambda: {})
    image_calls = []

    async def image_answer(question, image_bytes, _mime, _settings, history=None, **kwargs):
        image_calls.append({"question": question, "raw": image_bytes, "history": history or []})
        if question == "Lỗi ảnh tạm thời" and sum(x["question"] == question for x in image_calls) == 1:
            raise DraftError("fixture_unavailable", "Lỗi giả lập để kiểm tra nút thử lại.")
        return "**Mô tả giả lập offline.** Đây là ảnh hình học dùng kiểm thử. [S1]", "vision-fixture"

    monkeypatch.setattr(demo_api, "generate_image_answer", image_answer)

    # Fail immediately if an unmocked provider path is reached.
    async def no_provider(*_args, **_kwargs):
        raise AssertionError("Browser smoke must never call an external provider")

    monkeypatch.setattr(demo_api, "generate_answer", no_provider)
    monkeypatch.setattr(demo_api, "plan_turn", no_provider)
    passage = {key: "offline-fixture" for key in (
        "chunk_id", "source_id", "title", "publisher", "url", "section",
        "source_date", "license", "source_sha256", "text_sha256", "text")}
    passage.update(title="Nguồn giả lập offline", url="https://example.invalid/reference")

    def lookup(_question, *, top_k):
        return {"status": "candidates_found", "reason": "unvalidated_candidates",
                "answer_ready": False, "hits": [passage][:top_k]}

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(demo_api.create_app(lookup), log_level="error", ws="none"))
    worker = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            assert worker.is_alive() and time.monotonic() < deadline, "Temporary test server failed to start"
            time.sleep(.05)
        yield f"http://127.0.0.1:{port}", image_calls
    finally:
        server.should_exit = True
        worker.join(timeout=10)
        listener.close()
        assert not worker.is_alive(), "Temporary test server failed to stop"


def test_browser_image_context_and_sqlite_lifecycle(offline_chatbot, tmp_path):
    executable = chrome_path()
    if not executable:
        pytest.skip("Installed Chrome/Chromium required; set BONESCOPE_TEST_CHROME")
    websockets = pytest.importorskip("websockets")
    origin, image_calls = offline_chatbot
    profile = tmp_path / "chrome-profile"
    chrome_log = (tmp_path / "chrome.log").open("w", encoding="utf-8")
    process = subprocess.Popen([
        executable, "--headless=new", "--remote-debugging-port=0",
        "--remote-debugging-address=127.0.0.1", f"--user-data-dir={profile}",
        "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-gpu",
        "--disable-component-update", "--disable-extensions", "--disable-sync",
        "--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost",
        "about:blank"], stdout=subprocess.DEVNULL, stderr=chrome_log)
    try:
        active_port = profile / "DevToolsActivePort"
        deadline = time.monotonic() + 12
        while not active_port.is_file():
            assert process.poll() is None and time.monotonic() < deadline, "Headless Chrome failed to start"
            time.sleep(.05)
        port = int(active_port.read_text().splitlines()[0])
        with urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5) as response:
            target = next(x for x in json.load(response) if x["type"] == "page")
        output = BytesIO()
        Image.new("RGB", (64, 64), "gray").save(output, "PNG")
        raw = output.getvalue()
        encoded = base64.b64encode(raw).decode("ascii")

        async def exercise():
            async with websockets.connect(target["webSocketDebuggerUrl"], max_size=8*1024*1024,
                                          proxy=None, compression=None) as connection:
                page = ChromePage(connection)
                await page.call("Runtime.enable")
                await page.call("Page.enable")
                await page.call("Page.navigate", url=origin)
                await page.wait("!!document.querySelector('#question') && typeof sendQuestion==='function'")
                await page.wait("document.querySelector('[data-provider-name]')?.textContent.includes('OpenRouter')")

                # Attach once; subsequent turns must resend the same in-memory File.
                await page.evaluate("{const bytes=Uint8Array.from(atob('"+encoded+"'),c=>c.charCodeAt(0));"
                                    "const dt=new DataTransfer();dt.items.add(new File([bytes],'smoke-image.png',{type:'image/png'}));"
                                    "const n=document.querySelector('#image-input');n.files=dt.files;n.dispatchEvent(new Event('change'));}")
                assert await page.evaluate("!document.querySelector('#image-attachment').hidden")
                await page.send("Lỗi ảnh tạm thời")
                await page.wait("!!document.querySelector('.error-message')")
                await page.send("Mô tả ảnh A")
                await page.wait("document.querySelectorAll('.saved-open').length===1")
                assert await page.evaluate("document.querySelector('#image-attachment').hidden && document.querySelector('#image-input').files.length===0")
                assert await page.evaluate("!document.querySelector('#image-context-banner').hidden")
                assert await page.evaluate("document.querySelectorAll('.source-card').length===1")
                assert await page.evaluate("document.querySelectorAll('.citation').length===0")

                # A retry created before the first save must keep its original image
                # after the draft key has migrated to a persisted conversation ID.
                await page.click(".error-message button")
                await page.wait("!document.querySelector('#submit').disabled")
                assert [x["question"] for x in image_calls] == ["Lỗi ảnh tạm thời", "Mô tả ảnh A", "Lỗi ảnh tạm thời"]
                await page.send("Giải thích thêm về ảnh này")
                assert len(image_calls) == 4
                assert all(x["raw"] == raw for x in image_calls)
                assert any(x["role"] == "assistant" for x in image_calls[-1]["history"])
                for i in range(4):
                    await page.send(f"Hỏi tiếp lượt dài {i}")
                assert len(image_calls) == 8
                assert all(len(x["history"]) <= 8 for x in image_calls)
                assert all(sum(len(m["content"]) for m in x["history"]) <= 9000 for x in image_calls)

                # New chats must not inherit A's image; switching back restores A.
                await page.click("#clear-chat")
                assert await page.evaluate("document.querySelector('#image-context-banner').hidden")
                await page.send("xin chào")
                await page.wait("document.querySelectorAll('.saved-open').length===2")
                assert len(image_calls) == 8
                await page.open_chat("Mô tả ảnh A")
                assert await page.evaluate("document.querySelector('#image-context-name').textContent.includes('smoke-image.png')")
                await page.send("Hỏi tiếp ảnh A sau khi đổi chat")
                assert len(image_calls) == 9 and image_calls[-1]["raw"] == raw

                await page.click("#remove-image-context")
                await page.send("xin chào")
                assert len(image_calls) == 9

                # Responsive controls remain reachable at small widths.
                for width, height in ((390, 844), (320, 568)):
                    await page.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
                                    deviceScaleFactor=1, mobile=True)
                    await page.wait("document.querySelector('#sidebar').inert")
                    assert await page.evaluate("document.documentElement.scrollWidth<=innerWidth"), width
                    assert await page.evaluate("document.querySelector('#question-form').getBoundingClientRect().right<=innerWidth"), width
                    await page.click("#menu-toggle")
                    assert await page.evaluate("document.querySelector('#main').inert")
                    await page.click("#sidebar-backdrop")
                    assert await page.evaluate("!document.querySelector('#main').inert")
                await page.call("Emulation.clearDeviceMetricsOverride")
                await page.click("#theme-toggle")
                assert await page.evaluate("document.documentElement.dataset.theme==='dark'")

                # Reload: only text/sources survive; the File must be attached again.
                await page.call("Page.reload")
                await page.wait("document.querySelectorAll('.saved-open').length===2")
                await page.open_chat("Mô tả ảnh A")
                assert await page.evaluate("!document.querySelector('#reattach-image-context').hidden")
                assert await page.evaluate("document.querySelector('#remove-image-context').hidden")
                assert await page.evaluate("document.querySelectorAll('.source-card').length===8")
                assert await page.evaluate("!!document.querySelector('#messages .assistant strong')")
                assert await page.evaluate("document.querySelectorAll('.citation').length===0")
                assert await page.evaluate("document.querySelector('.sources-heading').textContent.includes('ĐỌC THÊM')")
                assert await page.evaluate("document.documentElement.dataset.theme==='dark'")

                # Exercise rename/delete on the isolated test DB through the UI.
                await page.evaluate("window.prompt=()=> 'Chat A đã đổi tên'; window.confirm=()=>true")
                await page.evaluate("[...document.querySelectorAll('.saved-row')].find(n=>n.querySelector('.saved-open').textContent==='Mô tả ảnh A').querySelector('.saved-action').click()")
                await page.wait("[...document.querySelectorAll('.saved-open')].some(n=>n.textContent==='Chat A đã đổi tên')")
                await page.evaluate("[...document.querySelectorAll('.saved-row')].find(n=>n.querySelector('.saved-open').textContent==='Chat A đã đổi tên').querySelector('.saved-delete').click()")
                await page.wait("document.querySelectorAll('.saved-open').length===1")
                assert not page.errors, page.errors

        asyncio.run(exercise())
        remaining = chat_history.list_conversations()
        assert len(remaining) == 1 and remaining[0]["title"] == "xin chào"
        assert raw not in chat_history.DB_PATH.read_bytes()
        assert encoded.encode("ascii") not in chat_history.DB_PATH.read_bytes()
        assert b"smoke-image.png" not in chat_history.DB_PATH.read_bytes()
    finally:
        chrome_log.close()
        if process.poll() is not None and process.returncode:
            print((tmp_path / "chrome.log").read_text(encoding="utf-8", errors="replace")[-3000:])
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
