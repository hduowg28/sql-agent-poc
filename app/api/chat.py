from fastapi import APIRouter, status
from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_services import ChatService
router = APIRouter()


@router.post("/", response_model = ChatResponse)
def chat(request: ChatRequest):
    return ChatService.ask(request.question)