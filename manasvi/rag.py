import re


class KnowledgeBase:
    def __init__(self, path, chunk_size=700, overlap=120, enable_vector=False):
        self.path = path
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.enable_vector = enable_vector
        self.chunks = []
        self.index = None
        self.embedding_model = None
        self.ready = False
        self.error = None
        self._load()

    def _load(self):
        if not self.path.exists():
            self.error = f"Knowledge base not found: {self.path}"
            return

        text = self.path.read_text(encoding="utf-8")
        self.chunks = self._chunk_text(text)
        if not self.enable_vector:
            return

        try:
            import faiss
            import numpy as np
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = self.embedding_model.encode(self.chunks)
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(np.array(embeddings))
            self.ready = True
        except Exception as exc:
            self.error = str(exc)

    def query(self, user_query, top_k=2):
        if not user_query or not self.chunks:
            return ""

        if self.ready:
            import numpy as np

            query_embedding = self.embedding_model.encode([user_query])
            _, indices = self.index.search(np.array(query_embedding), top_k)
            return "\n\n".join(self.chunks[i] for i in indices[0])

        query_terms = set(re.findall(r"[a-zA-Z]{4,}", user_query.lower()))
        scored = []
        for chunk in self.chunks:
            chunk_terms = set(re.findall(r"[a-zA-Z]{4,}", chunk.lower()))
            scored.append((len(query_terms & chunk_terms), chunk))
        scored.sort(reverse=True, key=lambda item: item[0])
        return "\n\n".join(chunk for score, chunk in scored[:top_k] if score > 0) or self.chunks[0]

    def _chunk_text(self, text):
        normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
        if not normalized:
            return []

        chunks = []
        start = 0
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            chunks.append(normalized[start:end].strip())
            if end == len(normalized):
                break
            start = max(end - self.overlap, 0)
        return chunks
