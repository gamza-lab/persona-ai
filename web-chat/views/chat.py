from pathlib import Path

import gradio as gr
from fastapi import HTTPException
from pydantic import ValidationError

from app import OPENING
from models.conversation import ChatRequest, Conversation


def conversation_from_history(history):
    def content(item):
        value = item["content"]
        if isinstance(value, str):
            return value
        return "".join(block.get("text", "") for block in value if block.get("type") == "text")

    messages = []
    pending = None
    # Failed/cancelled submissions may leave an unanswered user bubble in Gradio.
    for item in history:
        if item["role"] == "user":
            pending = {"role": "user", "content": content(item)}
        elif item["role"] == "assistant" and pending is not None and content(item):
            messages.extend([pending, {"role": "assistant", "content": content(item)}])
            pending = None
    return Conversation(intro=messages[0]["content"] if messages else "",
                        messages=messages[-12:])


def build_view(controller):
    async def respond(message, history):
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
        gr.ChatInterface(
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
    return view
