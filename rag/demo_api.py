"""Local educational text lookup demo with Groq/OpenAI drafting; no case storage."""

import asyncio
import logging
import re
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

from rag import retrieval
from rag.policy import assess
from rag.conversation import needs_context, plan_turn
from rag.generation import DraftError, DraftSettings, RETRIEVAL_TIMEOUT_SECONDS, generate_answer


WEB = Path(__file__).resolve().parent / "demo_web"
ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
QUERY_TIMEOUT_SECONDS = 85
load_dotenv(ROOT / ".env", override=False)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    mode: Literal["auto", "documents"] = "documents"

    @model_validator(mode="after")
    def bound_history(self):
        if sum(len(item.content) for item in self.history) > 12000:
            raise ValueError("Conversation history exceeds 12000 characters")
        return self


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

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/api/config")
    def config():
        # Return only public UI metadata, never the settings object or API key.
        try:
            settings = DraftSettings.from_env(require_key=False)
            data = {"provider": settings.provider, "provider_label": settings.label,
                    "model": settings.model, "configured": bool(settings.api_key)}
        except DraftError:
            data = {"provider": None, "provider_label": "AI", "model": None, "configured": False}
        return JSONResponse(data, headers={"Cache-Control": "no-store"})

    async def handle_query(body: Query, request: Request):
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
                                 "answer": ("Chào bạn! Mình có thể cùng bạn trò chuyện, giải thích kiến thức, viết nội dung "
                                            "và hỗ trợ lập trình. Khi hỏi về xương, mình sẽ tìm nguồn trong tài liệu BoneScope. "
                                            "Bạn muốn bắt đầu với điều gì?") if body.mode == "auto" else
                                           "Xin chào! Mình có thể giúp bạn tìm và giải thích thông tin trong tài liệu BoneScope. Bạn muốn hỏi điều gì?",
                                 "passages": []}, headers={"Cache-Control": "no-store"})
        # Report setup failures before loading the local embedding model.
        history = [item.model_dump() for item in body.history]
        search_question = question
        try:
            settings = DraftSettings.from_env()
        except DraftError as exc:
            return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                status_code=exc.status_code, headers={"Cache-Control": "no-store"})
        if body.mode == "auto" or needs_context(question, history):
            policy_status, reason = assess(question, retrieval.load_config())
            # Keep existing scope/evidence guards for image/case, dose, and
            # unsupported disease queries. Ordinary off-topic questions may chat.
            if policy_status and reason != "outside_bone_tumor_corpus":
                return JSONResponse({"status": policy_status, "reason": reason,
                                     "answer_ready": False, "passages": []},
                                    headers={"Cache-Control": "no-store"})
            if policy_status or needs_context(question, history):
                try:
                    plan = await plan_turn(question, history, settings,
                                           force_search=body.mode == "documents" or policy_status is None)
                except DraftError as exc:
                    return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                        status_code=exc.status_code, headers={"Cache-Control": "no-store"})
                except Exception:
                    LOG.error("Unexpected %s conversation failure", settings.label)
                    raise HTTPException(status_code=502, detail="Chưa xử lý được hội thoại. "
                                        "Bạn thử diễn đạt lại câu hỏi nhé.") from None
                if plan["route"] == "chat":
                    return JSONResponse({"status": "conversation", "answer": plan["answer"],
                                         "answer_ready": False, "passages": [],
                                         "provider": settings.provider, "model": settings.model,
                                         "basis": "model_knowledge"}, headers={"Cache-Control": "no-store"})
                search_question = plan["question"]
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(retrieve_fn, search_question, top_k=5),
                timeout=RETRIEVAL_TIMEOUT_SECONDS,
            )
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
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Tra cứu tài liệu quá thời gian chờ. "
                                "Lần đầu có thể cần nạp mô hình tìm kiếm; hãy thử lại sau.") from None
        except Exception:
            LOG.exception("Local source lookup failed")
            raise HTTPException(status_code=503, detail="Source lookup unavailable") from None
        answer = None
        if status == "candidates_found":
            try:
                if history:
                    answer = await generate_answer(question, passages, settings, history=history)
                else:
                    answer = await generate_answer(question, passages, settings)
            except DraftError as exc:
                LOG.warning("%s draft failed: %s", settings.label, exc.code)
                return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                    status_code=exc.status_code, headers={"Cache-Control": "no-store"})
            except Exception:
                LOG.error("Unexpected %s draft failure", settings.label)
                raise HTTPException(status_code=502,
                                    detail=f"Không tạo được bản nháp từ {settings.label}. Hãy thử lại sau.") from None
        response = {"status": status, "reason": result["reason"],
                    "answer_ready": False, "passages": passages}
        if status == "candidates_found":
            response["answer"] = answer
            response["provider"] = settings.provider
            response["model"] = settings.model
        return JSONResponse(response, headers={"Cache-Control": "no-store"})

    @app.post("/api/query")
    async def query(body: Query, request: Request):
        try:
            async with asyncio.timeout(QUERY_TIMEOUT_SECONDS):
                return await handle_query(body, request)
        except TimeoutError:
            raise HTTPException(status_code=504, detail="Đã hết thời gian xử lý hội thoại. "
                                "Hãy thử câu hỏi ngắn hơn hoặc thử lại sau.") from None

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
