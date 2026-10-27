"""Build a traceable text-only NCI corpus. No patient data or model output is used."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = ROOT / "source_cache"
OUTPUT = DATA / "corpus.jsonl"
LOCK = DATA / "source_lock.json"
SKIP_TAGS = {"script", "style", "nav", "aside", "footer", "form", "figure", "noscript"}
TEXT_TAGS = {"h1", "h2", "h3", "h4", "p", "li", "tr"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
EXCLUDE_SECTIONS = {"references", "current clinical trials", "related resources",
                    "about pdq", "about this pdq summary", "reviewers and updates",
                    "clinical trial information", "permission to use this summary",
                    "disclaimer", "contact us", "purpose of this summary",
                    "levels of evidence"}


def clean(value):
    return re.sub(r"\s+", " ", value).strip()


class MainTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.main_depth = 0
        self.skip_depth = 0
        self.capture = None
        self.buffer = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if not self.in_main:
            if tag == "main":
                self.in_main = True
                self.main_depth = 1
            return
        if tag in VOID_TAGS:
            if tag == "br" and self.capture:
                self.buffer.append(" ")
            return
        self.main_depth += 1
        if self.skip_depth:
            self.skip_depth += 1
            return
        if tag in SKIP_TAGS:
            self.skip_depth = 1
            return
        if tag in TEXT_TAGS and self.capture is None:
            self.capture = (tag, self.main_depth)
            self.buffer = []
        elif tag == "br" and self.capture:
            self.buffer.append(" ")

    def handle_startendtag(self, tag, attrs):
        if tag == "br" and self.capture:
            self.buffer.append(" ")

    def handle_data(self, data):
        if self.in_main and not self.skip_depth and self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if not self.in_main:
            return
        if self.skip_depth:
            self.skip_depth -= 1
        elif self.capture and tag == self.capture[0] and self.main_depth == self.capture[1]:
            value = clean("".join(self.buffer))
            if value:
                self.blocks.append((tag, value))
            self.capture = None
            self.buffer = []
        self.main_depth -= 1
        if tag == "main" or self.main_depth <= 0:
            self.in_main = False


def extract_blocks(html):
    parser = MainTextParser()
    parser.feed(html)
    return parser.blocks


def chunks_for(source, blocks, html_sha, accessed_at, source_date):
    section = source["title"]
    excluded = False
    paragraphs = []
    chunks = []

    def flush():
        if not paragraphs:
            return
        content = "\n".join(paragraphs)
        chunks.append({
            "chunk_id": f"{source['id']}:{len(chunks) + 1:04d}",
            "source_id": source["id"], "title": source["title"],
            "publisher": "National Cancer Institute", "url": source["url"],
            "authors": source["authors"], "source_date": source_date,
            "section": section, "accessed_at": accessed_at,
            "source_sha256": html_sha,
            "text_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "text": content,
        })
        paragraphs.clear()

    for tag, value in blocks:
        if tag.startswith("h"):
            flush()
            section = value
            excluded = value.casefold() in EXCLUDE_SECTIONS
            continue
        if excluded:
            continue
        if value.startswith("You can help speed up the development of new treatments"):
            continue
        if len(value) < 35 or value == (paragraphs[-1] if paragraphs else None):
            continue
        if len(value) > 1300:
            flush()
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", value)
            for sentence in sentences:
                if paragraphs and sum(map(len, paragraphs)) + len(sentence) > 1300:
                    flush()
                paragraphs.append(sentence)
            flush()
            continue
        if paragraphs and sum(map(len, paragraphs)) + len(value) > 1300:
            flush()
        paragraphs.append(value)
    flush()
    unique = []
    seen = set()
    for chunk in chunks:
        if chunk["text_sha256"] not in seen:
            chunk["chunk_id"] = f"{source['id']}:{len(unique) + 1:04d}"
            unique.append(chunk)
            seen.add(chunk["text_sha256"])
    return unique


def download(source):
    parsed = urlparse(source["url"])
    if parsed.scheme != "https" or parsed.netloc != "www.cancer.gov":
        raise ValueError(f"Source URL is not an approved NCI HTTPS URL: {source['url']}")
    request = Request(source["url"], headers={"User-Agent": "BoneScope-research-corpus/1.0"})
    with urlopen(request, timeout=30) as response:
        if "text/html" not in response.headers.get("Content-Type", ""):
            raise ValueError(f"Not HTML: {source['id']}")
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError(f"Source exceeds 5 MB: {source['id']}")
    return data


def build(offline=False):
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    if len(sources) < 10 or len({item["id"] for item in sources}) != len(sources):
        raise ValueError("The corpus needs at least 10 distinct sources")
    CACHE.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    all_chunks = []
    lock = []
    for source in sources:
        source = {**source, "authors": ("PDQ Pediatric Treatment Editorial Board"
                  if "-pdq" in source["url"] else "National Cancer Institute")}
        cache_path = CACHE / f"{source['id']}.html"
        if offline:
            data = cache_path.read_bytes()
            accessed_at = datetime.fromtimestamp(cache_path.stat().st_mtime, timezone.utc).isoformat()
        else:
            data = download(source)
            cache_path.write_bytes(data)
            accessed_at = datetime.now(timezone.utc).isoformat()
        html_sha = hashlib.sha256(data).hexdigest()
        html = data.decode("utf-8", errors="replace")
        dates = re.findall(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})', html)
        source_date = dates[-1] if dates else None
        blocks = extract_blocks(html)
        chunks = chunks_for(source, blocks, html_sha, accessed_at, source_date)
        if not chunks:
            raise ValueError(f"No text extracted from {source['id']}")
        all_chunks.extend(chunks)
        lock.append({**source, "publisher": "National Cancer Institute",
                     "license": "NCI text reuse policy; credit and link to source; no images",
                     "license_url": "https://www.cancer.gov/policies/copyright-reuse",
                     "accessed_at": accessed_at, "source_date": source_date,
                     "html_sha256": html_sha,
                     "chunk_count": len(chunks)})
        print(f"{source['id']}: {len(chunks)} chunks")
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_chunks), encoding="utf-8")
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(all_chunks)} chunks from {len(lock)} sources")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Rebuild from cached HTML")
    build(parser.parse_args().offline)
