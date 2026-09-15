"""LangChain PGVector store and cached embedding model.

The embedding model is loaded once per process via lru_cache. The previous
implementation reloaded all-mpnet-base-v2 from disk on every single search,
which cost seconds of latency per request.
"""
from functools import lru_cache
from typing import Any, Optional

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

from core import config


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Load the sentence-transformer embedding model once per process."""
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vectorstore() -> PGVector:
    """Return the shared PGVector store, creating tables if needed."""
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=config.COLLECTION_NAME,
        connection=config.CONNECTION_STRING,
        use_jsonb=True,
    )


def _source_filter(source: Optional[str]) -> Optional[dict[str, Any]]:
    """Build a metadata filter restricting results to one source file."""
    if not source:
        return None
    return {"filename": {"$eq": source}}


def similarity_search(
    query: str, top_k: int = 5, source: Optional[str] = None
) -> list[tuple[Document, float]]:
    """Search the store, optionally scoped to a single source file.

    The filter is pushed into the query so scoping to one paper returns the
    top_k chunks *from that paper*, rather than filtering a global top_k
    down to whatever happens to remain.
    """
    store = get_vectorstore()
    return store.similarity_search_with_relevance_scores(
        query, k=top_k, filter=_source_filter(source)
    )


def get_retriever(top_k: int = 5, source: Optional[str] = None):
    """Return a LangChain retriever, optionally scoped to one source file."""
    search_kwargs: dict[str, Any] = {"k": top_k}
    filt = _source_filter(source)
    if filt:
        search_kwargs["filter"] = filt
    return get_vectorstore().as_retriever(search_kwargs=search_kwargs)


def add_documents(documents: list[Document]) -> int:
    """Embed and store documents in a single batched call."""
    if not documents:
        return 0
    get_vectorstore().add_documents(documents)
    return len(documents)


@lru_cache(maxsize=1)
def _engine():
    """Shared SQLAlchemy engine for the metadata queries below."""
    import sqlalchemy

    return sqlalchemy.create_engine(config.CONNECTION_STRING)


def list_sources() -> list[str]:
    """Return the distinct source filenames currently indexed."""
    import sqlalchemy

    stmt = sqlalchemy.text(
        """
        SELECT DISTINCT e.cmetadata ->> 'filename' AS filename
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = :collection
          AND e.cmetadata ->> 'filename' IS NOT NULL
        ORDER BY filename
        """
    )
    try:
        with _engine().connect() as conn:
            return [row[0] for row in conn.execute(
                stmt, {"collection": config.COLLECTION_NAME}
            )]
    except Exception:
        # Collection not created yet.
        return []


def delete_source(filename: str) -> int:
    """Remove every chunk belonging to one source file.

    PGVector.delete() only accepts explicit ids and silently ignores a
    metadata filter, so the delete is issued as SQL scoped to this
    collection. Returns the number of chunks removed.
    """
    import sqlalchemy

    stmt = sqlalchemy.text(
        """
        DELETE FROM langchain_pg_embedding e
        USING langchain_pg_collection c
        WHERE e.collection_id = c.uuid
          AND c.name = :collection
          AND e.cmetadata ->> 'filename' = :filename
        """
    )
    try:
        with _engine().begin() as conn:
            return conn.execute(
                stmt,
                {"collection": config.COLLECTION_NAME, "filename": filename},
            ).rowcount
    except Exception:
        # Collection not created yet; nothing to delete.
        return 0
