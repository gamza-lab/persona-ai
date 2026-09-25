from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Message(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1600)


class Conversation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intro: str = Field(default="", max_length=500)
    messages: list[Message] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def validate_history(self):
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
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    message: str = Field(min_length=1, max_length=500)
    state: Conversation = Field(default_factory=Conversation)


class ChatReply(BaseModel):
    reply: str
    state: Conversation
