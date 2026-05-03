from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from datetime import datetime, timezone
from hashlib import sha256

from bson import ObjectId
from django.conf import settings

from api.db import get_db

LOCAL_MODEL_NAME = "local-hash-256"
LOCAL_EMBEDDING_DIMENSION = 256


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def local_hash_embedding(text: str) -> list[float]:
    vector = [0.0] * LOCAL_EMBEDDING_DIMENSION
    tokens = [token for token in text.lower().split() if token]
    if not tokens:
        return vector

    for token in tokens:
        digest = sha256(token.encode("utf-8")).digest()
        for index in range(0, len(digest), 2):
            bucket = digest[index] % LOCAL_EMBEDDING_DIMENSION
            direction = 1.0 if digest[index + 1] % 2 == 0 else -1.0
            vector[bucket] += direction
    return vector


def _request_openrouter_embeddings(texts: list[str]) -> tuple[str, list[list[float]]]:
    payload = {
        "model": settings.OPENROUTER_EMBEDDING_MODEL,
        "input": texts,
        "encoding_format": "float",
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "ProjectNest",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        content = json.loads(response.read().decode("utf-8"))

    model_name = content.get("model") or settings.OPENROUTER_EMBEDDING_MODEL
    vectors = [item["embedding"] for item in content.get("data", [])]
    return model_name, vectors


def generate_embedding_sets(texts: list[str]) -> dict[str, list[list[float]]]:
    result: dict[str, list[list[float]]] = {
        LOCAL_MODEL_NAME: [local_hash_embedding(text) for text in texts],
    }
    if not settings.OPENROUTER_API_KEY or not texts:
        return result

    try:
        model_name, vectors = _request_openrouter_embeddings(texts)
        if len(vectors) == len(texts):
            result[model_name] = vectors
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        pass
    return result


def generate_query_embeddings(text: str) -> dict[str, list[float]]:
    return {model_name: vectors[0] for model_name, vectors in generate_embedding_sets([text]).items()}


def _request_openrouter_chat_completion(messages: list[dict[str, str]]) -> str | None:
    payload = {
        "model": settings.OPENROUTER_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "ProjectNest",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=90) as response:
        content = json.loads(response.read().decode("utf-8"))

    choices = content.get("choices") or []
    if not choices:
        return None

    message = choices[0].get("message") or {}
    content_text = message.get("content")
    if isinstance(content_text, str):
        return content_text.strip() or None
    return None


def generate_grounded_answer(question: str, matches: list[dict]) -> str | None:
    if not matches:
        return "I could not find enough matching content inside this project to answer that question."
    if not settings.OPENROUTER_API_KEY:
        return "The assistant is not configured with an OpenRouter API key, so only retrieval results are available."

    context_blocks = []
    for index, match in enumerate(matches, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"Source {index}",
                    f"Document: {match['document_title']}",
                    f"Chunk index: {match['chunk_index']}",
                    f"Snippet: {match['snippet']}",
                ]
            )
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You are ProjectNest's project-scoped assistant. "
                "Answer only from the supplied project context. "
                "Do not use outside knowledge. "
                "If the context is insufficient, say that clearly. "
                "Format the answer in Markdown. "
                "Keep the answer concise and mention the source document titles you relied on."
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Question:",
                    question,
                    "",
                    "Project-scoped context:",
                    "\n\n".join(context_blocks),
                ]
            ),
        },
    ]

    try:
        answer = _request_openrouter_chat_completion(messages)
        return answer or "The model did not return a usable answer. Review the retrieved project snippets below and retry."
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            return (
                "The selected LLM is rate-limited right now (HTTP 429). "
                "Your project-only snippets were retrieved correctly below, so retry in a moment."
            )
        return (
            f"The selected LLM returned HTTP {exc.code}. "
            "The retrieved project-only snippets are still shown below."
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "The LLM is temporarily unavailable. The retrieved project-only snippets are shown below."


def rank_project_matches(project_id: ObjectId, query: str, top_k: int) -> list[dict]:
    database = get_db()
    query_embeddings = generate_query_embeddings(query)
    if not query_embeddings:
        return []

    rows = list(
        database.chunk_embeddings.find(
            {"project_id": project_id, "model_name": {"$in": list(query_embeddings.keys())}}
        )
    )
    if not rows:
        return []

    best_by_chunk: dict[ObjectId, dict] = {}
    for row in rows:
        score = cosine_similarity(query_embeddings[row["model_name"]], row["vector"])
        previous = best_by_chunk.get(row["chunk_id"])
        if previous is None or score > previous["score"]:
            best_by_chunk[row["chunk_id"]] = {
                "chunk_id": row["chunk_id"],
                "score": score,
                "model_name": row["model_name"],
            }

    ranked = sorted(best_by_chunk.values(), key=lambda item: item["score"], reverse=True)[:top_k]
    if not ranked:
        return []

    chunk_ids = [item["chunk_id"] for item in ranked]
    chunks = {
        row["_id"]: row
        for row in database.document_chunks.find({"_id": {"$in": chunk_ids}, "project_id": project_id})
    }
    document_ids = {row["document_id"] for row in chunks.values()}
    documents = {
        row["_id"]: row
        for row in database.documents.find({"_id": {"$in": list(document_ids)}, "project_id": project_id})
    }

    matches: list[dict] = []
    for item in ranked:
        chunk = chunks.get(item["chunk_id"])
        if not chunk:
            continue
        document = documents.get(chunk["document_id"])
        if not document:
            continue
        matches.append(
            {
                "chunk_id": str(chunk["_id"]),
                "document_id": str(document["_id"]),
                "document_title": document["title"],
                "snippet": chunk["content"],
                "score": round(item["score"], 5),
                "chunk_index": chunk["chunk_index"],
                "model_name": item["model_name"],
            }
        )
    return matches


def rebuild_document_embeddings(document: dict) -> None:
    database = get_db()
    from api.documents import chunk_text, extract_text_from_file
    from api.storage import read_stored_file

    filename, content = read_stored_file(document["file_path"])
    extracted_text = extract_text_from_file(filename, content)
    chunks = chunk_text(extracted_text)
    if not chunks and extracted_text:
        chunks = [extracted_text]

    database.document_chunks.delete_many({"document_id": document["_id"]})
    database.chunk_embeddings.delete_many({"project_id": document["project_id"], "document_id": document["_id"]})

    now = datetime.now(timezone.utc)
    chunk_docs = [
        {
            "document_id": document["_id"],
            "project_id": document["project_id"],
            "chunk_index": index,
            "content": chunk,
            "created_at": now,
        }
        for index, chunk in enumerate(chunks)
    ]

    if chunk_docs:
        insert_result = database.document_chunks.insert_many(chunk_docs)
        chunk_ids = insert_result.inserted_ids
        embeddings_by_model = generate_embedding_sets(chunks)
        embedding_rows = []
        for model_name, vectors in embeddings_by_model.items():
            for chunk_id, vector in zip(chunk_ids, vectors, strict=False):
                embedding_rows.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": document["_id"],
                        "project_id": document["project_id"],
                        "vector": vector,
                        "model_name": model_name,
                        "created_at": now,
                    }
                )
        if embedding_rows:
            database.chunk_embeddings.insert_many(embedding_rows)

    database.documents.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "extracted_text": extracted_text,
                "chunk_count": len(chunk_docs),
                "indexing_status": "completed",
                "updated_at": now,
            }
        },
    )


def cascade_delete_document(document: dict) -> None:
    database = get_db()
    from api.storage import delete_media_file

    delete_media_file(document.get("file_path"))
    delete_media_file(document.get("thumbnail_image_path"))
    database.document_chunks.delete_many({"document_id": document["_id"]})
    database.chunk_embeddings.delete_many({"document_id": document["_id"]})
    database.documents.delete_one({"_id": document["_id"]})


def cascade_delete_project(project: dict) -> None:
    database = get_db()
    from api.storage import delete_media_file

    delete_media_file(project.get("cover_image_path"))
    documents = list(database.documents.find({"project_id": project["_id"]}))
    for document in documents:
        cascade_delete_document(document)

    conversation_ids = [row["_id"] for row in database.conversations.find({"project_id": project["_id"]})]
    if conversation_ids:
        database.messages.delete_many({"conversation_id": {"$in": conversation_ids}})
    database.conversations.delete_many({"project_id": project["_id"]})
    database.semantic_query_logs.delete_many({"project_id": project["_id"]})
    database.project_members.delete_many({"project_id": project["_id"]})
    database.projects.delete_one({"_id": project["_id"]})
