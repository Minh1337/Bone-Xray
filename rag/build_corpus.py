"""Build a traceable, license-checked text-only corpus. No patient data is used."""

import argparse
import hashlib
import json
import re
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CACHE = ROOT / "source_cache"
OUTPUT = DATA / "corpus.jsonl"
LOCK = DATA / "source_lock.json"
SKIP_TAGS = {"script", "style", "nav", "aside", "footer", "form", "figure", "noscript"}
TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr"}
BLOCK_BOUNDARIES = TEXT_TAGS | {"td", "th", "ul", "ol"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}
EXCLUDE_SECTIONS = {"references", "current clinical trials", "related resources",
                    "about pdq", "about this pdq summary", "reviewers and updates",
                    "clinical trial information", "permission to use this summary",
                    "disclaimer", "contact us", "purpose of this summary",
                    "levels of evidence", "metrics", "author contributions",
                    "declaration of generative ai and ai-assisted technologies in the writing process",
                    "funding statement", "declaration of competing interest",
                    "funding", "data availability", "data availability statement",
                    "availability of data and materials",
                    "conflict of interest", "conflicts of interest", "competing interests",
                    "ethics approval and consent to participate", "consent for publication",
                    "acknowledgements", "acknowledgments", "contributor information",
                    "authors' contributions", "authors’ contributions"}
ALLOWED_HOSTS = {"www.cancer.gov", "openorthopaedicsjournal.com", "pmc.ncbi.nlm.nih.gov",
                 "www.ncbi.nlm.nih.gov", "www.ebi.ac.uk", "webapis.cancer.gov"}
CC_BY_4 = "https://creativecommons.org/licenses/by/4.0/"
NCI_LICENSE = "NCI text reuse policy; credit and link to source; no images"
NCI_LICENSE_URL = "https://www.cancer.gov/policies/copyright-reuse"


def explicitly_cc_by_4(statement, license_urls=()):
    """Accept the unmodified CC BY 4.0 identifier, never NC/ND/SA variants."""
    normalized = re.sub(r"\s+", " ", statement.casefold())
    url_text = " ".join(value.casefold() for value in license_urls if isinstance(value, str))
    normalized += " " + url_text
    restricted_markers = (
        r"\bnon[\s-]?commercial\b", r"\bno[\s-]?derivatives\b",
        r"\bshare[\s-]?alike\b", r"\bcc[\s-]?by[\s-]?(?:nc|nd|sa)\b",
        r"\battribution[\s-]?(?:noncommercial|noderivatives|sharealike)\b",
        r"/licenses/by-(?:nc|nd|sa)(?:/|\b)",
    )
    if any(re.search(pattern, normalized) for pattern in restricted_markers):
        return False
    for value in license_urls:
        parsed = urlparse(value.strip().rstrip(".,;)]}"))
        if (parsed.scheme in {"https", "http"}
                and parsed.hostname == "creativecommons.org"
                and parsed.path.rstrip("/") == "/licenses/by/4.0"):
            return True
    return bool(
        re.search(r"\bcc[\s-]*by\s+4\.0\b", normalized)
        or re.search(r"\bcreative commons attribution\s+4\.0\b", normalized)
    )


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
        elif tag in BLOCK_BOUNDARIES and self.capture:
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
        elif self.capture and tag in BLOCK_BOUNDARIES:
            self.buffer.append(" ")
        self.main_depth -= 1
        if tag == "main" or self.main_depth <= 0:
            self.in_main = False


def extract_blocks(html):
    parser = MainTextParser()
    parser.feed(html)
    return parser.blocks


def extract_bioc_blocks(raw):
    """Convert PMC BioC prose into sectioned text blocks; omit tables, figures and refs."""
    collection = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    if not isinstance(collection, list) or len(collection) != 1:
        raise ValueError("Expected one PMC BioC collection")
    documents = collection[0].get("documents", [])
    if len(documents) != 1:
        raise ValueError("Expected one BioC document")
    document = documents[0]
    doc_id = document.get("id")
    if not re.fullmatch(r"PMC\d+", doc_id or ""):
        raise ValueError("BioC document has no valid PMCID")
    doc_license = document.get("infons", {}).get("license", "")
    license_text = " ".join(p.get("infons", {}).get("license", "")
                             for p in document.get("passages", []))
    # PMC BioC normalizes the document-level license to "CC BY" and may omit
    # its version from passage infons. The source registry is separately
    # restricted to CC BY 4.0 and the article-specific publisher license must
    # be verified before a source is registered.
    explicit_cc_by_4 = explicitly_cc_by_4(license_text)
    if doc_license != "CC BY" or not explicit_cc_by_4:
        raise ValueError("BioC payload does not identify the registered CC BY license")
    blocks = []
    for passage in document.get("passages", []):
        infons = passage.get("infons", {})
        kind = infons.get("type", "")
        section_type = infons.get("section_type", "")
        value = clean(passage.get("text", ""))
        if not value or section_type in {"REF", "FIG", "TABLE", "AUTH_CONT"}:
            continue
        if kind == "title_1":
            blocks.append(("h2", value))
        elif kind in {"title", "front"}:
            continue
        elif kind == "abstract":
            blocks.append(("h2", "Abstract"))
            blocks.append(("p", value))
        elif kind == "paragraph" and len(value) <= 100 and not re.search(r"[.!?;:]$", value):
            # Some BioC exports label article subheadings as short paragraph passages.
            blocks.append(("h3", value))
        elif kind == "paragraph":
            blocks.append(("p", value))
    return blocks, doc_id


def extract_nci_glossary_blocks(raw, expected_term_id=None, expected_term_name=None,
                                expected_audience="Patient"):
    """Extract the definition text from a single official NCI glossary API record."""
    record = json.loads(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw)
    definition = record.get("definition") if isinstance(record, dict) else None
    if (not isinstance(record, dict)
            or not isinstance(record.get("dictionary"), str)
            or record["dictionary"].casefold() != "cancer.gov"
            or record.get("language") != "en"
            or record.get("audience") != expected_audience
            or not record.get("termId") or not isinstance(record.get("termName"), str)
            or not record["termName"].strip()
            or (expected_term_id is not None and record.get("termId") != expected_term_id)
            or (expected_term_name is not None
                and record.get("termName", "").casefold() != expected_term_name.casefold())
            or not isinstance(definition, dict)
            or not isinstance(definition.get("text"), str)
            or not definition["text"].strip()):
        raise ValueError("NCI glossary payload is missing expected term metadata")
    blocks = [("h2", record["termName"])]
    blocks.append(("p", definition["text"].strip()))
    return blocks, record["termId"]


def extract_jats_blocks(raw):
    """Extract text-only JATS sections after identity/license checks.

    Europe PMC serves a bare ``article`` root, while NCBI EFetch wraps its
    JATS payload in ``pmc-articleset``. Accept either representation, but
    reject wrappers containing zero or multiple articles to avoid silently
    mixing records.
    """
    root = ET.fromstring(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    root_kind = root.tag.rsplit("}", 1)[-1]
    if root_kind == "pmc-articleset":
        articles = [node for node in root if node.tag.rsplit("}", 1)[-1] == "article"]
        if len(articles) != 1:
            raise ValueError("Expected exactly one JATS article in PMC article set")
        root = articles[0]
    elif root_kind != "article":
        raise ValueError("Expected a JATS article")
    ids = {node.attrib.get("pub-id-type"): (node.text or "").strip()
           for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "article-id"}
    pmcid, doi = ids.get("pmcid", ""), ids.get("doi", "")
    license_nodes = [node for node in root.iter()
                     if node.tag.rsplit("}", 1)[-1] in {"license", "license-p"}]
    license_text = " ".join(" ".join("".join(node.itertext()).split())
                            for node in license_nodes)
    license_urls = [value for node in license_nodes for key, value in node.attrib.items()
                    if key.rsplit("}", 1)[-1] in {"href", "url"}]
    license_urls.extend(re.findall(r"https?://creativecommons\.org/licenses/by/4\.0/?",
                                   license_text, flags=re.IGNORECASE))
    explicit_cc_by_4 = explicitly_cc_by_4(license_text, license_urls)
    if not re.fullmatch(r"PMC\d+", pmcid) or not doi:
        raise ValueError("JATS article is missing PMCID or DOI")
    if not explicit_cc_by_4:
        raise ValueError("JATS article does not explicitly identify CC BY 4.0")

    blocks = []
    meta = next((node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "article-meta"), None)
    body = next((node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "body"), None)
    if meta is not None:
        for abstract in (node for node in meta if node.tag.rsplit("}", 1)[-1] == "abstract"):
            blocks.append(("h2", "Abstract"))
            for para in abstract:
                if para.tag.rsplit("}", 1)[-1] == "p":
                    value = clean(" ".join("".join(para.itertext()).split()))
                    if value:
                        blocks.append(("p", value))

    def walk_section(section, level=2):
        title = next((node for node in section if node.tag.rsplit("}", 1)[-1] == "title"), None)
        if title is not None:
            heading = clean(" ".join("".join(title.itertext()).split()))
            if heading:
                blocks.append(("h2" if level == 2 else "h3", heading))
        for child in section:
            kind = child.tag.rsplit("}", 1)[-1]
            if kind == "p":
                value = clean(" ".join("".join(child.itertext()).split()))
                if value:
                    blocks.append(("p", value))
            elif kind == "sec":
                walk_section(child, min(level + 1, 3))
            # Figures, references, footnotes, and tables are omitted.

    if body is not None:
        for section in body:
            if section.tag.rsplit("}", 1)[-1] == "sec":
                walk_section(section)
    return blocks, pmcid, doi


def chunks_for(source, blocks, source_sha, accessed_at, source_date):
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
            "publisher": source.get("publisher", "National Cancer Institute"), "url": source["url"],
            "authors": source["authors"], "source_date": source_date,
            "license": source.get("license", NCI_LICENSE),
            "license_url": source.get("license_url", NCI_LICENSE_URL),
            "scope": source.get("scope", ""),
            "section": section, "accessed_at": accessed_at,
            "source_sha256": source_sha,
            "text_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "text": content,
        })
        for key in ("doi", "pmcid"):
            if source.get(key):
                chunks[-1][key] = source[key]
        paragraphs.clear()

    for tag, value in blocks:
        if tag.startswith("h"):
            flush()
            section = value
            if value.casefold() in EXCLUDE_SECTIONS or value.casefold().startswith("downloads"):
                excluded = True
            else:
                excluded = False
            continue
        if excluded:
            continue
        if value == "All published articles of this journal are available on ScienceDirect." \
                or value.startswith("E-Mail Address of Dr.") \
                or re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            continue
        if value.startswith("You can help speed up the development of new treatments"):
            continue
        minimum = 2 if tag in {'li', 'tr'} else 20
        if len(value) < minimum or value == (paragraphs[-1] if paragraphs else None):
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


def validate_source(source):
    parsed = urlparse(source["url"])
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Source URL host is not approved: {source['url']}")
    download_url = source.get("download_url")
    if download_url:
        download_parsed = urlparse(download_url)
        if download_parsed.scheme != "https" or download_parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError(f"Download URL host is not approved: {download_url}")
    if source.get("format", "html") == "bioc_json":
        expected = ("https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/"
                    f"BioC_json/{source.get('pmcid')}/unicode")
        if parsed.hostname != "pmc.ncbi.nlm.nih.gov" or download_url != expected:
            raise ValueError(f"BioC source URLs do not match the registered PMCID: {source['id']}")
    elif source.get("format") == "jats_xml":
        expected = ("https://www.ebi.ac.uk/europepmc/webservices/rest/"
                    f"{source.get('pmcid')}/fullTextXML")
        if parsed.hostname != "pmc.ncbi.nlm.nih.gov" or download_url != expected:
            raise ValueError(f"JATS source URLs do not match the registered PMCID: {source['id']}")
    elif source.get("format") == "nci_glossary_json":
        if (parsed.hostname != "www.cancer.gov" or not download_url
                or urlparse(download_url).hostname != "webapis.cancer.gov"
                or not source.get("nci_term_id")):
            raise ValueError(f"NCI glossary source URLs or term ID are invalid: {source['id']}")
    elif source.get("format", "html") != "html":
        raise ValueError(f"Unsupported source format: {source['format']}")
    if parsed.hostname == "www.cancer.gov":
        if (source.get("license") != NCI_LICENSE
                or source.get("license_url") != NCI_LICENSE_URL):
            raise ValueError(f"Unexpected NCI reuse declaration: {source['id']}")
    elif source.get("license") != "CC BY 4.0" or source.get("license_url") != CC_BY_4:
        raise ValueError(f"Non-NCI sources must explicitly declare CC BY 4.0: {source['id']}")
    if parsed.hostname != "www.cancer.gov" and not source.get("scope"):
        raise ValueError(f"Non-NCI source must declare its evidence scope: {source['id']}")


def download(source):
    validate_source(source)
    if source.get("format") in {"bioc_json", "jats_xml", "nci_glossary_json"} and os.name == "nt" and shutil.which("curl.exe"):
        with tempfile.TemporaryDirectory(prefix="bonescope-source-") as temp_dir:
            extension = ".xml" if source.get("format") == "jats_xml" else ".json"
            output_path = Path(temp_dir) / f"source{extension}"
            subprocess.run(["curl.exe", "--fail", "--location", "--silent", "--show-error",
                            "--output", str(output_path), source["download_url"]],
                           check=True, capture_output=True, timeout=30)
            data = output_path.read_bytes()
        if len(data) > 5_000_000:
            raise ValueError(f"Source exceeds 5 MB: {source['id']}")
        if source.get("format") == "bioc_json":
            extract_bioc_blocks(data)
        elif source.get("format") == "nci_glossary_json":
            blocks, term_id = extract_nci_glossary_blocks(
                data, expected_term_id=source["nci_term_id"],
                expected_term_name=source.get("nci_term_name"))
            if term_id != source["nci_term_id"]:
                raise ValueError(f"NCI glossary term ID mismatch: {source['id']}")
        else:
            pmcid, doi = extract_jats_blocks(data)[1:]
            if pmcid != source.get("pmcid") or doi != source.get("doi"):
                raise ValueError(f"Downloaded JATS identity mismatch: {source['id']}")
        return data
    request_url = source.get("download_url", source["url"])
    request = Request(request_url, headers={"User-Agent": "BoneScope-research-corpus/1.0"})
    with urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        expected_type = "application/json" if source.get("format") in {"bioc_json", "nci_glossary_json"} else (
            "xml" if source.get("format") == "jats_xml" else "text/html")
        if expected_type not in content_type:
            raise ValueError(f"Unexpected source content type: {source['id']}")
        data = response.read(5_000_001)
    if len(data) > 5_000_000:
        raise ValueError(f"Source exceeds 5 MB: {source['id']}")
    if source.get("format") == "jats_xml":
        pmcid, doi = extract_jats_blocks(data)[1:]
        if pmcid != source.get("pmcid") or doi != source.get("doi"):
            raise ValueError(f"Downloaded JATS identity mismatch: {source['id']}")
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
        # Validate registry rights and source endpoints for online and offline builds.
        validate_source(source)
        source = {**source, "authors": source.get("authors", (
            "PDQ Pediatric Treatment Editorial Board" if "-pdq" in source["url"]
            else "National Cancer Institute")),
            "publisher": source.get("publisher", "National Cancer Institute"),
            "license": source.get("license", NCI_LICENSE),
            "license_url": source.get("license_url", NCI_LICENSE_URL)}
        suffix = {"bioc_json": ".json", "jats_xml": ".xml", "nci_glossary_json": ".json"}.get(source.get("format"), ".html")
        cache_path = CACHE / f"{source['id']}{suffix}"
        if offline:
            data = cache_path.read_bytes()
            accessed_at = datetime.fromtimestamp(cache_path.stat().st_mtime, timezone.utc).isoformat()
        else:
            data = download(source)
            cache_path.write_bytes(data)
            accessed_at = datetime.now(timezone.utc).isoformat()
        source_sha = hashlib.sha256(data).hexdigest()
        if source.get("format") == "bioc_json":
            blocks, pmcid = extract_bioc_blocks(data)
            if pmcid != source["pmcid"]:
                raise ValueError(f"BioC PMCID mismatch for {source['id']}")
            source_date = source.get("source_date")
        elif source.get("format") == "jats_xml":
            blocks, pmcid, doi = extract_jats_blocks(data)
            if pmcid != source["pmcid"] or doi != source["doi"]:
                raise ValueError(f"JATS article identity mismatch for {source['id']}")
            source_date = source.get("source_date")
        elif source.get("format") == "nci_glossary_json":
            blocks, term_id = extract_nci_glossary_blocks(
                data, expected_term_id=source["nci_term_id"],
                expected_term_name=source.get("nci_term_name"))
            if term_id != source["nci_term_id"]:
                raise ValueError(f"NCI glossary term ID mismatch for {source['id']}")
            source_date = source.get("source_date")
        else:
            html = data.decode("utf-8", errors="replace")
            dates = re.findall(r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})', html)
            source_date = dates[-1] if dates else source.get("source_date")
            blocks = extract_blocks(html)
        chunks = chunks_for(source, blocks, source_sha, accessed_at, source_date)
        if not chunks:
            raise ValueError(f"No text extracted from {source['id']}")
        all_chunks.extend(chunks)
        lock.append({**source,
                     "accessed_at": accessed_at, "source_date": source_date,
                     "source_sha256": source_sha,
                     "chunk_count": len(chunks)})
        print(f"{source['id']}: {len(chunks)} chunks")
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in all_chunks), encoding="utf-8")
    LOCK.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Built {len(all_chunks)} chunks from {len(lock)} sources")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Rebuild from cached HTML/BioC/JATS source files")
    build(parser.parse_args().offline)
