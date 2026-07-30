"""
app/api/chat.py
~~~~~~~~~~~~~~~
Chat API Router.

Thay đổi so với phiên bản cũ:
  - Thêm `Depends(get_db)` để inject Session vào endpoint
  - Truyền `db` xuống ChatService.ask() (DI pattern)
  - Khai báo đầy đủ response_model, status_code, tags cho OpenAPI docs
  - Exception được handle bởi Global Handler (không try/except ở đây)
"""

from fastapi import APIRouter, status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_services import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Hỏi đáp với SQL Agent",
    description=(
        "Gửi câu hỏi bằng ngôn ngữ tự nhiên. "
        "Agent sẽ tự động sinh SQL, truy vấn database và trả lời."
    ),
)
def ask_question(request: ChatRequest) -> ChatResponse:
    """
    Endpoint nhận câu hỏi từ người dùng và trả lời qua SQL Agent.

    - **question**: Câu hỏi bằng tiếng Việt hoặc tiếng Anh
    - **include_sql**: Có trả về câu SQL đã sinh không (mặc định True)
    """
    return ChatService.ask(request=request)
