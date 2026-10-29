"""Local text-only retrieval demonstration; no answer generation or case storage."""

import logging
import os
import re
from pathlib import Path
from threading import Lock

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field

from rag import retrieval


WEB = Path(__file__).resolve().parent / "demo_web"
ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


def create_app(retrieve_fn=None):
    if retrieve_fn is None:
        engine = None
        guard = Lock()

        def retrieve_fn(question, *, top_k):
            nonlocal engine
            with guard:
                if engine is None:
                    engine = retrieval.Retriever()
                return retrieval.retrieve(question, engine=engine, top_k=top_k)

    app = FastAPI(title="BoneScope source lookup demo", version="0.1")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")

    def generate_answer(question, passages):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        from google import genai
        client = genai.Client(api_key=api_key)
        context = "\n\n".join(
            f"[S{i}] {p['title']} — {p['section']}\n{p['text']}"
            for i, p in enumerate(passages, 1)
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=(
                "Bạn là trợ lý học tập BoneScope. Trả lời bằng tiếng Việt, ngắn gọn, "
                "chỉ dựa vào CONTEXT. Gắn [Số nguồn] vào mỗi ý có căn cứ. "
                "Nếu context không đủ để trả lời, nói rõ điều chưa biết; không tự suy diễn. "
                "Không chẩn đoán, khuyến nghị điều trị, hoặc diễn giải ảnh/ca bệnh.\n\n"
                f"CÂU HỎI:\n{question}\n\nCONTEXT:\n{context}"
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response")
        return answer

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-store"})

    @app.post("/api/query")
    def query(body: Query, request: Request):
        origin = request.headers.get("origin")
        expected_origin = f"{request.url.scheme}://{request.headers['host']}"
        if origin is not None and origin != expected_origin:
            raise HTTPException(status_code=403, detail="Cross-origin request rejected")
        question = body.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="Question must be nonempty")
        normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", question.casefold())
        normalized = " ".join(normalized.split())
        greetings = {"xin chào", "chào", "chào bạn", "hello", "hi", "hey", "good morning", "good afternoon"}
        if normalized in greetings:
            return JSONResponse({"status": "greeting", "answer_ready": False,
                                 "answer": "Xin chào! Mình có thể giúp bạn tìm và giải thích thông tin trong tài liệu BoneScope. Bạn muốn hỏi điều gì?",
                                 "passages": []}, headers={"Cache-Control": "no-store"})
        try:
            result = retrieve_fn(question, top_k=5)
            if result.get("answer_ready") is not False:
                raise ValueError("Unexpected answer readiness")
            status = result["status"]
            if status not in {"candidates_found", "insufficient_evidence", "out_of_scope"}:
                raise ValueError("Unexpected retrieval status")
            hits = result["hits"]
            if bool(hits) != (status == "candidates_found"):
                raise ValueError("Retrieval status and passages disagree")
            passages = [
                {key: hit[key] for key in (
                    "chunk_id", "source_id", "title", "publisher", "url", "section",
                    "source_date", "license", "source_sha256", "text_sha256", "text"
                )}
                for hit in hits
            ]
        except Exception:
            LOG.exception("Local source lookup failed")
            raise HTTPException(status_code=503, detail="Source lookup unavailable") from None
        answer = None
        if status == "candidates_found":
            try:
                answer = generate_answer(question, passages)
            except Exception:
                LOG.exception("Gemini answer generation failed")
                raise HTTPException(status_code=502,
                                    detail="Không gọi được Gemini. Kiểm tra API key, model và kết nối mạng.") from None
        response = {"status": status, "reason": result["reason"],
                    "answer_ready": False, "passages": passages}
        if status == "candidates_found":
            response["answer"] = answer
        return JSONResponse(response, headers={"Cache-Control": "no-store"})

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
