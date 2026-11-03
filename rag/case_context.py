"""Educational image-case context for the chatbot demo.

The classifier output is server-owned: the browser receives an opaque case ID
and never supplies scores. Only the Top-3 labels/scores and the label-mapping
note are sent to the LLM provider. The image, metadata (age, sex, site, view)
and hashes stay on this machine. Scores are uncalibrated softmax outputs, not
disease probabilities or a diagnosis.
"""

import json
import secrets
from threading import Lock
from time import monotonic

from rag.generation import INSTRUCTIONS, request_response, response_text


CASE_TTL_SECONDS = 1800
MAX_CASES = 50
SITE_FIELDS = ("hand", "ulna", "radius", "humerus", "foot", "tibia", "fibula", "femur",
               "hip bone", "ankle-joint", "knee-joint", "hip-joint", "elbow-joint",
               "shoulder-joint", "upper limb", "lower limb", "pelvis")
VIEW_FIELDS = ("frontal", "lateral", "oblique")
NOTICE = ("Kết quả phân loại tự động cho mục đích học tập. Điểm là đầu ra softmax chưa hiệu chỉnh, "
          "không phải xác suất mắc bệnh và không phải chẩn đoán.")

# Mapping status:
#   direct      - the checkpoint label text equals a term the corpus covers; an
#                 automatic lookup is allowed for the general concept only.
#   unresolved  - a related concept exists, but equivalence with the dataset
#                 class definition has not been verified; no automatic lookup.
#   aggregate   - a grouped class with no single concept; no lookup.
#   no_tumor    - no tumour concept to look up.
# Statuses mirror rag/retrieval_config.json unsupported_terms; they are an
# agent-authored working table, not a reviewed clinical terminology mapping.
LABEL_GUIDE = {
    "no-tumor": {"display": "Không có u (nhãn dữ liệu)", "status": "no_tumor",
                 "note": "Nhãn 'no-tumor' của bộ dữ liệu không ứng với một khái niệm bệnh để tra cứu."},
    "osteochondroma": {"display": "Osteochondroma (u xương sụn)", "status": "direct",
                       "query": "Osteochondroma là gì, thường gặp ở đâu và có đặc điểm hình ảnh nào?",
                       "note": "Tên nhãn trùng thuật ngữ có trong kho tài liệu; nguồn chỉ mô tả khái niệm chung."},
    "multiple osteochondromas": {"display": "Multiple osteochondromas (nhãn dữ liệu)", "status": "unresolved",
                                 "related": "osteochondroma",
                                 "note": "Kho tài liệu chưa có nguồn riêng; chưa kiểm tra định nghĩa nhãn của bộ dữ liệu."},
    "simple bone cyst": {"display": "Simple bone cyst (nang xương đơn độc)", "status": "direct",
                         "query": "Simple bone cyst (unicameral bone cyst) là gì và có đặc điểm hình ảnh nào?",
                         "note": "Tên nhãn trùng thuật ngữ có trong kho tài liệu; nguồn chỉ mô tả khái niệm chung."},
    "giant cell tumor": {"display": "Giant cell tumor (u tế bào khổng lồ)", "status": "direct",
                         "query": "Giant cell tumor of bone là gì và có đặc điểm hình ảnh nào?",
                         "note": "Tên nhãn trùng thuật ngữ có trong kho tài liệu; nguồn chỉ mô tả khái niệm chung."},
    "osteofibroma": {"display": "Osteofibroma (nhãn dữ liệu)", "status": "unresolved",
                     "related": "osteofibrous dysplasia",
                     "note": "Chưa xác minh nhãn này tương đương osteofibrous dysplasia hay khái niệm khác."},
    "synovial osteochondroma": {"display": "Synovial osteochondroma (nhãn dữ liệu)", "status": "unresolved",
                                "related": "synovial chondromatosis",
                                "note": "Chưa xác minh nhãn này tương đương synovial chondromatosis."},
    "other bt": {"display": "Other benign tumor (nhóm u lành gộp)", "status": "aggregate",
                 "note": "Nhóm gộp nhiều loại u lành; không có một khái niệm duy nhất để tra cứu."},
    "osteosarcoma": {"display": "Osteosarcoma (sarcoma xương)", "status": "direct",
                     "query": "Osteosarcoma là gì, thường gặp ở đâu và có đặc điểm hình ảnh nào?",
                     "note": "Tên nhãn trùng thuật ngữ có trong kho tài liệu; nguồn chỉ mô tả khái niệm chung."},
    "other mt": {"display": "Other malignant tumor (nhóm u ác gộp)", "status": "aggregate",
                 "note": "Nhóm gộp nhiều loại u ác; không có một khái niệm duy nhất để tra cứu."},
}


def check_demo_metadata(meta):
    """Extra demo rule observed in all 3,746 BTXRD rows: >=1 site, exactly one view.

    This rejects an untouched all-zero form instead of silently guessing.
    """
    if not any(meta.get(key) == 1 for key in SITE_FIELDS):
        raise ValueError("Chọn ít nhất một vị trí xương/khớp/chi của ảnh; không để trống.")
    if sum(meta.get(key) == 1 for key in VIEW_FIELDS) != 1:
        raise ValueError("Chọn đúng một tư thế chụp: frontal, lateral hoặc oblique.")


class CaseStore:
    """Short-lived in-memory cases. Nothing is written to disk."""

    def __init__(self, ttl=CASE_TTL_SECONDS, limit=MAX_CASES, clock=monotonic):
        self.ttl, self.limit, self.clock = ttl, limit, clock
        self.items = {}
        self.lock = Lock()

    def _prune(self, now):
        self.items = {k: v for k, v in self.items.items() if now - v["created"] < self.ttl}

    def add(self, record):
        case_id = secrets.token_urlsafe(24)
        with self.lock:
            now = self.clock()
            self._prune(now)
            while len(self.items) >= self.limit:
                del self.items[min(self.items, key=lambda k: self.items[k]["created"])]
            self.items[case_id] = {**record, "created": now}
        return case_id

    def get(self, case_id):
        with self.lock:
            self._prune(self.clock())
            return self.items.get(case_id)

    def remove(self, case_id):
        with self.lock:
            return self.items.pop(case_id, None) is not None


def build_record(ranked, seconds, model_info):
    if len(ranked) != len(LABEL_GUIDE) or {label for label, _ in ranked} != set(LABEL_GUIDE):
        raise ValueError("Unexpected classifier labels")
    return {"ranked": [(label, float(score)) for label, score in ranked],
            "prediction_seconds": float(seconds),
            "model_sha256": model_info.get("sha256", {}).get("best_model.pt"),
            "device": model_info.get("device")}


def summary(case_id, record):
    top1 = record["ranked"][0][0]
    guide = LABEL_GUIDE[top1]
    mapping = {"status": guide["status"], "note": guide["note"]}
    if guide.get("related"):
        mapping["related_concept_unverified"] = guide["related"]
    return {"case_id": case_id, "top1": top1, "top1_display": guide["display"],
            "top3": [{"label": label, "display": LABEL_GUIDE[label]["display"], "score": score}
                     for label, score in record["ranked"][:3]],
            "scores": dict(record["ranked"]), "prediction_seconds": record["prediction_seconds"],
            "model_sha256": record["model_sha256"], "device": record["device"],
            "mapping": mapping, "notice": NOTICE, "expires_in_seconds": CASE_TTL_SECONDS,
            "answer_ready": False}


def llm_context(record):
    """Minimal data shared with the external LLM provider."""
    top1 = record["ranked"][0][0]
    guide = LABEL_GUIDE[top1]
    return {"kind": "educational_classifier_output",
            "model_output_top3": [{"label": label, "softmax_score": round(score, 3)}
                                  for label, score in record["ranked"][:3]],
            "top1_label_mapping": {"status": guide["status"], "note": guide["note"]},
            "limits": ["Assistant cannot see the image.",
                       "Scores are uncalibrated softmax outputs, not disease probabilities.",
                       "Output is not a diagnosis and has no independent external validation."]}


def lookup_query(record):
    guide = LABEL_GUIDE[record["ranked"][0][0]]
    return guide.get("query") if guide["status"] == "direct" else None


def template_explanation(record, sources_found=False):
    """Deterministic explanation: no LLM call, used when lookup is not allowed or
    when the provider is unavailable (then the retrieved passages are shown as-is)."""
    top = record["ranked"]
    guide = LABEL_GUIDE[top[0][0]]
    lines = ["### Kết quả mô hình",
             *[f"- **{LABEL_GUIDE[label]['display']}**: điểm {score:.3f}" for label, score in top[:3]],
             "", NOTICE, "", "### Tra cứu tài liệu"]
    if sources_found:
        lines.append("Các đoạn nguồn bên dưới mô tả khái niệm chung của nhãn Top-1, không chứng minh ảnh có "
                     "tổn thương đó. Chưa có bản nháp AI; hãy tự đọc và đối chiếu từng đoạn.")
    else:
        lines.append(f"{guide['note']} Vì vậy mình không tự động tìm nguồn cho nhãn này.")
    if guide.get("related") and not sources_found:
        lines.append(f"Nếu muốn học về khái niệm có thể liên quan, bạn có thể hỏi riêng về "
                     f"`{guide['related']}` — đây là gợi ý học tập, không phải ánh xạ nhãn đã kiểm chứng.")
    lines += ["", "### Giới hạn",
              "- Mình không nhìn thấy ảnh; chỉ biết đầu ra của mô hình phân loại.",
              "- Mô hình có thể sai và chưa được kiểm định độc lập trên dữ liệu ngoài."]
    return "\n".join(lines)


CASE_ADDENDUM = """
Có trường case_context: đó là đầu ra của mô hình phân loại ảnh tự động cho một ảnh học tập mà bạn KHÔNG nhìn thấy.
Có thể nhắc lại và giải thích ý nghĩa đầu ra mô hình, nhưng không mô tả ảnh, không khẳng định ảnh có tổn thương,
không coi điểm là xác suất mắc bệnh hay chẩn đoán, không gắn [S#] cho case_context."""

CASE_EXPLAIN_INSTRUCTIONS = INSTRUCTIONS + CASE_ADDENDUM + """
Nhiệm vụ: viết 3 phần ngắn có tiêu đề Markdown:
### Kết quả mô hình — nêu Top-3 nhãn và điểm; nhắc điểm softmax chưa hiệu chỉnh, không phải chẩn đoán.
### Tài liệu nói gì về khái niệm — chỉ dùng passages, gắn [S1], [S2]; nói rõ đây là kiến thức chung về khái niệm,
không chứng minh ảnh này có tổn thương đó.
### Giới hạn — mô hình có thể sai, bạn không nhìn thấy ảnh, không dùng cho chẩn đoán hay điều trị."""


async def explain_case(record, passages, settings):
    payload = {"case_context": llm_context(record),
               "passages": [{"citation": f"S{i}", "title": p["title"], "section": p["section"], "text": p["text"]}
                            for i, p in enumerate(passages, 1)]}
    response = await request_response(settings, instructions=CASE_EXPLAIN_INSTRUCTIONS,
                                      input=json.dumps(payload, ensure_ascii=False))
    return response_text(response, settings)
