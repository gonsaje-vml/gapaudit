"""Offline regression checks for the decisions that can mislead audit readers."""

from copy import deepcopy
import gzip
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import gap_audit as audit


SOURCE = "https://source.example"
TARGET = "https://preview.example"


def response(url, body="", status=200, error=""):
    parser = audit.PageParser(url)
    parser.feed(body)
    return {"url": url, "finalUrl": url, "status": status, "contentType": "text/html",
            "error": error, "redirects": [], "html": parser.summary() if body else {}}


def html(content, lang=' lang="en"'):
    return f'<html{lang}><head><title>Provider resources</title><meta name="description" content="Resources"><link rel="canonical" href="/home"></head><body><main>{content}</main></body></html>'


def example_evidence():
    config = {"name": "Example provider migration", "sourceOrigin": SOURCE, "targetOrigin": TARGET,
              "documentPrefixes": ["/docs/"]}
    common = '<h1>Provider resources</h1><p>Find forms and provider guidance.</p><a href="/docs/form.pdf">Form</a>'
    pages = [
        {"id": "PAGE-example-home", "route": "/home", "source": response(SOURCE + "/home", html(common)),
         "target": response(TARGET + "/home", html(common + '<img alt="" src="/decoration.png">', lang=""))},
        {"id": "PAGE-example-lookup", "route": "/lookup", "source": response(SOURCE + "/lookup", html('<h1>Code lookup</h1><p>Read eligibility guidance before using this tool.</p>')),
         "target": response(TARGET + "/lookup", html('<p>Code lookup</p><input name="code">'))},
        {"id": "PAGE-example-forms", "route": "/forms", "source": response(SOURCE + "/forms", html(common)),
         "target": response(TARGET + "/forms", html(common + '<a href="/docs/restricted.pdf">Restricted resource</a>'))},
        {"id": "PAGE-example-contact", "route": "/contact", "source": response(SOURCE + "/contact", html('<h1>Contact</h1><p>Contact the provider team for assistance.</p>')),
         "target": response(TARGET + "/contact", status=0, error="Synthetic timeout")},
    ]
    checks = [{"url": TARGET + "/docs/form.pdf", "finalUrl": TARGET + "/docs/form.pdf", "status": 404, "error": ""},
              {"url": TARGET + "/docs/restricted.pdf", "finalUrl": TARGET + "/docs/restricted.pdf", "status": 403, "error": ""}]
    return {"schemaVersion": 1, "methodVersion": audit.VERSION, "synthetic": True,
            "generatedAt": "2026-09-28T12:00:00+00:00", "config": config, "configHash": audit.digest(config),
            "inventory": {"inputs": [], "excluded": [], "candidateCount": 4}, "pages": pages, "linkChecks": checks}


class AuditTests(unittest.TestCase):
    def test_unique_targets_not_summed_page_occurrences(self):
        result = audit.analyze(example_evidence(), None)
        self.assertEqual(result["summary"]["unavailableLinks"], 1)
        self.assertEqual(result["summary"]["affectedPages"], 2)
        self.assertEqual(result["summary"]["unverifiedLinks"], 1)
        self.assertEqual(sum(len(p["brokenLinks"]) for p in result["rows"]), 2)

    def test_failure_is_unknown_and_excluded_from_similarity_denominator(self):
        result = audit.analyze(example_evidence(), None)
        contact = next(r for r in result["rows"] if r["route"] == "/contact")
        self.assertEqual(contact["content"], "Unverified")
        self.assertEqual(contact["metrics"], {})
        self.assertEqual(result["summary"]["comparablePages"], 3)
        self.assertEqual(result["summary"]["textSampleSize"], 3)
        for status in (0, 401, 403, 429, 500, 503):
            self.assertEqual(audit.link_state({"status": status}), "unverified")
        self.assertEqual(audit.link_state({"status": 200, "error": "Truncated"}), "unverified")

    def test_low_similarity_does_not_auto_assign_critical(self):
        rows = audit.analyze(example_evidence(), None)["rows"]
        lookup = next(r for r in rows if r["route"] == "/lookup")
        self.assertEqual(lookup["content"], "Review")
        self.assertIn("Missing H1: regression", lookup["flags"])
        self.assertNotIn("Critical", [r["content"] for r in rows])

    def test_inherited_h1_and_decorative_alt_not_critical(self):
        data = example_evidence()
        data["pages"][1]["source"]["html"]["h1s"] = []
        rows = audit.analyze(data, None)["rows"]
        self.assertIn("Missing H1: inherited", next(r for r in rows if r["route"] == "/lookup")["flags"])
        home = next(r for r in rows if r["route"] == "/home")
        self.assertEqual(home["content"], "Good")
        self.assertIn("1 empty-alt images to review", home["flags"])

    def test_http_200_redirect_requires_review(self):
        data = example_evidence()
        data["pages"][0]["target"]["finalUrl"] = TARGET + "/login"
        row = next(r for r in audit.analyze(data, None)["rows"] if r["route"] == "/home")
        self.assertEqual(row["content"], "Review")
        self.assertIn("Target redirect requires review", row["flags"])

    def test_empty_metrics_are_not_passes(self):
        self.assertIsNone(audit.coverage([], []))
        self.assertIsNone(audit.similarity("", ""))

    def test_parser_entities_main_links_and_alt(self):
        p = audit.PageParser(TARGET + "/home")
        p.feed('<html lang="en"><head><title>A &amp; B</title></head><body><nav><a href="/nav">Nav</a></nav><main><h1>One <span>title</span></h1><h3>Next</h3><script>hidden code</script><a href="/doc?a=1&amp;b=2#top">A &amp; B</a><img><img alt=""></main></body></html>')
        result = p.summary()
        self.assertEqual(result["title"], "A & B")
        self.assertEqual(result["h1s"], ["One title"])
        self.assertEqual(result["headingJumps"], 1)
        self.assertEqual(len(result["links"]), 1)
        self.assertEqual(result["links"][0]["url"], TARGET + "/doc?a=1&b=2")
        self.assertNotIn("hidden code", result["mainText"])
        self.assertEqual((result["missingAltCount"], result["emptyAltCount"]), (1, 1))

    def test_recursive_gzip_sitemap_and_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "snapshots").mkdir()
            (root / "index.xml").write_text('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><sitemap><loc>child.xml.gz</loc></sitemap><sitemap><loc>index.xml</loc></sitemap></sitemapindex>')
            (root / "child.xml.gz").write_bytes(gzip.compress(f'<urlset><url><loc>{SOURCE}/home</loc></url><url><loc>{SOURCE}/home#top</loc></url><url><loc>{SOURCE}/private/page</loc></url><url><loc>https://other.example/page</loc></url></urlset>'.encode()))
            config = {"sourceOrigin": SOURCE, "maxSitemaps": 10, "maxPages": 10,
                      "inventories": [{"location": "index.xml", "kind": "sitemap"}], "includePrefixes": ["/"], "excludePrefixes": ["/private/"]}
            urls, inventory = audit.read_inventory(config, root, None, root)
            self.assertEqual(urls, [SOURCE + "/home"])
            self.assertEqual(len(inventory["inputs"]), 2)
            self.assertEqual(len(inventory["excluded"]), 2)
            config["includePrefixes"] = ["/no-match"]
            with self.assertRaisesRegex(ValueError, "zero in-scope"):
                audit.read_inventory(config, root, None, root)

    def test_inventory_empty_limit_and_malformed_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "snapshots").mkdir()
            config = {"sourceOrigin": SOURCE, "maxSitemaps": 10, "maxPages": 1,
                      "inventories": [{"location": "urls.txt", "kind": "urls"}], "includePrefixes": ["/"], "excludePrefixes": []}
            (root / "urls.txt").write_text(SOURCE + "/a\n" + SOURCE + "/b\n")
            with self.assertRaisesRegex(ValueError, "Page limit"):
                audit.read_inventory(config, root, None, root)
            (root / "urls.txt").write_text("")
            with self.assertRaisesRegex(ValueError, "zero in-scope"):
                audit.read_inventory(config, root, None, root)
            config["inventories"][0]["kind"] = "sitemap"
            (root / "urls.txt").write_text("<urlset><url/></urlset>")
            with self.assertRaisesRegex(ValueError, "Missing loc"):
                audit.read_inventory(config, root, None, root)

    def test_url_identity_preserves_significant_components(self):
        self.assertEqual(audit.url_key("https://EXAMPLE.com/A/?q=one#top"), "https://example.com/A/?q=one")
        self.assertNotEqual(audit.url_key(SOURCE + "/A"), audit.url_key(SOURCE + "/a"))
        with self.assertRaises(ValueError):
            audit.url_key("file:///etc/passwd")

    def test_reviews_bound_to_evidence_and_required_fields(self):
        data = example_evidence()
        with self.assertRaisesRegex(ValueError, "stale"):
            audit.analyze(data, {"evidenceSha256": "old", "findings": []})
        with self.assertRaisesRegex(ValueError, "nonempty"):
            audit.analyze(data, {"evidenceSha256": audit.digest(data), "findings": [{"id": "F-1"}]})

    def test_confirmed_vs_accepted_priority_and_stale_reviews(self):
        root = Path(__file__).resolve().parents[1] / "docs/gap-audit/examples"
        data = json.loads((root / "evidence.json").read_text())
        reviews = json.loads((root / "reviews.json").read_text())
        result = audit.analyze(data, reviews)
        self.assertEqual(next(r for r in result["rows"] if r["route"] == "/home")["content"], "Good")
        reviews["findings"][1]["priority"] = "P0"
        reviews["findings"][1]["contentFidelity"] = "Critical"
        result = audit.analyze(data, reviews)
        self.assertEqual(next(r for r in result["rows"] if r["route"] == "/lookup")["content"], "Critical")
        reviews["findings"][0]["disposition"] = "accepted"
        result = audit.analyze(data, reviews)
        self.assertEqual(next(r for r in result["rows"] if r["route"] == "/home")["content"], "Good")
        data["generatedAt"] = "2026-09-29T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "stale"):
            audit.analyze(data, reviews)

    def test_http_transport_redirect_scope_and_status(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == "/redirect":
                    self.send_response(302)
                    self.send_header("Location", "/ok")
                elif self.path == "/external":
                    self.send_response(302)
                    self.send_header("Location", "https://outside.invalid/page")
                else:
                    self.send_response(404 if self.path == "/missing" else 200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<html><main><h1>Test</h1></main></html>")

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            fetch = audit.Fetcher([base], timeout=2, delay=0)
            try:
                result, raw = fetch(base + "/redirect")
                self.assertEqual(result["status"], 200)
                self.assertEqual(result["finalUrl"], base + "/ok")
                self.assertEqual(len(result["redirects"]), 1)
                self.assertTrue(raw)
                result, _ = fetch(base + "/missing", body=False)
                self.assertEqual(audit.link_state(result), "unavailable")
                result, _ = fetch(base + "/external")
                self.assertEqual(audit.link_state(result), "unverified")
                self.assertIn("outside configured origins", result["error"])
            finally:
                server.shutdown()
                worker.join()

    def test_schema_counts_and_hash_validation(self):
        data = example_evidence()
        data["linkChecks"].pop()
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            audit.analyze(data, None)
        data = example_evidence()
        data["config"]["name"] = "Changed"
        with self.assertRaisesRegex(ValueError, "hash"):
            audit.analyze(data, None)

    def test_render_is_byte_identical_and_fixed_order(self):
        data = example_evidence()
        report = audit.report(data, audit.analyze(data, None))
        reordered = deepcopy(data)
        reordered["pages"].reverse()
        rows = audit.analyze(reordered, None)["rows"]
        self.assertEqual(rows, audit.analyze(data, None)["rows"])
        self.assertEqual(report, audit.report(data, audit.analyze(data, None)))
        self.assertEqual([x[3:] for x in report.splitlines() if x.startswith("## ")], audit.SECTIONS)
        self.assertIn("SYNTHETIC EXAMPLE", report)

    def test_complete_collect_and_offline_render(self):
        calls = []

        def fake_fetch(_self, url, body=True):
            calls.append((url, body))
            status = 404 if "/docs/" in url else 200
            raw = html('<h1>Test</h1><p>Important provider information.</p><a href="/docs/missing.pdf">Document</a>').encode()
            result = {"url": url, "finalUrl": url, "status": status, "error": "", "contentType": "text/html", "redirects": [], "checkedAt": "2026-09-28T12:00:00Z"}
            return result, raw if body else b""

        with tempfile.TemporaryDirectory() as temp, patch.object(audit.Fetcher, "__call__", fake_fetch):
            root = Path(temp)
            (root / "urls.txt").write_text(SOURCE + "/old\n")
            config = {"name": "Fixture", "sourceOrigin": SOURCE, "targetOrigin": TARGET,
                      "inventories": [{"location": "urls.txt", "kind": "urls"}], "routeMap": {"/old": "/new"}}
            audit.write_json(root / "config.json", config)
            audit.collect(root / "config.json", root / "run")
            original = (root / "run/report.md").read_bytes()
            with patch.object(audit.Fetcher, "__call__", side_effect=AssertionError("Offline render fetched a URL")):
                audit.render(root / "run/evidence.json", root / "replay")
            self.assertEqual(original, (root / "replay/report.md").read_bytes())
            self.assertEqual(calls, [(SOURCE + "/old", True), (TARGET + "/new", True), (TARGET + "/docs/missing.pdf", False)])
            self.assertEqual(json.loads((root / "run/analysis.json").read_text())["summary"]["unavailableLinks"], 1)
            with self.assertRaises(FileExistsError):
                audit.collect(root / "config.json", root / "run")


if __name__ == "__main__":
    unittest.main()
