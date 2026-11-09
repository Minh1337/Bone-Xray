"""Local educational chatbot with source lookup, optional image-case context,
and text-only SQLite conversation history."""

import asyncio
import csv
import hashlib
import io
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from threading import Lock
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, UnidentifiedImageError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ValidationError, model_validator
from dotenv import load_dotenv

from rag import case_context as cases
from rag import chat_history
from rag import retrieval
from rag.policy import assess
from rag.conversation import needs_context, plan_turn
from rag.generation import (DraftError, DraftSettings, RETRIEVAL_TIMEOUT_SECONDS,
                            generate_answer, generate_image_answer)


WEB = Path(__file__).resolve().parent / "demo_web"
ROOT = Path(__file__).resolve().parents[1]
LOG = logging.getLogger(__name__)
QUERY_TIMEOUT_SECONDS = 105
IMAGE_RETRIEVAL_TIMEOUT_SECONDS = 25.0
NO_STORE = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
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


class SaveTurn(BaseModel):
    question: str = Field(min_length=1, max_length=3000)
    answer: str = Field(min_length=1, max_length=12000)
    sources: list[dict] = Field(default_factory=list, max_length=10)
    conversation_id: str | None = Field(default=None, min_length=32, max_length=32)


class ImageChatHistory(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


@lru_cache(maxsize=1)
def btxrd_hash_index():
    manifest = ROOT / "data" / "external_datasets" / "BTXRD" / "reference" / "manifest.csv"
    index = {}
    if not manifest.is_file():
        return index
    with manifest.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("metadata_status") != "ok" or not row.get("sha256"):
                continue
            try:
                metadata = json.loads(row["metadata_json"])
            except (KeyError, TypeError, json.JSONDecodeError):
                continue
            index.setdefault(row["sha256"].lower(), []).append({
                "image_id": row.get("image_id"), "metadata": metadata,
                "ground_truth": row.get("ground_truth") or None,
                "relative_path": row.get("relative_path"),
            })
    return index


class RenameConversation(BaseModel):
    title: str = Field(min_length=1, max_length=100)


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

    async def retrieve_passages(question, *, top_k=5, timeout=RETRIEVAL_TIMEOUT_SECONDS):
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(retrieve_fn, question, top_k=top_k),
                timeout=timeout,
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

    @asynccontextmanager
    async def lifespan(_app):
        chat_history.init_db()
        yield

    app = FastAPI(title="BoneScope source lookup demo", version="0.2", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])
    app.mount("/assets", StaticFiles(directory=WEB), name="assets")

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB / "index.html", headers=NO_STORE)

    @app.get("/api/health")
    def health():
        # Identity/liveness only: this does not load a model or contact an AI.
        return JSONResponse({"app": "bonescope-chatbot", "status": "ok",
                             "version": "0.2", "answer_ready": False}, headers=NO_STORE)

    @app.get("/api/config")
    def config():
        # Return only public UI metadata, never the settings object or API key.
        try:
            settings = DraftSettings.from_env(require_key=False)
            data = {"provider": settings.provider, "provider_label": settings.label,
                    "model": settings.model, "configured": bool(settings.api_key),
                    "paid_fallback_model": settings.paid_fallback_model,
                    "free_fallback_after_seconds": settings.free_fallback_after_seconds}
        except DraftError:
            data = {"provider": None, "provider_label": "AI", "model": None, "configured": False}
        data["groq_fallback_enabled"] = os.getenv("GROQ_FALLBACK_ENABLED", "false").strip().lower() == "true"
        data["groq_fallback_configured"] = bool(os.getenv("GROQ_API_KEY", "").strip())
        data["case_analysis"] = True
        return JSONResponse(data, headers=NO_STORE)

    def matched_image_metadata(raw):
        """Return non-label BTXRD context only for an exact, unambiguous byte match."""
        digest = hashlib.sha256(raw).hexdigest()
        matches = btxrd_hash_index().get(digest, [])
        if len(matches) != 1:
            return None
        row = matches[0]
        metadata = row.get("metadata") or {}
        if row.get("image_id") is None:
            return None
        sites = [key for key in (
            "hand", "ulna", "radius", "humerus", "foot", "tibia", "fibula", "femur",
            "hip bone", "ankle-joint", "knee-joint", "hip-joint", "elbow-joint",
            "shoulder-joint", "upper limb", "lower limb", "pelvis",
        ) if metadata.get(key) == 1]
        views = [key for key in ("frontal", "lateral", "oblique") if metadata.get(key) == 1]
        return {"source": "BTXRD metadata; exact SHA-256 match", "image_id": row["image_id"],
                "sites": sites, "views": views}

    @app.get("/api/conversations")
    def list_chat_history(request: Request):
        check_origin(request)
        return JSONResponse({"conversations": chat_history.list_conversations()}, headers=NO_STORE)

    @app.get("/api/conversations/{conversation_id}")
    def read_chat_history(conversation_id: str, request: Request):
        check_origin(request)
        result = chat_history.get_conversation(conversation_id)
        if result is None:
            raise HTTPException(404, "Không tìm thấy cuộc trò chuyện đã lưu.")
        return JSONResponse(result, headers=NO_STORE)

    @app.post("/api/conversations/turn")
    def save_chat_turn(body: SaveTurn, request: Request):
        check_origin(request)
        question, answer = body.question.strip(), body.answer.strip()
        if not question or not answer:
            raise HTTPException(422, "Câu hỏi và câu trả lời không được để trống.")
        try:
            cid = chat_history.save_turn(body.conversation_id, question, answer, body.sources)
        except LookupError:
            raise HTTPException(409, "Cuộc trò chuyện đã bị xóa. Tạo cuộc trò chuyện mới để lưu lượt này.") from None
        except OverflowError:
            raise HTTPException(409, "Lịch sử đã đạt giới hạn lưu trữ. Hãy tạo cuộc trò chuyện mới "
                                "hoặc tự xóa những hội thoại không cần giữ.") from None
        return JSONResponse({"conversation_id": cid}, headers=NO_STORE)

    @app.patch("/api/conversations/{conversation_id}")
    def rename_chat_history(conversation_id: str, body: RenameConversation, request: Request):
        check_origin(request)
        if not chat_history.rename_conversation(conversation_id, body.title):
            raise HTTPException(404, "Không tìm thấy cuộc trò chuyện đã lưu.")
        return JSONResponse({"updated": True}, headers=NO_STORE)

    @app.delete("/api/conversations/{conversation_id}")
    def delete_chat_history(conversation_id: str, request: Request):
        check_origin(request)
        return JSONResponse({"deleted": chat_history.delete_conversation(conversation_id)}, headers=NO_STORE)

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

    @app.post("/api/case/metadata-match")
    async def match_case_metadata(request: Request, file: UploadFile = File(...)):
        check_origin(request)
        raw = await file.read(30 * 1024 * 1024 + 1)
        await file.close()
        if not raw:
            raise HTTPException(422, "Tệp ảnh trống.")
        if len(raw) > 30 * 1024 * 1024:
            raise HTTPException(413, "Ảnh vượt quá 30 MiB.")
        digest = hashlib.sha256(raw).hexdigest()
        matches = btxrd_hash_index().get(digest, [])
        # Exact duplicate files are usable only if all associated metadata agree.
        distinct = {json.dumps(item["metadata"], sort_keys=True) for item in matches}
        if not matches or len(distinct) != 1:
            reason = "ambiguous_metadata" if matches else "no_exact_match"
            return JSONResponse({"matched": False, "reason": reason}, headers=NO_STORE)
        item = matches[0]
        labels = {candidate["ground_truth"] for candidate in matches}
        return JSONResponse({"matched": True, "image_id": item["image_id"],
                             "metadata": item["metadata"],
                             "ground_truth": item["ground_truth"] if len(labels) == 1 else None,
                             "match_method": "sha256_exact", "prediction_independent": False},
                            headers=NO_STORE)

    @app.get("/api/reference-images/{image_id}")
    def reference_image(image_id: str):
        """Load one local BTXRD image by catalogue ID for the educational demo."""
        identifier = image_id.upper()
        if not re.fullmatch(r"IMG\d{6}(?:\.JPEG)?", identifier):
            raise HTTPException(404, "Không tìm thấy mã ảnh BTXRD.")
        identifier = identifier.removesuffix(".JPEG") + ".jpeg"
        for group in btxrd_hash_index().values():
            for item in group:
                if item["image_id"] != identifier:
                    continue
                if len({json.dumps(candidate["metadata"], sort_keys=True)
                        for candidate in group}) != 1:
                    raise HTTPException(409, "Ảnh trùng nội dung nhưng metadata BTXRD mâu thuẫn; "
                                        "không thể tự điền an toàn.")
                relative_path = item.get("relative_path")
                if not relative_path:
                    break
                source_root = (ROOT / "data" / "external_datasets" / "BTXRD" /
                               "reference" / "source").resolve()
                target = (source_root / relative_path).resolve()
                if not target.is_relative_to(source_root) or not target.is_file():
                    break
                return FileResponse(target, media_type="image/jpeg", headers=NO_STORE)
        raise HTTPException(404, "Ảnh không có trong bộ BTXRD cục bộ.")

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
                             "answer": answer, "provider": answer.provider, "model": answer.model},
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
                             "provider": plan["provider"], "model": plan["model"],
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
            response["provider"] = answer.provider
            response["model"] = answer.model
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

    @app.post("/api/image-chat")
    async def image_chat(request: Request, file: UploadFile = File(...),
                         question: str = Form("Hãy mô tả ảnh và những gì có thể quan sát được."),
                         history: str = Form("[]")):
        check_origin(request)
        question = question.strip()[:1000]
        if not question:
            question = "Hãy mô tả ảnh và những gì có thể quan sát được."
        try:
            parsed_history = [ImageChatHistory.model_validate(item).model_dump()
                              for item in json.loads(history)]
            if len(parsed_history) > 8 or sum(len(item["content"]) for item in parsed_history) > 9000:
                raise ValueError
        except (ValueError, TypeError, json.JSONDecodeError, ValidationError):
            raise HTTPException(422, "Lịch sử hội thoại ảnh không hợp lệ.") from None
        try:
            raw = await file.read(10 * 1024 * 1024 + 1)
        finally:
            await file.close()
        if not raw:
            raise HTTPException(422, "Tệp ảnh trống.")
        if len(raw) > 10 * 1024 * 1024:
            raise HTTPException(413, "Ảnh vượt quá 10 MiB.")
        try:
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(415, "Luồng hỏi AI hỗ trợ JPEG, PNG hoặc WEBP.")
                if image.width * image.height > 25_000_000 or getattr(image, "n_frames", 1) != 1:
                    raise HTTPException(413, "Ảnh quá lớn hoặc có nhiều khung hình.")
                image.verify()
                mime_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[image.format]
        except HTTPException:
            raise
        except (OSError, ValueError, UnidentifiedImageError):
            raise HTTPException(415, "Tệp không phải ảnh hợp lệ hoặc bị hỏng.") from None
        try:
            settings = DraftSettings.from_env()
            trusted_metadata = matched_image_metadata(raw)
            answer = None
            async with asyncio.timeout(85):
                answer, vision_model = await generate_image_answer(
                    question, raw, mime_type, settings, parsed_history,
                    trusted_metadata=trusted_metadata)
                source_query = f"{question}\n{str(answer)}"[:2000]
                source_lookup_status = "unavailable"
                source_lookup_reason = None
                passages = []
                try:
                    source_lookup_status, source_lookup_reason, passages = await retrieve_passages(
                        source_query, top_k=4, timeout=IMAGE_RETRIEVAL_TIMEOUT_SECONDS)
                    # A question about a specific uploaded image can trigger the
                    # case-level interpretation guard. Retry against the generic
                    # visual description alone to find educational reading sources.
                    if source_lookup_reason == "image_requires_specialist_assessment":
                        generic_query = re.sub(
                            r"\b(?:this|that|attached|uploaded|provided|above|here|my|our)\b",
                            " ", str(answer), flags=re.IGNORECASE)
                        source_lookup_status, source_lookup_reason, passages = await retrieve_passages(
                            generic_query[:1800], top_k=4, timeout=IMAGE_RETRIEVAL_TIMEOUT_SECONDS)
                except HTTPException as source_error:
                    source_lookup_status = "timeout" if source_error.status_code == 504 else "unavailable"
                    LOG.warning("Image analysis completed; local source lookup skipped (%s)",
                                source_lookup_status)
        except DraftError as exc:
            return JSONResponse({"detail": str(exc), "error_code": exc.code},
                                status_code=exc.status_code, headers=NO_STORE)
        except TimeoutError:
            if answer is None:
                raise HTTPException(504, "AI chưa hoàn tất phân tích ảnh trong thời gian cho phép.") from None
            source_lookup_status = "timeout"
            source_lookup_reason = "retrieval_timeout"
            passages = []
        vision_provider = getattr(answer, "provider", settings.provider)
        vision_model = getattr(answer, "model", vision_model)
        return JSONResponse({"status": "image_chat", "answer_ready": False, "answer": answer,
                             "passages": passages, "source_lookup_status": source_lookup_status,
                             "source_lookup_reason": source_lookup_reason,
                             "provider": vision_provider,
                             "model": vision_model, "image_not_stored": True,
                             "image_metadata_match": trusted_metadata}, headers=NO_STORE)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
