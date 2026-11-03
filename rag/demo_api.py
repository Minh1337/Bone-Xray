"""Local educational chatbot demo: source lookup, Groq/OpenAI drafting and an
optional image-classification case context. No case or chat storage on disk."""

import asyncio
import logging
import re
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

from rag import case_context as cases
from rag import retrieval
from rag.policy import assess
from rag.conversation import needs_context, plan_turn
from rag.generation import DraftError, DraftSettings, RETRIEVAL_TIMEOUT_SECONDS, generate_answer


WEB = Path(__file__).resolve().parent / "demo_web"
ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
QUERY_TIMEOUT_SECONDS = 85
NO_STORE = {"Cache-Control": "no-store"}
load_dotenv(ROOT / ".env", override=False)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class Query(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)
    mode: Literal["auto", "documents"] = "documents"
    # Opaque server-issued ID; scores are looked up server-side, never sent by the client.
    case_id: str | None = Field(default=None, min_length=16, max_length=64)

    @model_validator(mode="after")
    def bound_history(self):
        if sum(len(item.content) for item in self.history) > 12000:
            raise ValueError("Conversation history exceeds 12000 characters")
        return self


def check_origin(request):
    origin = request.headers.get("origin")
    expected_origin = f"{request.url.scheme}://{request.headers['host']}"
    if origin is not None and origin != expected_origin:
        raise HTTPException(status_code=403, detail="Cross-origin request rejected")


def default_predictor_loader():
    # Imported lazily so the text chatbot never loads torch unless a case is analysed.
    from xray_api import load_real
    return load_real()


def create_app(retrieve_fn=None, predictor_loader=None):
    if retrieve_fn is None:
        engine = None
        guard = Lock()

        def retrieve_fn(question, *, top_k):
            nonlocal engine
            with guard:
                if engine is None:
                    engine = retrieval.Retriever()
                return retrieval.retrieve(question, engine=engine, top_k=top_k)

    predictor_loader = predictor_loader or default_predictor_loader
    store = cases.CaseStore()
    model_guard = Lock()
    model_state = {"predictor": None, "info": None}

    def predict_case(file, meta):
        from xray_api import predict_upload
        if not model_guard.acquire(blocking=False):
            raise HTTPException(429, "Mô hình đang phân tích một ảnh khác; thử lại sau ít giây.",
                                headers={"Retry-After": "2"})
        try:
            if model_state["predictor"] is None:
                try:
                    model_state["predictor"], model_state["info"] = predictor_loader()
                except Exception:
                    LOG.exception("Image classifier could not be loaded")
                    raise HTTPException(503, "Chưa nạp được mô hình phân loại ảnh. Kiểm tra thư mục "
                                        "model/ và môi trường PyTorch, rồi khởi động lại máy chủ.") from None
            result = predict_upload(model_state["predictor"], file, meta,
                                    extra_check=cases.check_demo_metadata)
            return cases.build_record(result["ranked"], result["seconds"], model_state["info"])
        finally:
            model_guard.release()

    async def retrieve_passages(question):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(retrieve_fn, question, top_k=5),
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
        return status, result["reason"], passages

    def active_case(case_id):
        record = store.get(case_id)
        if record is None:
            raise HTTPException(410, "Ca ảnh đã hết hạn hoặc đã bị xóa. Hãy phân tích lại ảnh.")
        return record

    app = FastAPI(title="BoneScope source lookup demo", version="0.2")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html", headers=NO_STORE)

    @app.get("/api/config")
    def config():
        # Return only public UI metadata, never the settings object or API key.
        try:
            settings = DraftSettings.from_env(require_key=False)
            data = {"provider": settings.provider, "provider_label": settings.label,
                    "model": settings.model, "configured": bool(settings.api_key)}
        except DraftError:
            data = {"provider": None, "provider_label": "AI", "model": None, "configured": False}
        data["case_analysis"] = True
        return JSONResponse(data, headers=NO_STORE)

    @app.post("/api/case")
    async def create_case(request: Request, file: UploadFile = File(...), metadata: str = Form(...)):
        check_origin(request)
        from xray_api import parse_metadata
        try:
            meta = parse_metadata(metadata)
            record = await asyncio.to_thread(predict_case, file, meta)
        finally:
            file.file.close()
        case_id = store.add(record)
        return JSONResponse(cases.summary(case_id, record), headers=NO_STORE)

    @app.delete("/api/case/{case_id}")
    def delete_case(case_id: str, request: Request):
        check_origin(request)
        return JSONResponse({"deleted": store.remove(case_id)}, headers=NO_STORE)

    @app.post("/api/case/{case_id}/explain")
    async def explain(case_id: str, request: Request):
        check_origin(request)
        record = active_case(case_id)
        base = {"status": "case_explanation", "case_id": case_id, "answer_ready": False}
        query_text = cases.lookup_query(record)
        if query_text is None:
            return JSONResponse({**base, "basis": "server_template", "lookup": "not_allowed",
                                 "answer": cases.template_explanation(record), "passages": []},
                                headers=NO_STORE)
        status, reason, passages = await retrieve_passages(query_text)
        if status != "candidates_found":
            return JSONResponse({**base, "basis": "server_template", "lookup": status, "reason": reason,
                                 "answer": cases.template_explanation(record), "passages": []},
                                headers=NO_STORE)
        fallback = {**base, "basis": "server_template", "lookup": status, "passages": passages,
                    "answer": cases.template_explanation(record, sources_found=True)}
        try:
            settings = DraftSettings.from_env()
            answer = await cases.explain_case(record, passages, settings)
        except DraftError as exc:
            LOG.warning("Case explanation draft unavailable: %s", exc.code)
            return JSONResponse({**fallback, "draft_error": str(exc)}, headers=NO_STORE)
        except Exception:
            LOG.error("Unexpected case explanation failure")
            return JSONResponse({**fallback, "draft_error": "Không tạo được bản nháp AI."}, headers=NO_STORE)
        return JSONResponse({**base, "basis": "documents", "lookup": status, "passages": passages,
                             "answer": answer, "provider": settings.provider, "model": settings.model},
                            headers=NO_STORE)

    async def handle_query(body: Query, request: Request):
        check_origin(request)
        question = body.question.strip()
        if not question:
            raise HTTPException(status_code=422, detail="Question must be nonempty")
        case = None
        if body.case_id is not None:
            case = cases.llm_context(active_case(body.case_id))
        case_kwargs = {"case_context": case, "extra_instructions": cases.CASE_ADDENDUM} if case else {}
        normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", question.casefold())
        normalized = " ".join(normalized.split())
        greetings = {"xin chào", "chào", "chào bạn", "hello", "hi", "hey", "good morning", "good afternoon"}
        if normalized in greetings:
            return JSONResponse({"status": "greeting", "answer_ready": False,
                                 "answer": ("Chào bạn! Mình có thể cùng bạn trò chuyện, giải thích kiến thức, viết nội dung "
                                            "và hỗ trợ lập trình. Khi hỏi về xương, mình sẽ tìm nguồn trong tài liệu BoneScope. "
                                            "Bạn muốn bắt đầu với điều gì?") if body.mode == "auto" else
                                           "Xin chào! Mình có thể giúp bạn tìm và giải thích thông tin trong tài liệu BoneScope. Bạn muốn hỏi điều gì?",
                                 "passages": []}, headers=NO_STORE)
        # Report setup failures before loading the local embedding model.
        history = [item.model_dump() for item in body.history]
        search_question = question
        try:
            settings = DraftSettings.from_env()
        except DraftError as exc:
            return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                status_code=exc.status_code, headers=NO_STORE)
        if body.mode == "auto" or needs_context(question, history):
            policy_status, reason = assess(question, retrieval.load_config())
            # Keep existing scope/evidence guards for image/case, dose, and
            # unsupported disease queries. Ordinary off-topic questions may chat.
            if policy_status and reason != "outside_bone_tumor_corpus":
                blocked = {"status": policy_status, "reason": reason, "answer_ready": False, "passages": []}
                if case:
                    blocked["case_hint"] = True
                return JSONResponse(blocked, headers=NO_STORE)
            if policy_status or needs_context(question, history):
                try:
                    plan = await plan_turn(question, history, settings,
                                           force_search=body.mode == "documents" or policy_status is None,
                                           **case_kwargs)
                except DraftError as exc:
                    return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                        status_code=exc.status_code, headers=NO_STORE)
                except Exception:
                    LOG.error("Unexpected %s conversation failure", settings.label)
                    raise HTTPException(status_code=502, detail="Chưa xử lý được hội thoại. "
                                        "Bạn thử diễn đạt lại câu hỏi nhé.") from None
                if plan["route"] == "chat":
                    reply = {"status": "conversation", "answer": plan["answer"],
                             "answer_ready": False, "passages": [],
                             "provider": settings.provider, "model": settings.model,
                             "basis": "model_knowledge"}
                    if case:
                        reply["case_context_used"] = True
                    return JSONResponse(reply, headers=NO_STORE)
                search_question = plan["question"]
        status, reason, passages = await retrieve_passages(search_question)
        if case and status != "candidates_found" and reason == "image_requires_specialist_assessment":
            return JSONResponse({"status": status, "reason": reason, "answer_ready": False,
                                 "passages": [], "case_hint": True}, headers=NO_STORE)
        answer = None
        if status == "candidates_found":
            draft_kwargs = dict(case_kwargs)
            if history:
                draft_kwargs["history"] = history
            try:
                answer = await generate_answer(question, passages, settings, **draft_kwargs)
            except DraftError as exc:
                LOG.warning("%s draft failed: %s", settings.label, exc.code)
                return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                    status_code=exc.status_code, headers=NO_STORE)
            except Exception:
                LOG.error("Unexpected %s draft failure", settings.label)
                raise HTTPException(status_code=502,
                                    detail=f"Không tạo được bản nháp từ {settings.label}. Hãy thử lại sau.") from None
        response = {"status": status, "reason": reason,
                    "answer_ready": False, "passages": passages}
        if status == "candidates_found":
            response["answer"] = answer
            response["provider"] = settings.provider
            response["model"] = settings.model
            if case:
                response["case_context_used"] = True
        return JSONResponse(response, headers=NO_STORE)

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
