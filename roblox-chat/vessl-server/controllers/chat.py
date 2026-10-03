import asyncio
import logging

from fastapi import HTTPException

from models.conversation import ChatReply, ChatRequest, Conversation, Message

logger = logging.getLogger(__name__)


class ChatController:
    """화면과 API의 공통 대화 처리기. 요청 순서, 시간 제한, 응답 상태를 관리한다."""

    def __init__(self, model):
        self.model = model
        self.lock = asyncio.Lock()

    async def chat(self, request: ChatRequest) -> ChatReply:
        """한 번의 질문을 처리하고 다음 요청에서 재사용할 대화 상태를 돌려준다.

        기록은 서버 DB에 저장하지 않는다. 클라이언트가 반환받은 state를
        다음 질문과 함께 보내면 그 기록을 이어서 사용한다.
        """
        # 단일 모델의 동시 추론을 제한하되 대기 시간과 추론 시간은 별도로 제한한다.
        try:
            await asyncio.wait_for(self.lock.acquire(), timeout=10)
        except TimeoutError:
            raise HTTPException(429, "대화 요청이 많습니다. 잠시 후 다시 시도해 주세요.")
        try:
            reply = await asyncio.wait_for(self.model.respond(request), timeout=90)
            if not reply or len(reply) > 1600:
                raise ValueError("Invalid model response")
            state = Conversation(
                # 첫 자기소개는 보존하고 최근 여섯 번의 완결된 대화만 반환한다.
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
            # 상세 원인은 서버 로그에만 남기고 사용자에게는 안내 메시지를 보낸다.
            logger.exception("Model request failed")
            raise HTTPException(503, "모델에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        finally:
            # 추론 실패나 요청 취소가 발생해도 다음 요청이 진행되도록 잠금을 푼다.
            self.lock.release()
