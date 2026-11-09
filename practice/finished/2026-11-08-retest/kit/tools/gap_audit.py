#!/usr/bin/env python3
"""Evidence-first migration audit. Python 3.10+, standard library only."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET


VERSION = "1.0.0"
THRESHOLDS = {"textSimilarity": 0.90, "headingCoverage": 0.90, "linkTextCoverage": 0.95}
SECTIONS = [
    "Executive summary", "Scope and method", "What is working",
    "Critical functional gaps", "High-risk content gaps", "Visual gaps",
    "SEO gaps", "Accessibility gaps", "Broken-document concentration",
    "Page-by-page matrix", "Recommended remediation order", "Conclusion",
]
MAX_BYTES = 10 * 1024 * 1024


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def digest(value):
    if not isinstance(value, bytes):
        value = json_text(value).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    Path(path).write_text(json_text(value), encoding="utf-8")


def normalized(value):
    return " ".join(value.split())


def url_key(url):
    """Drop fragments only; preserve path case, slash and query semantics."""
    parts = urlsplit(urldefrag(url)[0])
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username or parts.password:
        raise ValueError(f"Expected an HTTP(S) URL without credentials: {url}")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def origin(url):
    parts = urlsplit(url_key(url))
    return f"{parts.scheme}://{parts.netloc}"


def words(text):
    return [word for word in re.findall(r"\w+", text.casefold()) if len(word) > 2]


def similarity(left, right):
    a, b = Counter(words(left)), Counter(words(right))
    if not a or not b:
        return None
    return round(sum(n * b[k] for k, n in a.items()) / math.sqrt(
        sum(n * n for n in a.values()) * sum(n * n for n in b.values())), 6)


def coverage(source, target):
    a = {normalized(x).casefold() for x in source if normalized(x)}
    b = {normalized(x).casefold() for x in target if normalized(x)}
    return round(len(a & b) / len(a), 6) if a else None


class PageParser(HTMLParser):
    """Static HTML extraction, deliberately not a rendered-DOM approximation."""

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, url):
        super().__init__(convert_charrefs=True)
        self.url = url
        self.stack = []
        self.title = []
        self.description = ""
        self.canonical = ""
        self.lang = ""
        self.has_main = False
        self.texts = []
        self.headings = []
        self.links = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang") or ""
        if tag == "meta" and (attrs.get("name") or "").lower() == "description":
            self.description = attrs.get("content") or ""
        if tag == "link" and "canonical" in (attrs.get("rel") or "").lower().split():
            self.canonical = urljoin(self.url, attrs.get("href") or "") if attrs.get("href") else ""
        if tag == "base" and attrs.get("href"):
            self.url = urljoin(self.url, attrs["href"])
        if tag == "main":
            self.has_main = True
        in_main = tag == "main" or any(item["tag"] == "main" for item in self.stack)
        item = {"tag": tag, "text": [], "inMain": in_main}
        if re.fullmatch(r"h[1-6]", tag):
            item["level"] = int(tag[1])
            self.headings.append(item)
        if tag == "a" and attrs.get("href"):
            item["url"] = urljoin(self.url, attrs["href"])
            self.links.append(item)
        if tag == "img":
            self.images.append({"alt": attrs.get("alt"), "inMain": in_main})
        if tag not in self.VOID:
            self.stack.append(item)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        tags = {item["tag"] for item in self.stack}
        if tags & {"script", "style", "noscript", "template"}:
            return
        if "title" in tags:
            self.title.append(data)
        if not tags & {"head", "title"}:
            self.texts.append(("main" in tags, data))
        for item in self.stack:
            if item["tag"] == "a" or re.fullmatch(r"h[1-6]", item["tag"]):
                item["text"].append(data)

    def summary(self):
        headings = [h for h in self.headings if h["inMain"] or not self.has_main]
        images = [i for i in self.images if i["inMain"] or not self.has_main]
        links = []
        for link in self.links:
            if link["inMain"] or not self.has_main:
                try:
                    links.append({"url": url_key(link["url"]), "text": normalized(" ".join(link["text"]))})
                except ValueError:
                    pass  # mailto/tel/javascript are not network targets.
        return {
            "title": normalized(" ".join(self.title)), "description": self.description,
            "canonical": self.canonical, "lang": self.lang, "hasMain": self.has_main,
            "mainText": normalized(" ".join(t for inside, t in self.texts if inside or not self.has_main)),
            "h1s": [normalized(" ".join(h["text"])) for h in headings
                    if h["level"] == 1 and normalized(" ".join(h["text"]))],
            "headings": [normalized(" ".join(h["text"])) for h in headings],
            "headingJumps": sum(b["level"] > a["level"] + 1 for a, b in zip(headings, headings[1:])),
            "links": links, "imageCount": len(images),
            "missingAltCount": sum(i["alt"] is None for i in images),
            "emptyAltCount": sum(i["alt"] == "" for i in images),
        }


class ScopedRedirect(HTTPRedirectHandler):
    def __init__(self, allowed, chain):
        self.allowed, self.chain = allowed, chain

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.chain.append({"url": req.full_url, "status": code, "location": newurl})
        if origin(newurl) not in self.allowed:
            raise ValueError(f"Redirect outside configured origins: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    def __init__(self, allowed, timeout=20, delay=0.2):
        self.allowed, self.timeout, self.delay = set(allowed), timeout, delay

    def __call__(self, url, body=True):
        url = url_key(url)
        if origin(url) not in self.allowed:
            raise ValueError(f"URL outside configured origins: {url}")
        chain = []
        result = {"url": url, "finalUrl": url, "status": 0, "redirects": chain,
                  "checkedAt": datetime.now(timezone.utc).isoformat(), "error": "", "contentType": ""}
        raw = b""
        try:
            opener = build_opener(ScopedRedirect(self.allowed, chain))
            request = Request(url, headers={"User-Agent": f"MigrationGapAudit/{VERSION}", "Accept-Encoding": "identity"})
            try:
                response = opener.open(request, timeout=self.timeout)
            except HTTPError as error:
                response = error
            with response:
                result.update(status=response.code, finalUrl=response.url,
                              contentType=response.headers.get("Content-Type", ""))
                if body:
                    raw = response.read(MAX_BYTES + 1)
                    if len(raw) > MAX_BYTES:
                        raise ValueError("Response exceeds 10 MiB collection limit")
        except (URLError, OSError, ValueError) as error:
            result["error"] = str(error)
            raw = b""
        finally:
            time.sleep(self.delay)
        return result, raw


def usable(page):
    return 200 <= page["status"] < 300 and not page.get("error") and bool(page.get("html"))


def link_state(check):
    if check.get("error") or check["status"] == 0:
        return "unverified"
    if check["status"] in (404, 410):
        return "unavailable"
    if 200 <= check["status"] < 300:
        return "available"
    return "unverified"


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("name", "sourceOrigin", "targetOrigin", "inventories"):
        if not config.get(key):
            raise ValueError(f"Configuration requires {key}")
    for key in ("sourceOrigin", "targetOrigin"):
        if url_key(config[key]) != origin(config[key]) + "/":
            raise ValueError(f"{key} must be an origin without a path/query")
        config[key] = origin(config[key])
    config.setdefault("includePrefixes", ["/"])
    config.setdefault("excludePrefixes", [])
    config.setdefault("routeMap", {})
    config.setdefault("documentPrefixes", ["/docs/"])
    config.setdefault("maxPages", 1000)
    config.setdefault("maxLinks", 10000)
    config.setdefault("maxSitemaps", 100)
    config.setdefault("timeoutSeconds", 20)
    config.setdefault("requestDelaySeconds", 0.2)
    for key in ("maxPages", "maxLinks", "maxSitemaps", "timeoutSeconds"):
        if not isinstance(config[key], int) or config[key] < 1:
            raise ValueError(f"{key} must be a positive integer")
    if not isinstance(config["requestDelaySeconds"], (float, int)) or config["requestDelaySeconds"] < 0:
        raise ValueError("requestDelaySeconds must be nonnegative")
    return config


def read_inventory(config, base_dir, fetch, out):
    candidates, records, visited = [], [], set()

    def read(location, kind):
        remote = location.startswith(("http://", "https://"))
        key = url_key(location) if remote else str(Path(location).resolve())
        if key in visited:
            return
        if len(visited) >= config["maxSitemaps"]:
            raise ValueError("Inventory file limit reached; adjust maxSitemaps explicitly")
        visited.add(key)
        if remote:
            if origin(key) != config["sourceOrigin"]:
                raise ValueError("Remote inventories must use sourceOrigin")
            response, raw = fetch(key)
            if response["error"] or not 200 <= response["status"] < 300:
                raise ValueError(f"Inventory unavailable: {key}: {response}")
        else:
            with Path(key).open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("Inventory exceeds 10 MiB limit")
        snapshot = f"snapshots/{digest(raw)}.inventory"
        (out / snapshot).write_bytes(raw)
        records.append({"location": key, "kind": kind, "sha256": digest(raw), "snapshot": snapshot})
        if raw.startswith(b"\x1f\x8b"):
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("Expanded sitemap exceeds 10 MiB limit")
        if kind == "urls":
            candidates.extend(line.strip() for line in raw.decode("utf-8-sig").splitlines()
                              if line.strip() and not line.lstrip().startswith("#"))
            return
        if kind != "sitemap":
            raise ValueError(f"Unknown inventory kind: {kind}")
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ValueError("Sitemaps with DTDs/entities are not supported")
        root = ET.fromstring(raw)
        tag = root.tag.rsplit("}", 1)[-1]
        if tag not in ("urlset", "sitemapindex"):
            raise ValueError(f"Expected urlset or sitemapindex, found {tag}")
        entry_name = "url" if tag == "urlset" else "sitemap"
        locations = []
        for entry in root:
            if entry.tag.rsplit("}", 1)[-1] != entry_name:
                continue
            loc = next((child.text for child in entry if child.tag.rsplit("}", 1)[-1] == "loc"), None)
            if not loc or not loc.strip():
                raise ValueError(f"Missing loc in {key}")
            locations.append(loc.strip())
        if tag == "urlset":
            candidates.extend(locations)
        else:
            for child in sorted(locations):
                resolved = urljoin(key, child) if remote else str(Path(key).parent / child)
                if child.startswith(("http://", "https://")):
                    resolved = child
                read(resolved, "sitemap")

    for item in config["inventories"]:
        location = item["location"]
        if not location.startswith(("http://", "https://")):
            location = str(base_dir / location)
        read(location, item["kind"])
    urls, excluded = set(), []
    for value in sorted(set(candidates)):
        url = url_key(value)
        path = urlsplit(url).path
        reason = ""
        if origin(url) != config["sourceOrigin"]:
            reason = "different origin"
        elif not any(path.startswith(p) for p in config["includePrefixes"]):
            reason = "outside included prefixes"
        elif any(path.startswith(p) for p in config["excludePrefixes"]):
            reason = "excluded prefix"
        if reason:
            excluded.append({"url": url, "reason": reason})
        else:
            urls.add(url)
    if not urls:
        raise ValueError("Inventory contains zero in-scope URLs; no audit was produced")
    if len(urls) > config["maxPages"]:
        raise ValueError("Page limit exceeded; narrow scope or increase maxPages explicitly")
    return sorted(urls), {"inputs": records, "excluded": excluded, "candidateCount": len(set(candidates))}


def collect(config_path, output):
    config_path, out = Path(config_path).resolve(), Path(output)
    config = load_config(config_path)
    out.mkdir(parents=True, exist_ok=False)
    (out / "snapshots").mkdir()
    fetch = Fetcher([config["sourceOrigin"], config["targetOrigin"]],
                    config["timeoutSeconds"], config["requestDelaySeconds"])
    urls, inventory = read_inventory(config, config_path.parent, fetch, out)
    pages, checks = [], {}

    def page(url):
        response, raw = fetch(url)
        if raw:
            snapshot = f"snapshots/{digest(raw)}.body"
            (out / snapshot).write_bytes(raw)
            response.update(snapshot=snapshot, sha256=digest(raw))
        response["html"] = {}
        if raw and ("text/html" in response["contentType"].lower()
                    or "application/xhtml+xml" in response["contentType"].lower()):
            charset = re.search(r"charset=[\"']?([\w-]+)", response["contentType"], re.I)
            encoding = charset[1] if charset else "utf-8"
            try:
                decoded = raw.decode(encoding, errors="replace")
            except LookupError:
                decoded = raw.decode("utf-8", errors="replace")
            parser = PageParser(response["finalUrl"])
            parser.feed(decoded)
            response["html"] = parser.summary()
        return response

    for i, source_url in enumerate(urls, 1):
        parts = urlsplit(source_url)
        route = parts.path + ("?" + parts.query if parts.query else "")
        mapped = config["routeMap"].get(route, route)
        target_url = url_key(urljoin(config["targetOrigin"] + "/", mapped))
        if origin(target_url) != config["targetOrigin"]:
            raise ValueError(f"Mapping leaves targetOrigin: {route}")
        source, target = page(source_url), page(target_url)
        pages.append({"id": "PAGE-" + hashlib.sha256(source_url.encode()).hexdigest()[:12],
                      "route": route, "source": source, "target": target})
        checks[target_url] = {k: v for k, v in target.items() if k != "html"}
        print(f"Collected {i}/{len(urls)}: {route}", file=sys.stderr)

    links = sorted({link["url"] for p in pages if usable(p["target"])
                    for link in p["target"]["html"]["links"]
                    if origin(link["url"]) == config["targetOrigin"]})
    if len(links) > config["maxLinks"]:
        raise ValueError("Link limit exceeded; increase maxLinks explicitly")
    for i, url in enumerate(links, 1):
        print(f"Checking destination {i}/{len(links)}: {url}", file=sys.stderr)
        if url not in checks:
            checks[url], _ = fetch(url, body=False)
    evidence = {"schemaVersion": 1, "methodVersion": VERSION,
                "generatedAt": datetime.now(timezone.utc).isoformat(), "config": config,
                "configHash": digest(config), "inventory": inventory, "pages": pages,
                "linkChecks": [checks[url] for url in links]}
    write_json(out / "evidence.json", evidence)
    render(out / "evidence.json", out)


def validate_evidence(evidence):
    if evidence.get("schemaVersion") != 1 or evidence.get("methodVersion") != VERSION:
        raise ValueError("Unsupported evidence schema/method version; use the matching script version")
    if digest(evidence["config"]) != evidence["configHash"]:
        raise ValueError("Evidence configuration hash does not match")
    pages = evidence["pages"]
    if not pages or len({p["id"] for p in pages}) != len(pages):
        raise ValueError("Evidence must contain pages with unique IDs")
    if len({p["source"]["url"] for p in pages}) != len(pages):
        raise ValueError("Duplicate source URL in evidence")
    for page in pages:
        for side in ("source", "target"):
            p = page[side]
            if type(p["status"]) is not int or not (p["status"] == 0 or 100 <= p["status"] <= 599):
                raise ValueError("Invalid HTTP status")
            for key in ("url", "finalUrl", "contentType", "error", "html"):
                if key not in p:
                    raise ValueError(f"Page response requires {key}")
            expected = evidence["config"]["sourceOrigin" if side == "source" else "targetOrigin"]
            if origin(p["url"]) != expected:
                raise ValueError(f"{side} page URL is outside configured origin")
            if p["html"]:
                for key in ("title", "description", "canonical", "lang", "hasMain", "mainText",
                            "h1s", "headings", "headingJumps", "links", "imageCount", "missingAltCount", "emptyAltCount"):
                    if key not in p["html"]:
                        raise ValueError(f"HTML evidence requires {key}")
    checks = evidence["linkChecks"]
    for check in checks:
        if type(check["status"]) is not int or not (check["status"] == 0 or 100 <= check["status"] <= 599):
            raise ValueError("Invalid link HTTP status")
    if len({c["url"] for c in checks}) != len(checks):
        raise ValueError("Duplicate link checks")
    check_urls = {c["url"] for c in checks}
    required = {link["url"] for p in pages if usable(p["target"])
                for link in p["target"]["html"]["links"]
                if origin(link["url"]) == evidence["config"]["targetOrigin"]}
    if required != check_urls:
        raise ValueError("Link checks must exactly cover unique internal links from usable target pages")


def validate_reviews(reviews, evidence):
    if reviews.get("evidenceSha256") != digest(evidence):
        raise ValueError("Reviews must reference this evidenceSha256; stale review decisions cannot be reused")
    ids = {p["id"] for p in evidence["pages"]}
    seen = set()
    for review in reviews.get("findings", []):
        for key in ("id", "category", "title", "priority", "disposition", "pageIds", "observation",
                    "impact", "recommendation", "acceptance", "owner", "evidence", "reviewer", "reviewedAt"):
            if not review.get(key):
                raise ValueError(f"Reviewed finding requires nonempty {key}")
        if review["id"] in seen:
            raise ValueError("Duplicate reviewed finding ID")
        seen.add(review["id"])
        if review["category"] not in ("functional", "content", "visual", "seo", "accessibility"):
            raise ValueError("Unknown finding category")
        if review["priority"] not in ("P0", "P1", "P2") or review["disposition"] not in ("confirmed", "accepted", "needs-review"):
            raise ValueError("Invalid reviewed priority/disposition")
        fidelity = review.get("contentFidelity")
        if fidelity not in (None, "Review", "Critical"):
            raise ValueError("contentFidelity must be null, Review or Critical")
        if fidelity and (review["disposition"] != "confirmed" or review["category"] not in ("content", "functional")):
            raise ValueError("Content-fidelity overrides require a confirmed content/functional finding")
        if fidelity == "Critical" and review["priority"] != "P0":
            raise ValueError("Critical content fidelity requires confirmed P0 impact")
        if not isinstance(review["pageIds"], list) or not set(review["pageIds"]) <= ids:
            raise ValueError("Review refers to unknown page IDs")
        if not isinstance(review["evidence"], list) or not all(isinstance(x, str) and x.strip() for x in review["evidence"]):
            raise ValueError("Review evidence must be a list of references")
    return sorted(reviews.get("findings", []), key=lambda r: (r["priority"], r["id"]))


def analyze(evidence, reviews):
    validate_evidence(evidence)
    findings = validate_reviews(reviews, evidence) if reviews else []
    checks = {c["url"]: c for c in evidence["linkChecks"]}
    rows = []
    for page in sorted(evidence["pages"], key=lambda p: (p["route"], p["id"])):
        source, target = page["source"], page["target"]
        a, b = source["html"], target["html"]
        metrics, flags = {}, []
        if usable(source) and usable(target):
            metrics = {"textSimilarity": similarity(a["mainText"], b["mainText"]),
                       "headingCoverage": coverage(a["headings"], b["headings"]),
                       "linkTextCoverage": coverage([x["text"] for x in a["links"]], [x["text"] for x in b["links"]])}
            if any(value is not None and value < THRESHOLDS[key] for key, value in metrics.items()):
                flags.append("Content/structure difference")
            if metrics["textSimilarity"] is None:
                flags.append("Insufficient text for comparison")
            if not b["h1s"]:
                flags.append("Missing H1: regression" if a["h1s"] else "Missing H1: inherited")
            if a["title"] != b["title"] or not b["title"]:
                flags.append("Title missing/different")
            if not a["hasMain"] or not b["hasMain"]:
                flags.append("Main region missing; full-document fallback")
            for side, response in (("Source", source), ("Target", target)):
                if response.get("redirects") or url_key(response["finalUrl"]) != url_key(response["url"]):
                    flags.append(f"{side} redirect requires review")
            content_flags = list(flags)
            content = "Review" if content_flags else "Good"
        else:
            content = "Unverified"
            flags.append("Source or target HTML unavailable; inspect response evidence")
        if usable(target):
            if not b["lang"]:
                flags.append("Document language missing")
            if not b["description"]:
                flags.append("Meta description missing")
            if not b["canonical"]:
                flags.append("Canonical missing")
            if b["headingJumps"]:
                flags.append(f"{b['headingJumps']} heading jumps")
            if b["missingAltCount"]:
                flags.append(f"{b['missingAltCount']} images missing alt")
            if b["emptyAltCount"]:
                flags.append(f"{b['emptyAltCount']} empty-alt images to review")
        urls = {x["url"] for x in b.get("links", [])} if usable(target) else set()
        broken = sorted(u for u in urls if u in checks and link_state(checks[u]) == "unavailable")
        unknown = sorted(u for u in urls if u in checks and link_state(checks[u]) == "unverified")
        for review in findings:
            if page["id"] in review["pageIds"]:
                flags.append(f"{review['id']}: {review['title']} ({review['disposition']})")
                if review.get("contentFidelity") == "Critical":
                    content = "Critical"
                elif review.get("contentFidelity") == "Review" and content == "Good":
                    content = "Review"
        rows.append({"id": page["id"], "route": page["route"], "content": content,
                     "sourceStatus": source["status"], "targetStatus": target["status"],
                     "metrics": metrics, "brokenLinks": broken, "unverifiedLinks": unknown, "flags": flags})
    targets = [p["target"]["html"] for p in evidence["pages"] if usable(p["target"])]
    pairs = [p for p in evidence["pages"] if usable(p["source"]) and usable(p["target"])]
    scores = [r["metrics"]["textSimilarity"] for r in rows if r["metrics"].get("textSimilarity") is not None]
    broken = [u for u, c in checks.items() if link_state(c) == "unavailable"]
    prefixes = evidence["config"].get("documentPrefixes", ["/docs/"])
    documents = [u for u in broken if any(urlsplit(u).path.startswith(p) for p in prefixes)
                 or re.search(r"\.(pdf|docx?|xlsx?|pptx?|zip)$", urlsplit(u).path, re.I)]
    summary = {"pages": len(rows), "usableTargetPages": len(targets), "comparablePages": len(pairs),
               "matchingTitles": sum(bool(p["source"]["html"]["title"]) and p["source"]["html"]["title"] == p["target"]["html"]["title"] for p in pairs),
               "descriptionsPresent": sum(bool(p["description"]) for p in targets),
               "canonicalsPresent": sum(bool(p["canonical"]) for p in targets),
               "missingLanguage": sum(not p["lang"] for p in targets),
               "missingH1": sum(not p["h1s"] for p in targets),
               "headingJumpPages": sum(p["headingJumps"] > 0 for p in targets),
               "missingAltImages": sum(p["missingAltCount"] for p in targets),
               "emptyAltImages": sum(p["emptyAltCount"] for p in targets),
               "uniqueLinksChecked": len(checks), "unavailableLinks": len(broken),
               "unavailableDocuments": len(documents),
               "unverifiedLinks": sum(link_state(c) == "unverified" for c in checks.values()),
               "affectedPages": sum(bool(r["brokenLinks"]) for r in rows),
               "meanTextSimilarity": round(sum(scores) / len(scores), 6) if scores else None,
               "textSampleSize": len(scores), "confirmedFindings": sum(f["disposition"] == "confirmed" for f in findings)}
    return {"schemaVersion": 1, "methodVersion": VERSION, "evidenceSha256": digest(evidence),
            "reviewsSha256": digest(reviews) if reviews else None, "thresholds": THRESHOLDS,
            "summary": summary, "rows": rows, "findings": findings}


def cell(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("\n", " ")


def percent(value):
    return f"{value * 100:.1f}%" if value is not None else "Not measurable"


def report(evidence, result):
    s, config = result["summary"], evidence["config"]
    lines = [f"# {cell(config['name'])} — Migration Gap Audit", "",
             f"Evidence collected: {evidence['generatedAt']}", "",
             f"Source: {config['sourceOrigin']}  ", f"Target: {config['targetOrigin']}", "",
             f"Method: {VERSION} · Evidence SHA-256: `{result['evidenceSha256']}`", ""]
    if evidence.get("synthetic"):
        lines += ["**SYNTHETIC EXAMPLE — demonstrates the format; these are not live site findings.**", ""]
    sections = {name: [] for name in SECTIONS}
    sections["Executive summary"] = [
        f"{s['usableTargetPages']}/{s['pages']} target routes returned usable static HTML. "
        f"{s['comparablePages']}/{s['pages']} source/target pairs could be compared.",
        f"{s['unavailableLinks']}/{s['uniqueLinksChecked']} unique internal targets returned 404/410, "
        f"with document targets accounting for {s['unavailableDocuments']}. Unverified targets: {s['unverifiedLinks']}. "
        f"{s['affectedPages']}/{s['pages']} pages link to an unavailable target.",
        f"{s['confirmedFindings']} findings have a recorded reviewer confirmation. "
        "This report does not certify launch readiness; browser and functional review must be recorded separately.",
    ]
    sections["Scope and method"] = [
        f"Inventory: {s['pages']} unique source URLs; {len(evidence['inventory']['excluded'])} inventory entries excluded. "
        "Only routes in this inventory are assessed; sitemap completeness is not assumed.",
        "Static HTTP GET collection, exact route mapping, main-content extraction, text/heading/link-label comparison, "
        "and unique internal target checks. Fragments are removed; queries, path case and trailing slashes are retained. "
        "Linked files are checked for HTTP availability, not file integrity or content parity.",
        "404/410 = unavailable at collection time. Timeouts, blocked requests, rate limits and other non-2xx responses "
        "= unverified. HTTP 200 may still be a soft error or login page.",
        "Text similarity uses token-frequency cosine similarity. Heading and link-label coverage compare distinct normalized labels. "
        "Signals below 90%, 90% and 95% respectively trigger review. Empty denominators are not treated as passes.",
        "Static HTML does not execute JavaScript or establish visual, interaction, keyboard, contrast or accessibility conformance. "
        "CSS-hidden content may be included. Canonical presence does not establish canonical correctness.",
        "Good = no automated content flags; Review = content/structure signal; Critical = reviewer-confirmed P0 content/functional gap; "
        "Unverified = comparison unavailable. Resource failures and shared experience defects are independent of content fidelity.",
        "Evidence: `evidence.json` and `analysis.json`; capture paths are recorded in the evidence file when present. "
        "Identical evidence, reviews and method version produce byte-identical report content.",
    ]
    sections["What is working"] = [
        f"- Matching nonempty titles: {s['matchingTitles']}/{s['comparablePages']} comparable pairs.\n"
        f"- Descriptions present: {s['descriptionsPresent']}/{s['usableTargetPages']} usable target pages.\n"
        f"- Canonicals present: {s['canonicalsPresent']}/{s['usableTargetPages']} usable target pages.\n"
        f"- Mean text similarity: {percent(s['meanTextSimilarity'])} across {s['textSampleSize']} measurable pairs. "
        "These checks are limited to static HTML.",
    ]
    category_sections = {"functional": "Critical functional gaps", "content": "High-risk content gaps",
                         "visual": "Visual gaps", "seo": "SEO gaps", "accessibility": "Accessibility gaps"}
    for category, section in category_sections.items():
        entries = [f for f in result["findings"] if f["category"] == category]
        sections[section] = [
            f"### {cell(f['id'])} — {cell(f['title'])}\n\n"
            f"{f['priority']} · {f['disposition']} · Owner: {cell(f['owner'])}\n\n"
            f"Observation: {cell(f['observation'])}\n\nImpact: {cell(f['impact'])}\n\n"
            f"Required: {cell(f['recommendation'])}\n\nAcceptance: {cell(f['acceptance'])}\n\n"
            f"Pages: {', '.join(f['pageIds'])}. Evidence: {cell('; '.join(f['evidence']))}. "
            f"Reviewed by {cell(f['reviewer'])}, {cell(f['reviewedAt'])}." for f in entries
        ] or ["No reviewed findings recorded. Review remains unverified; this is not a passing result."]
    sections["SEO gaps"].insert(0,
        f"Static signals: {s['usableTargetPages'] - s['descriptionsPresent']} missing descriptions; "
        f"{s['usableTargetPages'] - s['canonicalsPresent']} missing canonicals among {s['usableTargetPages']} usable target pages. "
        "Canonical correctness, production robots, sitemap coverage and search indexing require separate review.")
    sections["Accessibility gaps"].insert(0,
        f"Static signals across {s['usableTargetPages']} usable target pages — missing document language: {s['missingLanguage']}; "
        f"pages without H1: {s['missingH1']}; pages with heading jumps: {s['headingJumpPages']}; "
        f"images missing alt: {s['missingAltImages']}; images with empty alt: {s['emptyAltImages']}. "
        "Empty alt may be appropriate for decoration. These signals are review candidates, not a conformance verdict.")
    sections["Broken-document concentration"] = [
        f"Unique unavailable document targets: {s['unavailableDocuments']}; unavailable internal targets total: {s['unavailableLinks']}. "
        "Per-page counts below include documents and page links; the same target can appear on multiple pages. Do not sum rows to get unique totals.",
        "| Route | Unavailable internal targets | Unverified targets |\n|---|---:|---:|\n" + "\n".join(
            f"| {cell(r['route'])} | {len(r['brokenLinks'])} | {len(r['unverifiedLinks'])} |"
            for r in sorted(result["rows"], key=lambda r: (-len(r["brokenLinks"]), r["route"]))
            if r["brokenLinks"] or r["unverifiedLinks"]),
    ]
    sections["Page-by-page matrix"] = [
        "| ID / Route | Content fidelity | Source / target HTTP | Text similarity | Unavailable / unverified links | Main flags |\n"
        "|---|---|---|---:|---:|---|\n" + "\n".join(
            f"| {r['id']} / {cell(r['route'])} | {r['content']} | {r['sourceStatus']} / {r['targetStatus']} | "
            f"{percent(r['metrics'].get('textSimilarity'))} | {len(r['brokenLinks'])} / {len(r['unverifiedLinks'])} | "
            f"{cell('; '.join(r['flags']) or 'No automated flags; browser review still required')} |" for r in result["rows"]),
    ]
    sections["Recommended remediation order"] = [
        "Priority rubric: P0 blocks a required user journey or required resource at launch; "
        "P1 is a material quality issue with an available workaround; P2 is minor polish. "
        "A reviewer assigns priority using agreed launch criteria; similarity alone cannot establish P0.",
    ]
    for priority in ("P0", "P1", "P2"):
        entries = [f for f in result["findings"] if f["priority"] == priority and f["disposition"] == "confirmed"]
        sections["Recommended remediation order"].append(
            f"### {priority}\n\n" + ("\n".join(f"- {f['id']}: {cell(f['recommendation'])} Owner: {cell(f['owner'])}." for f in entries)
                                     or "No confirmed items recorded."))
    sections["Conclusion"] = [
        "This evidence establishes the observed route, metadata, content-signal and resource-availability results for the listed inventory. "
        "Resolve or accept confirmed findings, complete browser/journey review and obtain content-owner approval before a launch decision. "
        "Unverified observations remain open; content similarity and HTTP success do not prove functional equivalence.",
    ]
    for name in SECTIONS:
        lines += [f"## {name}", "", "\n\n".join(sections[name]), ""]
    return "\n".join(lines)


def render(evidence_path, output, reviews_path=None):
    evidence = json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    reviews = json.loads(Path(reviews_path).read_text(encoding="utf-8")) if reviews_path else None
    result = analyze(evidence, reviews)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "analysis.json", result)
    (out / "report.md").write_text(report(evidence, result), encoding="utf-8")
    if not reviews_path and not (out / "reviews.json").exists():
        write_json(out / "reviews.json", {"evidenceSha256": digest(evidence), "findings": []})
    print(f"Wrote {out / 'report.md'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    collect_parser = commands.add_parser("collect", help="Collect HTTP evidence and render a draft")
    collect_parser.add_argument("--config", required=True)
    collect_parser.add_argument("--out", required=True, help="New run directory; must not exist")
    render_parser = commands.add_parser("render", help="Rebuild a report offline from saved evidence")
    render_parser.add_argument("--evidence", required=True)
    render_parser.add_argument("--reviews")
    render_parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            collect(args.config, args.out)
        else:
            render(args.evidence, args.out, args.reviews)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        parser.exit(1, f"Audit failed: {error}\n")


if __name__ == "__main__":
    main()
