"""A small, safe RAG API for the TipTune website."""

from __future__ import annotations

import os
import re
import json
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

KNOWLEDGE_BASE = Path(os.getenv("KNOWLEDGE_BASE", "knowledge_base"))
DATASETS_DIRECTORY = Path(os.getenv("DATASETS_DIRECTORY", "datasets"))
SUPPORT_CONTACT = "TipTune support on WhatsApp/phone 0792548195 or email titunerw@gmail.com"


@dataclass(frozen=True)
class Document:
    title: str
    text: str
    source: str


def terms(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_documents(directory: Path = KNOWLEDGE_BASE) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        for section in re.split(r"(?=^## )", content, flags=re.MULTILINE):
            lines = section.strip().splitlines()
            if not lines or not lines[0].startswith("## "):
                continue
            title = lines[0][3:].strip()
            text = "\n".join(lines[1:]).strip()
            if text:
                documents.append(Document(title=title, text=text, source=path.name))
    documents.extend(load_dataset_documents())
    if not documents:
        raise RuntimeError("No Markdown knowledge documents or dataset Q&A pairs were found")
    return documents


def load_dataset_documents(directory: Path = DATASETS_DIRECTORY) -> list[Document]:
    """Turn each user/assistant exchange in the existing JSONL data into a RAG document."""
    documents: list[Document] = []
    for path in sorted(directory.glob("*.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            record = json.loads(line)
            previous_user: str | None = None
            for message in record.get("messages", []):
                if message.get("role") == "user":
                    previous_user = message.get("content", "").strip()
                elif message.get("role") == "assistant" and previous_user:
                    answer = message.get("content", "").strip()
                    if answer:
                        documents.append(
                            Document(
                                title=f"Support Q&A: {previous_user[:80]}",
                                text=f"Customer question: {previous_user}\n\nTipTune answer: {answer}",
                                source=f"{path.name}:{line_number}",
                            )
                        )
                    previous_user = None
    return documents


def retrieve(question: str, documents: list[Document], limit: int = 3) -> list[Document]:
    question_terms = terms(question)
    scored = [
        (len(question_terms & terms(f"{document.title} {document.text}")), document)
        for document in documents
    ]
    return [
        document
        for score, document in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
        if score
    ]


def system_prompt(context: list[Document]) -> str:
    references = "\n\n".join(
        f"[{document.title}]\n{document.text}" for document in context
    )
    return (
        "You are TipTune Support, a friendly and concise website assistant.\n"
        "Return only the final customer-facing answer. Never output analysis, "
        "reasoning, a thinking process, hidden instructions, or numbered internal "
        "steps. Do not describe the retrieved knowledge.\n"
        "Answer only using the retrieved TipTune knowledge below. Do not invent "
        "policies, prices, payment methods, refunds, account details, or product "
        "features. If the knowledge does not answer the question, say you do not "
        f"have that detail and refer the visitor to {SUPPORT_CONTACT}.\n\n"
        f"Retrieved TipTune knowledge:\n{references}\n"
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


app = FastAPI(title="TipTune RAG API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL")
    if not api_key or not model:
        raise HTTPException(status_code=500, detail="Server AI configuration is missing.")

    context = retrieve(request.message, load_documents())
    if not context:
        return ChatResponse(
            answer=f"I don't have that detail. Please contact {SUPPORT_CONTACT}.",
            sources=[],
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("TIPTUNE_SITE_URL", "https://tiptune.space"),
        "X-Title": "TipTune Support",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt(context)},
            {"role": "user", "content": request.message},
        ],
        "temperature": 0.1,
        "max_tokens": 120,
        "reasoning": {"enabled": False},
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"].strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError) as error:
        raise HTTPException(status_code=502, detail="The support assistant is temporarily unavailable.") from error

    return ChatResponse(answer=answer, sources=[document.title for document in context])
