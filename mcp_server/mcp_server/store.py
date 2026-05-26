from dataclasses import dataclass
from pathlib import Path


class DocumentNotFoundError(Exception):
    pass


@dataclass
class Document:
    id: str
    content: str
    mime_type: str


class DocumentStore:
    def __init__(self, docs_dir: Path) -> None:
        self._docs: dict[str, Document] = {}
        for path in sorted(docs_dir.iterdir()):
            if path.is_file() and path.suffix in (".md", ".txt"):
                mime = "text/markdown" if path.suffix == ".md" else "text/plain"
                self._docs[path.name] = Document(
                    id=path.name,
                    content=path.read_text(encoding="utf-8"),
                    mime_type=mime,
                )

    def list(self) -> list[Document]:
        return list(self._docs.values())

    def get(self, id: str) -> Document:
        if id not in self._docs:
            raise DocumentNotFoundError(f"Document '{id}' not found")
        return self._docs[id]

    def replace(self, id: str, content: str) -> Document:
        doc = self.get(id)
        self._docs[id] = Document(id=id, content=content, mime_type=doc.mime_type)
        return self._docs[id]

    def append(self, id: str, content: str) -> Document:
        doc = self.get(id)
        self._docs[id] = Document(id=id, content=doc.content + content, mime_type=doc.mime_type)
        return self._docs[id]
