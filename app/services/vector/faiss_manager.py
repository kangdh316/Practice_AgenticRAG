from __future__ import annotations

import threading
from pathlib import Path
from typing import List
import hashlib

import faiss
import numpy as np
from sympy import python

from app.services.vector.serializer import (
    save_metadata,
    load_metadata,
)
from app.llm.embedding import (document_embeddings)


class FAISSManager:

    def __init__(
        self,
        dim: int,
        base_dir: str = "./data/faiss",
    ):

        self.dim = dim

        self.base_dir = Path(base_dir)

        self.temp_dir = self.base_dir / "temp"
        self.prod_dir = self.base_dir / "prod"

        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.prod_dir.mkdir(parents=True, exist_ok=True)

        self.memory_index = None
        self.memory_docs = []

        self.lock = threading.Lock()

    # =========================================================
    # internal
    # =========================================================

    def _target_dir(self, target: str):

        if target == "temp":
            return self.temp_dir

        if target == "prod":
            return self.prod_dir

        raise ValueError(
            "target must be temp or prod"
        )

    def _index_path(self, target: str):

        return self._target_dir(target) / "index.faiss"

    def _meta_path(self, target: str):

        return self._target_dir(target) / "metadata.json"

    def _create_index(self):

        return faiss.IndexFlatIP(self.dim)

    def _to_faiss_vector(
        self,
        embedding,
    ):

        embedding = np.asarray(
            embedding,
            dtype=np.float32,
        )

        if embedding.ndim == 1:

            embedding = embedding.reshape(
                1,
                -1,
            )

        return embedding

    def _create_content_hash(
        self, text: str,
    ) -> str:
        normalized = ( text.strip() .replace("\r\n", "\n") )
        return hashlib.sha256( normalized.encode("utf-8") ).hexdigest()

    def _build_index_from_docs(
        self,
        docs: list[dict],
    ):

        index = self._create_index()

        if not docs:
            return index
        
        doc_contents = ", ".join([doc["content"] for doc in docs])

        embeddings = self._to_faiss_vector(document_embeddings(doc_contents))

        index.add(embeddings)

        return index

    def _save_target(
        self,
        target: str,
        docs: list[dict],
    ):

        index = self._build_index_from_docs(
            docs
        )

        faiss.write_index(
            index,
            str(self._index_path(target))
        )

        save_metadata(
            self._meta_path(target),
            docs,
        )

    # =========================================================
    # memory
    # =========================================================

    def load_memory(
        self,
        target: str = "prod",
    ):

        with self.lock:
            try:
                self.memory_index = faiss.read_index(
                    str(self._index_path(target))
                )

                self.memory_docs = load_metadata(
                    self._meta_path(target)
                )
            except Exception as e:

                print(
                    f"failed to load memory: {e}"
                )

                self.memory_index = None
                self.memory_docs = []

    def reset_memory(self):

        with self.lock:

            self.memory_index = None
            self.memory_docs = []

    # =========================================================
    # temp save
    # =========================================================

    def save_temp_documents(
        self,
        docs: list[dict],
        dedup: bool = True,
        similarity_threshold: float = 0.95,
    ):

        with self.lock:

            existing_docs = load_metadata(
                self._meta_path("temp")
            )

            final_docs = existing_docs.copy()

            for new_doc in docs:
                content = new_doc["content"]

                # -----------------------------------------
                # 1. content hash 생성
                # -----------------------------------------
                content_hash = ( self._create_content_hash( content ) )

                # -------------------------------------------------
                # 2. hash dedup
                # -------------------------------------------------
                is_duplicate = False

                if dedup:

                    for existing in existing_docs:
                        if (existing.get("content_hash") == content_hash):
                            is_duplicate = True
                            break

                if is_duplicate:
                    continue

                # -----------------------------------------
                # 3. embedding 생성
                # -----------------------------------------
                embedding = document_embeddings( content )
                embedding = np.asarray( embedding, dtype=np.float32, )

                # -------------------------------------------------
                # 4. similarity dedup
                # -------------------------------------------------
                if dedup and existing_docs:

                    similar_results = (
                        self._similarity_search_docs(
                            query_embedding=embedding,
                            docs=existing_docs,
                            top_k=1,
                        )
                    )

                    if similar_results:
                        top_score = (similar_results[0]["score"])

                        if (top_score >= similarity_threshold):
                            continue

                # -----------------------------------------
                # 5. save document
                # -----------------------------------------
                save_doc = {
                    **new_doc,
                    "content_hash": content_hash,
                }
                
                final_docs.append(save_doc)
                
                # 중복 검사 대상에도 즉시 반영
                existing_docs.append(save_doc)
            # -----------------------------------------
            # save
            # -----------------------------------------
            self._save_target( "temp", final_docs, )

    # =========================================================
    # temp 조회
    # =========================================================

    def get_temp_documents(self):

        return load_metadata(
            self._meta_path("temp")
        )

    # =========================================================
    # promote
    # =========================================================

    def promote_temp_to_prod(
        self,
        index_list: List[int],
    ):

        with self.lock:

            temp_docs = load_metadata(
                self._meta_path("temp")
            )

            prod_docs = load_metadata(
                self._meta_path("prod")
            )

            selected_docs = [
                temp_docs[i]
                for i in index_list
            ]

            prod_docs.extend(selected_docs)

            self._save_target(
                "prod",
                prod_docs,
            )

        self.load_memory()

    # =========================================================
    # delete by id
    # =========================================================

    def delete_document_by_id(
        self,
        target: str,
        doc_id: str,
    ):

        with self.lock:

            docs = load_metadata(
                self._meta_path(target)
            )

            filtered_docs = [
                doc
                for doc in docs
                if doc["id"] != doc_id
            ]

            self._save_target(
                target,
                filtered_docs,
            )

    # =========================================================
    # delete by index
    # =========================================================

    def delete_document_by_index(
        self,
        target: str,
        index: int,
    ):

        with self.lock:

            docs = load_metadata(
                self._meta_path(target)
            )

            if index >= len(docs):

                raise IndexError(
                    f"invalid index: {index}"
                )

            del docs[index]

            self._save_target(
                target,
                docs,
            )

    # =========================================================
    # similarity search
    # =========================================================

    def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ):

        if self.memory_index is None:

            raise RuntimeError(
                "memory not loaded"
            )

        query = np.array(
            [query_embedding],
            dtype=np.float32,
        )

        scores, indices = (
            self.memory_index.search(
                query,
                top_k,
            )
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue

            results.append(
                {
                    "score": float(score),
                    "document":
                        self.memory_docs[idx],
                }
            )

        return results

    # =========================================================
    # internal similarity
    # =========================================================

    def _similarity_search_docs(
        self,
        query_embedding,
        docs: list[dict],
        top_k: int = 1,
    ):

        if not docs:
            return []

        temp_index = self._build_index_from_docs(
            docs
        )

        query = np.asarray(
            query_embedding,
            dtype=np.float32,
        )

        if query.ndim == 1:
            query = query.reshape( 1, -1, )

        scores, indices = temp_index.search(
            query,
            top_k,
        )

        results = []

        for score, idx in zip(
            scores[0],
            indices[0],
        ):

            if idx == -1:
                continue

            results.append(
                {
                    "score": float(score),
                    "document": docs[idx],
                }
            )

        return results