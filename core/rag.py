"""RAG chain built with LCEL: history-aware retrieval + ChatGroq.

Composed from langchain-core primitives rather than the legacy
`langchain.chains` helpers, which moved to the langchain-classic
compatibility package in LangChain 1.x.
"""
from functools import lru_cache
from operator import itemgetter
from typing import Optional

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_groq import ChatGroq

from core import config
from core.vectorstore import get_retriever, similarity_search

SYSTEM_PROMPT = """You are a research assistant that answers questions about \
academic papers.

Answer using the context below. Cite the source filename inline, like \
[attention.pdf], whenever you use information from it. If the context does not \
contain the answer, say so plainly rather than guessing.

Context:
{context}"""

CONTEXTUALIZE_PROMPT = """Given the chat history and the latest user question, \
rewrite the question so it can be understood on its own without the history. \
Do not answer it, only rewrite it if needed; otherwise return it unchanged."""

_answer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

_contextualize_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", CONTEXTUALIZE_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """Return the shared ChatGroq client."""
    return ChatGroq(
        api_key=config.require_groq_key(),
        model=config.GROQ_MODEL,
        temperature=0.3,
        max_tokens=1024,
    )


# Session id -> message history. Replaces the single module-level history that
# was previously shared across every user of the API.
_histories: dict[str, InMemoryChatMessageHistory] = {}


def get_history(session_id: str) -> InMemoryChatMessageHistory:
    """Return (creating if needed) the history for one session."""
    if session_id not in _histories:
        _histories[session_id] = InMemoryChatMessageHistory()
    return _histories[session_id]


def clear_history(session_id: str) -> None:
    """Drop one session's conversation history."""
    _histories.pop(session_id, None)


def format_docs(docs: list[Document]) -> str:
    """Render retrieved documents as cited context blocks."""
    blocks = []
    for doc in docs:
        name = doc.metadata.get("filename") or doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        header = f"[{name}]" + (f" page {page}" if page is not None else "")
        blocks.append(f"{header}\n{doc.page_content}")
    return "\n\n".join(blocks) if blocks else "(no relevant passages found)"


def build_chain(top_k: int = 5, source: Optional[str] = None):
    """Build a history-aware retrieval chain, optionally scoped to one file.

    Returns a runnable taking {"input", "chat_history"} and producing
    {"answer", "context"}.
    """
    llm = get_llm()
    retriever = get_retriever(top_k=top_k, source=source)

    # Rewrite follow-ups into standalone questions, but only when there is
    # history to resolve against — otherwise skip the extra LLM round-trip.
    contextualize = _contextualize_prompt | llm | StrOutputParser()
    standalone_question = RunnableLambda(
        lambda x: x["input"] if not x.get("chat_history") else contextualize.invoke(x)
    )

    retrieve = {
        "context": standalone_question | retriever,
        "input": itemgetter("input"),
        "chat_history": lambda x: x.get("chat_history", []),
    }

    answer = (
        RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
        | _answer_prompt
        | llm
        | StrOutputParser()
    )

    return retrieve | RunnablePassthrough.assign(answer=answer)


def ask(
    question: str,
    session_id: str = "default",
    top_k: int = 5,
    source: Optional[str] = None,
    use_history: bool = True,
) -> dict:
    """Answer a question over the indexed papers."""
    history = get_history(session_id)
    chat_history = list(history.messages) if use_history else []

    chain = build_chain(top_k=top_k, source=source)
    result = chain.invoke({"input": question, "chat_history": chat_history})

    answer = result["answer"]
    if use_history:
        history.add_user_message(question)
        history.add_ai_message(answer)

    sources: list[str] = []
    for doc in result.get("context", []):
        name = doc.metadata.get("filename") or doc.metadata.get("source", "")
        if name and name not in sources:
            sources.append(name)

    return {
        "answer": answer,
        "sources": sources,
        "model": config.GROQ_MODEL,
        "context_used": bool(result.get("context")),
    }


def search(query: str, top_k: int = 5, source: Optional[str] = None) -> list[dict]:
    """Pure semantic search with no LLM involved."""
    return [
        {
            "content": doc.page_content,
            "source": doc.metadata.get("filename")
            or doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
            "similarity": round(float(score), 4),
        }
        for doc, score in similarity_search(query, top_k=top_k, source=source)
    ]
