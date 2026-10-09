import json
import os
import tempfile
from pathlib import Path

import faiss
import numpy as np


class VectorStoreError(Exception):
    """Raised when a local FAISS index is missing or inconsistent."""


class FaissVectorStore:
    INDEX_FILENAME = "medical.faiss"
    METADATA_FILENAME = "medical.metadata.json"

    def __init__(self, index_dir=None):
        self.index_dir = (
            Path(index_dir)
            if index_dir
            else Path(__file__).resolve().parents[2] / "data" / "faiss"
        )

    @property
    def index_path(self):
        return self.index_dir / self.INDEX_FILENAME

    @property
    def metadata_path(self):
        return self.index_dir / self.METADATA_FILENAME

    @property
    def exists(self):
        return self.index_path.is_file() and self.metadata_path.is_file()

    def save(self, vectors, records):
        matrix = np.ascontiguousarray(vectors, dtype=np.float32)
        if (
            matrix.ndim != 2
            or matrix.shape[0] != len(records)
            or not len(records)
            or matrix.shape[1] == 0
        ):
            raise VectorStoreError("Vector and source metadata counts must match and be non-empty.")

        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        index_temp = None
        metadata_temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.index_dir, suffix=".faiss.tmp", delete=False) as file:
                index_temp = Path(file.name)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.index_dir, suffix=".json.tmp", delete=False
            ) as file:
                metadata_temp = Path(file.name)
                json.dump(records, file, ensure_ascii=False)

            faiss.write_index(index, str(index_temp))
            os.replace(index_temp, self.index_path)
            os.replace(metadata_temp, self.metadata_path)
        finally:
            for temp_path in (index_temp, metadata_temp):
                if temp_path and temp_path.exists():
                    temp_path.unlink()
        return index.ntotal

    def search(self, query_vector, limit=4):
        if not self.exists:
            return []
        try:
            index = faiss.read_index(str(self.index_path))
            records = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, RuntimeError) as exc:
            raise VectorStoreError("The local medical search index could not be read.") from exc

        if index.ntotal != len(records):
            raise VectorStoreError("The local medical index and source metadata do not match.")

        query = np.ascontiguousarray(query_vector, dtype=np.float32)
        scores, ids = index.search(query, min(limit, index.ntotal))
        results = []
        for score, record_id in zip(scores[0], ids[0]):
            if record_id < 0:
                continue
            results.append({**records[int(record_id)], "score": float(score)})
        return results
