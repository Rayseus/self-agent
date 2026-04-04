"""文档导入脚本：读取 data/ 下的 Markdown 文件，切分后写入 documents + chunks 表。

用法：
    cd backend
    python -m scripts.ingest
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Chunk, Document, Embedding
from app.services.embedding_client import embed_texts

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CHUNK_MAX_TOKENS = 600
CHUNK_OVERLAP_TOKENS = 80


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数：CJK 字符按 1 token，ASCII 单词按 1 token。"""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    ascii_words = len(re.findall(r"[a-zA-Z0-9]+", text))
    return cjk + ascii_words


def split_by_headings(content: str) -> list[dict]:
    """按 Markdown 标题（#/##/###）分段。"""
    pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(content))

    if not matches:
        return [{"heading": "", "text": content.strip()}]

    sections: list[dict] = []

    pre = content[: matches[0].start()].strip()
    if pre:
        sections.append({"heading": "", "text": pre})

    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        if text:
            sections.append({"heading": m.group(2).strip(), "text": text})

    return sections


def chunk_text(
    text: str,
    max_tokens: int = CHUNK_MAX_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> list[str]:
    """将文本按 token 限制切块，句级粒度 + overlap。"""
    if estimate_tokens(text) <= max_tokens:
        return [text]

    sentences = re.split(r"(?<=[。！？\n])", text)
    sentences = [s for s in sentences if s.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = estimate_tokens(sent)
        if current_tokens + sent_tokens > max_tokens and current:
            chunks.append("".join(current))
            overlap: list[str] = []
            overlap_count = 0
            for s in reversed(current):
                t = estimate_tokens(s)
                if overlap_count + t > overlap_tokens:
                    break
                overlap.insert(0, s)
                overlap_count += t
            current = overlap
            current_tokens = overlap_count
        current.append(sent)
        current_tokens += sent_tokens

    if current:
        chunks.append("".join(current))

    return chunks


def ingest(dry_run: bool = False) -> None:
    md_files = sorted(DATA_DIR.glob("*.md"))
    if not md_files:
        print(f"未在 {DATA_DIR} 下找到 .md 文件")
        return

    if dry_run:
        print("[dry-run] 仅验证切分逻辑，不写入数据库\n")
        total_chunks = 0
        for fp in md_files:
            content = fp.read_text(encoding="utf-8")
            sections = split_by_headings(content)
            file_chunks = 0
            for sec in sections:
                chunks = chunk_text(sec["text"])
                for c in chunks:
                    tokens = estimate_tokens(c)
                    print(f"  [{fp.name}] heading={sec['heading']!r}  tokens={tokens}")
                    print(f"    {c[:80]}{'...' if len(c) > 80 else ''}")
                    file_chunks += 1
            total_chunks += file_chunks
            print(f"  ✓ {fp.name} → {len(sections)} 段 → {file_chunks} 个 chunk\n")
        print(f"汇总：{len(md_files)} 个文档，{total_chunks} 个 chunk")
        return

    session = SessionLocal()
    try:
        session.query(Document).delete()
        session.commit()

        all_chunks: list[Chunk] = []
        all_texts: list[str] = []

        for fp in md_files:
            content = fp.read_text(encoding="utf-8")
            doc = Document(
                source_type="markdown",
                source_name=fp.name,
                content=content,
            )
            session.add(doc)
            session.flush()

            sections = split_by_headings(content)
            for sec in sections:
                for chunk_str in chunk_text(sec["text"]):
                    chunk = Chunk(
                        document_id=doc.id,
                        chunk_text=chunk_str,
                        metadata_={"heading": sec["heading"], "source": fp.name},
                    )
                    session.add(chunk)
                    all_chunks.append(chunk)
                    all_texts.append(chunk_str)

            print(f"  ✓ {fp.name} → {len(sections)} 段")

        session.flush()

        print(f"\n生成 Embedding（{len(all_texts)} 条）...")
        BATCH_SIZE = 100
        for i in range(0, len(all_texts), BATCH_SIZE):
            batch_texts = all_texts[i : i + BATCH_SIZE]
            batch_chunks = all_chunks[i : i + BATCH_SIZE]
            vectors = embed_texts(batch_texts)
            for chunk, vec in zip(batch_chunks, vectors):
                session.add(Embedding(chunk_id=chunk.id, embedding=vec))
            print(f"  Embedding batch {i // BATCH_SIZE + 1} 完成")

        session.commit()
        print(f"\n导入完成：{len(md_files)} 个文档，{len(all_chunks)} 个 chunk + embedding")
    except Exception as e:
        session.rollback()
        print(f"导入失败：{e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="导入 data/ 下的文档到数据库")
    parser.add_argument("--dry-run", action="store_true", help="仅验证切分，不连接数据库")
    args = parser.parse_args()
    ingest(dry_run=args.dry_run)
