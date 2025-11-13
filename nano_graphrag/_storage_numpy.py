"""Simple NumPy-based vector storage for Windows compatibility"""
import os
import json
import numpy as np
from dataclasses import dataclass
from typing import Union

from .base import BaseVectorStorage
from ._utils import logger


@dataclass
class NumpyVectorStorage(BaseVectorStorage):
    """Simple in-memory vector storage using NumPy for cosine similarity"""

    def __post_init__(self):
        self._data = {}
        self._embeddings = None
        self._ids = []
        self._storage_file = os.path.join(
            self.global_config["working_dir"],
            f"vdb_{self.namespace}.json"
        )
        # Try to load existing data
        if os.path.exists(self._storage_file):
            self._load()

    async def query(self, query: str, top_k: int) -> list[dict]:
        """Query by cosine similarity"""
        if not self._data:
            return []

        # Get query embedding
        query_embedding = await self.embedding_func([query])
        query_vec = np.array(query_embedding[0])

        # Compute cosine similarities
        if self._embeddings is None:
            return []

        # Normalize vectors
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        embeddings_norm = self._embeddings / (np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10)

        # Cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)

        # Get top_k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return positive similarities
                doc_id = self._ids[idx]
                result = self._data[doc_id].copy()
                result['similarity'] = float(similarities[idx])
                results.append(result)

        return results

    async def upsert(self, data: dict[str, dict]):
        """Insert or update vectors"""
        if not data:
            return

        # Extract content and compute embeddings if needed
        contents = []
        ids = []
        for doc_id, doc_data in data.items():
            if 'content' in doc_data:
                contents.append(doc_data['content'])
                ids.append(doc_id)
            elif 'embedding' in doc_data:
                # Use provided embedding
                self._data[doc_id] = doc_data

        # Compute embeddings for new content
        if contents:
            embeddings = await self.embedding_func(contents)
            for doc_id, content, embedding in zip(ids, contents, embeddings):
                doc_data = data[doc_id].copy()
                doc_data['embedding'] = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
                self._data[doc_id] = doc_data

        # Rebuild embedding matrix
        self._rebuild_index()

        # Save to disk
        self._save()

    def _rebuild_index(self):
        """Rebuild the numpy embedding matrix from stored data"""
        if not self._data:
            self._embeddings = None
            self._ids = []
            return

        self._ids = list(self._data.keys())
        embeddings_list = []
        for doc_id in self._ids:
            emb = self._data[doc_id].get('embedding', [])
            if isinstance(emb, list):
                embeddings_list.append(emb)
            else:
                embeddings_list.append(emb.tolist())

        if embeddings_list:
            self._embeddings = np.array(embeddings_list, dtype=np.float32)

    def _save(self):
        """Save data to JSON file"""
        try:
            # Convert numpy arrays to lists for JSON serialization
            save_data = {}
            for doc_id, doc_data in self._data.items():
                save_data[doc_id] = {}
                for key, value in doc_data.items():
                    if isinstance(value, np.ndarray):
                        save_data[doc_id][key] = value.tolist()
                    else:
                        save_data[doc_id][key] = value

            with open(self._storage_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f)
        except Exception as e:
            logger.warning(f"Failed to save vector storage: {e}")

    def _load(self):
        """Load data from JSON file"""
        try:
            with open(self._storage_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            self._rebuild_index()
            logger.info(f"Loaded {len(self._data)} vectors from {self._storage_file}")
        except Exception as e:
            logger.warning(f"Failed to load vector storage: {e}")
            self._data = {}

    async def index_done_callback(self):
        """Save after indexing"""
        self._save()
