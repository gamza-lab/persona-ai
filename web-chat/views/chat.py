from pathlib import Path

import gradio as gr
from fastapi import HTTPException
from pydantic import ValidationError

from app import OPENING
from models.conversation import ChatRequest, Conversation


def conversation_from_history(history):
    """Gradio 화면 기록을 컨트롤러가 받는 Conversation으로 변환한다.

    답변 없이 남은 질문은 제외하고 완성된 질문·답변만 최대 6쌍 남긴다.
    첫 질문은 자기소개로 따로 보존하여 오래된 기록을 줄여도 유지한다.
    """
    def content(item):
        """문자열 또는 콘텐츠 블록 목록으로 오는 Gradio 본문에서 텍스트를 꺼낸다."""
        value = item["content"]
        if isinstance(value, str):
            return value
        return "".join(block.get("text", "") for block in value if block.get("type") == "text")

    messages = []
    pending = None
    # 실패하거나 취소한 요청은 사용자 말풍선만 남을 수 있어 답변과 짝지어 수집한다.
    for item in history:
        if item["role"] == "user":
            pending = {"role": "user", "content": content(item)}
        elif item["role"] == "assistant" and pending is not None and content(item):
            messages.extend([pending, {"role": "assistant", "content": content(item)}])
            pending = None
    return Conversation(intro=messages[0]["content"] if messages else "",
                        messages=messages[-12:])


def build_view(controller):
    """브라우저에서 사용할 단독 채팅 화면을 만든다."""

    async def respond(message, history):
        """화면 입력을 공통 컨트롤러에 전달하고 오류를 Gradio 알림으로 표시한다."""
        try:
            state = conversation_from_history(history)
            result = await controller.chat(ChatRequest(message=message, state=state))
            return result.reply
        except ValidationError:
            raise gr.Error("메시지는 1~500자로 입력해 주세요.")
        except HTTPException as error:
            raise gr.Error(error.detail)

    with gr.Blocks(title="세종과의 만남", analytics_enabled=False, fill_height=True, fill_width=True) as view:
        gr.HTML('<header class="persona-header"><div class="seal">世宗</div>'
                '<div><p>1449 · 조선</p><h1>세종과의 만남</h1></div>'
                '<span class="fiction">AI 역사 인물 · 창작 대화</span></header>')
        build_chat(respond)
    return view


def build_chat(respond):
    """입력창과 대화 목록을 구성한다. 전송·재시도·취소 동작은 Gradio가 담당한다."""
    return gr.ChatInterface(
            fn=respond,
            chatbot=gr.Chatbot(label="세종", placeholder=OPENING, height="65vh",
                               buttons=["copy"], allow_tags=False,
                               avatar_images=(None, str(Path(__file__).with_name("sejong.webp")))),
            textbox=gr.Textbox(placeholder="전하께 말을 건네 보세요", max_lines=5,
                               label="메시지", show_label=False,
                               max_length=500, submit_btn=True, stop_btn=True),
            flagging_mode="never", save_history=False, api_visibility="private",
            concurrency_limit=4, stop_btn=True, fill_width=True,
        )
