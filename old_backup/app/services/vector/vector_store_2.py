import json
import uuid
from datetime import datetime

import faiss
import numpy as np


class VectorStore:

    def __init__(self):

        self.index = None

        self.embedding_dim = None

        # 실제 문서 저장
        self.documents = []

        # metadata 저장
        self.metadatas = []

        # document uuid 저장
        self.doc_ids = []

    # =========================================================
    # 내부 유틸
    # =========================================================

    def _initialize_index(self, dim):

        self.embedding_dim = dim

        # cosine similarity
        self.index = faiss.IndexFlatIP(dim)

    def _normalize_vectors(self, vectors):

        norms = np.linalg.norm(
            vectors,
            axis=1,
            keepdims=True
        )

        # zero division 방지
        norms = np.clip(norms, 1e-12, None)

        return vectors / norms

    def _validate_dimension(self, embeddings):

        if not embeddings:
            return

        dim = len(embeddings[0])

        if self.index is None:

            self._initialize_index(dim)

            return

        if dim != self.embedding_dim:

            raise ValueError(
                f"Embedding dimension mismatch: "
                f"{dim} != {self.embedding_dim}"
            )

    # =========================================================
    # 기본 add
    # =========================================================

    def add_embeddings(
        self,
        embeddings,
        docs,
        metadata_list=None
    ):

        if not embeddings:
            return

        self._validate_dimension(embeddings)

        vectors = np.array(
            embeddings,
            dtype="float32"
        )

        vectors = self._normalize_vectors(vectors)

        self.index.add(vectors)

        if metadata_list is None:
            metadata_list = [{} for _ in docs]

        for doc, meta in zip(docs, metadata_list):

            self.documents.append(doc)

            self.metadatas.append(meta)

            self.doc_ids.append(
                str(uuid.uuid4())
            )

    # =========================================================
    # similarity search
    # =========================================================

    def similarity_search(
        self,
        query_embedding,
        top_k=5
    ):

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        query_vector = np.array(
            [query_embedding],
            dtype="float32"
        )

        query_vector = self._normalize_vectors(
            query_vector
        )

        distances, indices = self.index.search(
            query_vector,
            top_k
        )

        results = []

        for idx, dist in zip(
            indices[0],
            distances[0]
        ):

            if idx < 0:
                continue

            if idx >= len(self.documents):
                continue

            results.append({
                "index": int(idx),
                "doc_id": self.doc_ids[idx],
                "document": self.documents[idx],
                "score": float(dist),
                "metadata": self.metadatas[idx]
            })

        return results

    # =========================================================
    # dedup append
    # =========================================================

    def append_if_new(
        self,
        embedding,
        document,
        metadata=None,
        similarity_threshold=0.95
    ):

        metadata = metadata or {}

        results = self.similarity_search(
            embedding,
            top_k=1
        )

        if results:

            top_score = results[0]["score"]

            # 이미 매우 유사한 문서 존재
            if top_score >= similarity_threshold:

                return {
                    "status": "skipped",
                    "score": top_score
                }

        self.add_embeddings(
            embeddings=[embedding],
            docs=[document],
            metadata_list=[metadata]
        )

        return {
            "status": "appended"
        }

    # =========================================================
    # selective merge
    # =========================================================

    def merge_from(
        self,
        source_store,
        source_indices,
        embedding_fn,
        similarity_threshold=0.95
    ):

        appended = []

        skipped = []

        for idx in source_indices:

            if idx >= len(source_store.documents):
                continue

            document = source_store.documents[idx]

            metadata = source_store.metadatas[idx]

            embedding = embedding_fn(document)

            result = self.append_if_new(
                embedding=embedding,
                document=document,
                metadata=metadata,
                similarity_threshold=similarity_threshold
            )

            if result["status"] == "appended":

                appended.append(idx)

            else:

                skipped.append({
                    "index": idx,
                    "score": result["score"]
                })

        return {
            "appended": appended,
            "skipped": skipped
        }

    # =========================================================
    # 저장
    # =========================================================

    def save(
        self,
        index_path,
        documents_path
    ):

        if self.index is not None:

            faiss.write_index(
                self.index,
                index_path
            )

        data = []

        for doc_id, doc, meta in zip(
            self.doc_ids,
            self.documents,
            self.metadatas
        ):

            data.append({
                "doc_id": doc_id,
                "document": doc,
                "metadata": meta
            })

        with open(
            documents_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    # =========================================================
    # 로드
    # =========================================================

    def load(
        self,
        index_path,
        documents_path
    ):

        self.index = faiss.read_index(
            index_path
        )

        self.embedding_dim = self.index.d

        with open(
            documents_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        self.documents = [
            d["document"]
            for d in data
        ]

        self.metadatas = [
            d["metadata"]
            for d in data
        ]

        self.doc_ids = [
            d["doc_id"]
            for d in data
        ]

    # =========================================================
    # 상태 정보
    # =========================================================

    def stats(self):

        return {
            "total_documents": len(self.documents),
            "embedding_dim": self.embedding_dim,
            "index_size": (
                self.index.ntotal
                if self.index
                else 0
            )
        }
