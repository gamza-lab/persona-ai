import asyncio
import logging

from fastapi import HTTPException

from models.conversation import ChatReply, ChatRequest, Conversation, Message

logger = logging.getLogger(__name__)


class ChatController:
    def __init__(self, model):
        self.model = model
        self.lock = asyncio.Lock()

    async def chat(self, request: ChatRequest) -> ChatReply:
        try:
            await asyncio.wait_for(self.lock.acquire(), timeout=10)
        except TimeoutError:
            raise HTTPException(429, "대화 요청이 많습니다. 잠시 후 다시 시도해 주세요.")
        try:
            reply = await asyncio.wait_for(self.model.respond(request), timeout=90)
            if not reply or len(reply) > 1600:
                raise ValueError("Invalid model response")
            state = Conversation(
                intro=request.state.intro or request.message,
                messages=(request.state.messages + [
                    Message(role="user", content=request.message),
                    Message(role="assistant", content=reply),
                ])[-12:],
            )
            return ChatReply(reply=reply, state=state)
        except TimeoutError:
            raise HTTPException(504, "응답 시간이 길어지고 있습니다. 다시 시도해 주세요.")
        except Exception:
            logger.exception("Model request failed")
            raise HTTPException(503, "모델에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        finally:
            self.lock.release()
