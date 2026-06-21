from __future__ import annotations

import json
import hashlib
import math
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import UploadFile

from chitung_center.config import settings


SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown", ".html", ".htm"}


class RagServiceError(RuntimeError):
    """Clear user-facing RAG failure that should not crash FastAPI startup."""


class RagDependencyError(RagServiceError):
    pass


class RagService:
    collection_name = "chitung_rag"

    def __init__(self) -> None:
        self.chroma_dir = settings.rag_chroma_dir
        self.meta_path = settings.rag_meta_path
        self.upload_dir = settings.rag_upload_dir
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._sentence_model: Any | None = None

    async def upload_document(self, upload: UploadFile, collection: str = "default") -> dict[str, Any]:
        filename = Path(upload.filename or "document").name
        suffix = Path(filename).suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            raise RagServiceError(f"Unsupported document type: {suffix or '(none)'}")

        doc_id = uuid.uuid4().hex
        target = self.upload_dir / f"{doc_id}{suffix}"
        content = await upload.read()
        if not content:
            raise RagServiceError("Uploaded file is empty.")
        target.write_bytes(content)

        text = self._load_text(target, filename)
        chunks = self._split_text(text)
        if not chunks:
            raise RagServiceError("No searchable text could be extracted from the document.")

        chunk_ids = [f"{doc_id}:{idx}" for idx in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "file_name": filename,
                "file_type": suffix.lstrip("."),
                "chunk_index": idx,
                "collection": collection or "default",
            }
            for idx in range(len(chunks))
        ]
        embeddings = await self._embed_texts(chunks)
        collection_obj = self._collection()
        if embeddings is None:
            collection_obj.add(ids=chunk_ids, documents=chunks, metadatas=metadatas)
        else:
            collection_obj.add(ids=chunk_ids, documents=chunks, metadatas=metadatas, embeddings=embeddings)

        meta = self._read_meta()
        meta[doc_id] = {
            "doc_id": doc_id,
            "file_name": filename,
            "file_type": suffix.lstrip("."),
            "chunk_count": len(chunks),
            "collection": collection or "default",
            "stored_path": str(target),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_meta(meta)
        return {"ok": True, "doc_id": doc_id, "chunk_count": len(chunks), "file_name": filename}

    def list_documents(self) -> dict[str, Any]:
        meta = self._read_meta()
        return {"ok": True, "items": sorted(meta.values(), key=lambda item: item.get("created_at", ""), reverse=True)}

    def delete_document(self, doc_id: str) -> dict[str, Any]:
        meta = self._read_meta()
        if doc_id not in meta:
            raise RagServiceError(f"Document not found: {doc_id}")
        self._collection().delete(where={"doc_id": doc_id})
        stored_path = meta[doc_id].get("stored_path")
        if stored_path:
            Path(str(stored_path)).unlink(missing_ok=True)
        removed = meta.pop(doc_id)
        self._write_meta(meta)
        return {"ok": True, "doc_id": doc_id, "removed_chunks": removed.get("chunk_count", 0)}

    async def query(self, query: str, top_k: int = 5, collection: str | None = None) -> dict[str, Any]:
        where = {"collection": collection} if collection else None
        query_embeddings = await self._embed_texts([query])
        if query_embeddings is None:
            result = self._collection().query(query_texts=[query], n_results=top_k, where=where)
        else:
            result = self._collection().query(query_embeddings=query_embeddings, n_results=top_k, where=where)
        documents = result.get("documents", [[]])[0] if result.get("documents") else []
        metadatas = result.get("metadatas", [[]])[0] if result.get("metadatas") else []
        distances = result.get("distances", [[]])[0] if result.get("distances") else []
        matches = []
        for idx, text in enumerate(documents):
            metadata = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}
            matches.append(
                {
                    "text": text,
                    "source_file_name": metadata.get("file_name", ""),
                    "doc_id": metadata.get("doc_id", ""),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "collection": metadata.get("collection", "default"),
                    "score": distances[idx] if idx < len(distances) else None,
                }
            )
        return {"ok": True, "query": query, "items": matches}

    def stats(self) -> dict[str, Any]:
        meta = self._read_meta()
        chunk_count = sum(int(item.get("chunk_count", 0)) for item in meta.values())
        try:
            vector_count = self._collection().count()
        except Exception:
            vector_count = 0
        return {
            "ok": True,
            "document_count": len(meta),
            "chunk_count": chunk_count,
            "vector_count": vector_count,
            "chroma_dir": str(self.chroma_dir),
        }

    def _collection(self) -> Any:
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as exc:
            raise RagDependencyError("ChromaDB is not installed. Run pip install -r requirements.txt.") from exc
        client = chromadb.PersistentClient(path=str(self.chroma_dir), settings=Settings(anonymized_telemetry=False))
        return client.get_or_create_collection(self.collection_name)

    def _read_meta(self) -> dict[str, dict[str, Any]]:
        if not self.meta_path.exists():
            return {}
        try:
            data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write_meta(self, meta: dict[str, dict[str, Any]]) -> None:
        self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_text(self, path: Path, original_name: str) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._load_pdf(path)
        if suffix == ".docx":
            return self._load_docx(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        if suffix in {".html", ".htm"}:
            text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            raise RagServiceError(f"No text extracted from {original_name}.")
        return text

    def _load_pdf(self, path: Path) -> str:
        try:
            from langchain_community.document_loaders import PyPDFLoader

            docs = PyPDFLoader(str(path)).load()
            text = "\n".join(doc.page_content for doc in docs)
        except Exception:
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise RagDependencyError("PDF parsing requires pypdf or langchain-community.") from exc
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        text = text.strip()
        if not text:
            raise RagServiceError("No text extracted from PDF.")
        return text

    def _load_docx(self, path: Path) -> str:
        try:
            from langchain_community.document_loaders import Docx2txtLoader

            docs = Docx2txtLoader(str(path)).load()
            text = "\n".join(doc.page_content for doc in docs)
        except Exception:
            try:
                from docx import Document
            except ImportError as exc:
                raise RagDependencyError("DOCX parsing requires python-docx.") from exc
            doc = Document(str(path))
            text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        text = text.strip()
        if not text:
            raise RagServiceError("No text extracted from DOCX.")
        return text

    def _split_text(self, text: str) -> list[str]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            except ImportError:
                return _simple_split_text(text, chunk_size=500, overlap=50)
        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]

    async def _embed_texts(self, texts: list[str]) -> list[list[float]] | None:
        last_error: Exception | None = None
        if settings.llm_configured:
            try:
                return await self._embed_with_llm_gateway(texts)
            except Exception as exc:
                last_error = exc
        try:
            return self._embed_with_sentence_transformers(texts)
        except Exception as exc:
            if last_error:
                print(f"RAG LLM embedding failed, falling back locally: {last_error}")
            print(f"RAG sentence-transformers unavailable, using local hash embeddings: {exc}")
            return _embed_with_local_hash(texts)

    async def _embed_with_llm_gateway(self, texts: list[str]) -> list[list[float]]:
        url = settings.llm_embedding_base_url or _default_embedding_url(settings.llm_base_url)
        model = settings.llm_embedding_model or settings.llm_model
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json={"model": model, "input": texts})
            response.raise_for_status()
            data = response.json()
        vectors = [item.get("embedding") for item in data.get("data", [])]
        if len(vectors) != len(texts) or not all(isinstance(item, list) for item in vectors):
            raise RagServiceError("Embedding endpoint returned an unexpected response shape.")
        return vectors

    def _embed_with_sentence_transformers(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RagDependencyError("sentence-transformers is not installed.") from exc
        if self._sentence_model is None:
            self._sentence_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        vectors = self._sentence_model.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]


def _default_embedding_url(base_url: str) -> str:
    stripped = base_url.rstrip("/")
    if stripped.endswith("/chat/completions"):
        return stripped[: -len("/chat/completions")] + "/embeddings"
    if stripped.endswith("/v1"):
        return stripped + "/embeddings"
    return stripped + "/embeddings"


def _simple_split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(normalized):
        chunks.append(normalized[start : start + chunk_size])
        start += step
    return chunks


def _embed_with_local_hash(texts: list[str], dimensions: int = 384) -> list[list[float]]:
    vectors: list[list[float]] = []
    for text in texts:
        vector = [0.0] * dimensions
        normalized = re.sub(r"\s+", " ", text.lower()).strip()
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", normalized)
        features = tokens or [normalized]
        for token in features:
            digest = hashlib.blake2b(token.encode("utf-8", errors="ignore"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        vectors.append([value / norm for value in vector])
    return vectors


rag_service = RagService()
