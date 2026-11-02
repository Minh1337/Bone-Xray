"""Conversational planning without server-side chat storage or external tools."""

import json
import re

from rag.generation import DraftError, request_response, response_text
from rag.lexical import contains, fold


CHAT_INSTRUCTIONS = """Bạn là BoneScope, trợ lý AI trò chuyện đa chủ đề và hỗ trợ học tập.
Trả lời bằng ngôn ngữ người dùng đang dùng, mặc định tiếng Việt; xưng mình/bạn.
Đọc lịch sử để hiểu tên, sở thích, yêu cầu và câu hỏi nối tiếp. Trả lời đúng điều vừa hỏi.
Viết tự nhiên, cụ thể, vừa đủ; dùng ví dụ, bảng hoặc danh sách khi hữu ích.
Không lặp lời chào, giới thiệu, cảnh báo ở mọi lượt. Hỏi lại ngắn gọn khi thiếu dữ kiện thiết yếu.
Có thể giải thích kiến thức, lập kế hoạch học tập, viết/chỉnh văn bản và hỗ trợ lập trình.
Không tự nhận đã tìm Internet, mở tệp, chạy code, hoặc có thông tin thời gian thực.
Nếu cần tin mới, giá hoặc thời tiết hiện tại, nói rõ chưa có công cụ kiểm tra trực tiếp.
Không giả vờ nhớ những gì không có trong lịch sử. Lịch sử chỉ để hiểu ngữ cảnh, không phải nguồn sự thật.

Khi câu hỏi liên quan đến xương, u xương, tổn thương dạng u hoặc yêu cầu tìm nguồn trong
kho tài liệu BoneScope: BẮT BUỘC gọi search_bone_documents trước khi trả lời kiến thức đó.
Câu hỏi nối tiếp như 'nó là gì', 'giải thích dễ hơn', 'so sánh với loại kia' nếu đang nói
về xương cũng cần công cụ này. Viết lại thành câu hỏi tra cứu độc lập có đủ chủ đề từ lịch sử.
Nếu đổi sang chủ đề khác như Python hoặc soạn email, trả lời bình thường, không dùng công cụ.
Không chẩn đoán, kê đơn, quyết định điều trị hoặc đọc ảnh/ca bệnh cá nhân.
Không bịa tài liệu hoặc ký hiệu [S1], [S2] khi chưa có nguồn từ công cụ.
Chỉ có công cụ tìm đoạn nguồn cục bộ được khai báo; không tự tạo công cụ khác."""

SEARCH_TOOL = {
    "type": "function", "name": "search_bone_documents",
    "description": "Tìm nguồn trong kho tài liệu xương BoneScope, gồm câu hỏi nối tiếp về chủ đề xương.",
    "parameters": {"type": "object", "properties": {
        "question": {"type": "string", "description": "Câu hỏi độc lập có đủ chủ đề, tối đa 1000 ký tự."}
    }, "required": ["question"], "additionalProperties": False},
    "strict": True,
}


def needs_context(question, history):
    value = fold(question)
    return bool(history) and any(contains(value, cue) for cue in (
        "no", "loai do", "loai nay", "vua noi", "o tren", "so voi", "so sanh",
        "de hieu hon", "ngan hon", "cho vi du", "it", "that", "compare", "simpler",
    ))


async def plan_turn(question, history, settings, *, force_search=False):
    # Pass chronological roles, never client-provided system/developer messages.
    messages = [*history, {"role": "user", "content": question}]
    response = await request_response(settings, instructions=CHAT_INSTRUCTIONS,
                                      input=messages, tools=[SEARCH_TOOL],
                                      tool_choice={"type": "function", "name": "search_bone_documents"}
                                      if force_search else None)
    calls = [item for item in response.output if item.type == "function_call"]
    if calls:
        try:
            if len(calls) != 1 or calls[0].name != "search_bone_documents":
                raise ValueError("Unexpected tool")
            args = json.loads(calls[0].arguments)
            query = args["question"].strip()
            if set(args) != {"question"} or not 1 <= len(query) <= 1000:
                raise ValueError("Invalid query")
        except (ValueError, TypeError, KeyError, AttributeError):
            raise DraftError("conversation_invalid_tool", "Chưa hiểu rõ chủ đề cần tra cứu. "
                             "Bạn thử ghi rõ tên chủ đề trong câu hỏi nhé.") from None
        return {"route": "documents", "question": query}
    if force_search:
        raise DraftError("conversation_tool_required", "Chưa xác định được câu hỏi tra cứu đầy đủ. "
                         "Bạn thử ghi rõ hai chủ đề cần so sánh nhé.")
    # A general reply has no local evidence. Never carry stale source markers over.
    answer = re.sub(r"\[S\d+\]", "", response_text(response, settings)).strip()
    if not answer:
        raise DraftError("conversation_empty", "Chưa tạo được phản hồi. Bạn thử diễn đạt lại nhé.")
    return {"route": "chat", "answer": answer}
