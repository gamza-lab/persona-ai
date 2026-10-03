from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Message(BaseModel):
    """대화 한 줄의 역할과 본문. 임의의 추가 필드나 system 역할은 받지 않는다."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1600)


class Conversation(BaseModel):
    """첫 자기소개와 최근 대화 최대 6쌍을 담는 클라이언트 전달용 상태."""

    model_config = ConfigDict(extra="forbid")
    intro: str = Field(default="", max_length=500)
    messages: list[Message] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_history(self):
        """사용자→답변 순서, 자기소개 유무, 사용자 메시지 길이를 확인한다."""
        # 클라이언트가 보낸 기록도 검증하여 쌍 단위 자르기와 직전 질문 접근을 보장한다.
        if len(self.messages) % 2 or any(
            item.role != ("user" if index % 2 == 0 else "assistant")
            for index, item in enumerate(self.messages)
        ):
            raise ValueError("History must contain complete user/assistant pairs")
        if self.messages and not self.intro.strip():
            raise ValueError("History requires an introduction")
        if any(len(item.content) > 500 for item in self.messages if item.role == "user"):
            raise ValueError("User messages must not exceed 500 characters")
        return self


class ChatRequest(BaseModel):
    """새 질문과 이전 상태. state를 생략하면 새 대화를 시작한다."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    state: Conversation = Field(default_factory=Conversation)


class ChatReply(BaseModel):
    """화면에 표시할 답변과 다음 요청에 넘겨줄 대화 상태."""

    reply: str
    state: Conversation
