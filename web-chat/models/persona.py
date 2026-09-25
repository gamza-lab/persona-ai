import os

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app import BASE_URL, MODEL_NAME, SYSTEM_PROMPT, make_retriever, tokenize
from models.conversation import ChatRequest


class PersonaModel:
    def __init__(self):
        self.base_url = os.getenv("MODEL_BASE_URL", BASE_URL).rstrip("/")
        self.retriever = make_retriever()
        self.llm = ChatOpenAI(
            base_url=self.base_url, model=os.getenv("MODEL_NAME", MODEL_NAME),
            api_key=os.getenv("MODEL_API_KEY", "EMPTY"), max_tokens=400,
            temperature=0.2, seed=42, max_retries=0, timeout=90,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT), MessagesPlaceholder("history"),
            ("human", "{question}"),
        ])
        self.chain = prompt | self.llm | StrOutputParser()

    def inputs(self, request: ChatRequest):
        messages = request.state.messages
        previous = messages[-2].content if messages else ""
        query = f"{request.message} {request.message} {previous}"
        scores = self.retriever.vectorizer.get_scores(tokenize(query))
        evidence = [doc.metadata["evidence"] for doc in self.retriever.invoke(query)
                    if scores[doc.metadata["index"]] > 0]
        history = list(messages)
        # Bound client-supplied context while keeping complete conversation pairs.
        while history and sum(len(item.content) for item in history) > 2000:
            history = history[2:]
        return {
            "intro": request.state.intro or request.message,
            "question": request.message,
            "history": [(item.role, item.content) for item in history],
            "evidence": "\n\n".join(evidence) or "관련 역사 자료가 검색되지 않았다.",
        }

    async def respond(self, request: ChatRequest):
        return (await self.chain.ainvoke(self.inputs(request))).strip()

    async def ready(self):
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {os.getenv('MODEL_API_KEY', 'EMPTY')}"},
                )
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self):
        await self.llm.root_async_client.close()
        self.llm.root_client.close()
