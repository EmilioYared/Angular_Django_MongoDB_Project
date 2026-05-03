from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from django.test import SimpleTestCase

from api.documents import chunk_text
from api.semantic import (
    LOCAL_EMBEDDING_DIMENSION,
    LOCAL_MODEL_NAME,
    cosine_similarity,
    generate_grounded_answer,
    local_hash_embedding,
    rank_project_matches,
)


class FakeCollection:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.last_query: dict | None = None

    def find(self, query: dict):
        self.last_query = query
        return [row for row in self.rows if self._matches(row, query)]

    def _matches(self, row: dict, query: dict) -> bool:
        for key, value in query.items():
            row_value = row.get(key)
            if isinstance(value, dict) and "$in" in value:
                if row_value not in value["$in"]:
                    return False
            elif row_value != value:
                return False
        return True


class DocumentProcessingTests(SimpleTestCase):
    def test_chunk_text_splits_large_text(self):
        text = " ".join(f"word{i}" for i in range(300))

        chunks = chunk_text(text, chunk_size=120, overlap=20)

        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(chunk.strip() for chunk in chunks))


class SemanticUtilityTests(SimpleTestCase):
    def test_local_embedding_has_stable_dimension(self):
        vector = local_hash_embedding("project isolation semantic search")

        self.assertEqual(len(vector), LOCAL_EMBEDDING_DIMENSION)
        self.assertTrue(any(value != 0 for value in vector))

    def test_cosine_similarity_self_match_is_one(self):
        vector = local_hash_embedding("same text")

        self.assertAlmostEqual(cosine_similarity(vector, vector), 1.0)

    def test_generate_grounded_answer_returns_no_match_message_without_context(self):
        answer = generate_grounded_answer("What is this?", [])

        self.assertIn("could not find enough matching content", answer)


class SemanticIsolationTests(SimpleTestCase):
    def test_rank_project_matches_queries_only_selected_project(self):
        project_a = ObjectId()
        project_b = ObjectId()
        document_a = ObjectId()
        document_b = ObjectId()
        chunk_a = ObjectId()
        chunk_b = ObjectId()

        query_vector = local_hash_embedding("alpha isolation")
        fake_db = SimpleNamespace(
            chunk_embeddings=FakeCollection(
                [
                    {
                        "chunk_id": chunk_a,
                        "document_id": document_a,
                        "project_id": project_a,
                        "vector": query_vector,
                        "model_name": LOCAL_MODEL_NAME,
                    },
                    {
                        "chunk_id": chunk_b,
                        "document_id": document_b,
                        "project_id": project_b,
                        "vector": query_vector,
                        "model_name": LOCAL_MODEL_NAME,
                    },
                ]
            ),
            document_chunks=FakeCollection(
                [
                    {
                        "_id": chunk_a,
                        "document_id": document_a,
                        "project_id": project_a,
                        "chunk_index": 0,
                        "content": "Alpha project-only content.",
                    },
                    {
                        "_id": chunk_b,
                        "document_id": document_b,
                        "project_id": project_b,
                        "chunk_index": 0,
                        "content": "Beta content must not leak.",
                    },
                ]
            ),
            documents=FakeCollection(
                [
                    {"_id": document_a, "project_id": project_a, "title": "Alpha Doc"},
                    {"_id": document_b, "project_id": project_b, "title": "Beta Doc"},
                ]
            ),
        )

        with patch("api.semantic.get_db", return_value=fake_db), patch(
            "api.semantic.generate_query_embeddings", return_value={LOCAL_MODEL_NAME: query_vector}
        ):
            matches = rank_project_matches(project_a, "alpha isolation", top_k=5)

        self.assertEqual([match["document_title"] for match in matches], ["Alpha Doc"])
        self.assertEqual(fake_db.chunk_embeddings.last_query["project_id"], project_a)
        self.assertEqual(fake_db.document_chunks.last_query["project_id"], project_a)
        self.assertEqual(fake_db.documents.last_query["project_id"], project_a)
