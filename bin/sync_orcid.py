#!/usr/bin/env python3
"""Regenerate the site bibliographies from a public ORCID record.

Writes two files that jekyll-scholar renders:

  _bibliography/papers.bib   every ORCID work that is not a patent, followed by
                             the hand-written entries in _bibliography/manual.bib
  _bibliography/patents.bib  every ORCID work of type "patent"

Works with a DOI are described from Crossref metadata (full author list, venue,
volume, pages, abstract); works without one fall back to what ORCID stores.
Only the Python standard library is used so it runs anywhere, including CI.

Usage:  python3 bin/sync_orcid.py [--orcid 0000-0002-8363-7423]
"""

import argparse
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_ORCID = "0000-0002-8363-7423"
OWN_FAMILY_NAME = "Hadij-ElHouati"
ROOT = Path(__file__).resolve().parent.parent
BIB_DIR = ROOT / "_bibliography"
USER_AGENT = "abdelix.com-bibliography-sync (mailto:abdel.he.93@gmail.com)"

# ORCID work type -> BibTeX entry type
ORCID_TYPES = {
    "journal-article": "article",
    "conference-paper": "inproceedings",
    "conference-abstract": "inproceedings",
    "conference-poster": "inproceedings",
    "book": "book",
    "book-chapter": "incollection",
    "dissertation-thesis": "phdthesis",
    "preprint": "misc",
    "patent": "patent",
}
# Crossref type -> BibTeX entry type (preferred over ORCID's type when a DOI resolves)
CROSSREF_TYPES = {
    "journal-article": "article",
    "proceedings-article": "inproceedings",
    "book-chapter": "incollection",
    "book": "book",
    "posted-content": "misc",
    "dissertation": "phdthesis",
}


def fetch_json(url, accept="application/json", retries=3):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                return None
            if attempt == retries - 1:
                raise
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
        time.sleep(2**attempt)
    return None


def clean_text(value):
    """Strip JATS/HTML markup and collapse whitespace."""
    if not value:
        return ""
    value = re.sub(r"<jats:title>.*?</jats:title>", "", value, flags=re.S)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def bib_escape(value):
    value = str(value).replace("\\", "")
    for char in "&%#_$":
        value = value.replace(char, "\\" + char)
    return value.replace("{", "").replace("}", "")


def ascii_slug(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", value.lower())


def external_ids(obj):
    ids = (obj.get("external-ids") or {}).get("external-id") or []
    return {e["external-id-type"]: e["external-id-value"] for e in ids}


def split_ieee_authors(citation):
    """Pull the author list out of an IEEE-formatted citation: 'A. B, C. D, and E. F, “Title,” ...'."""
    head = re.split(r"[“\"]", citation, maxsplit=1)[0].strip().rstrip(",")
    names = re.split(r",\s*(?:and\s+)?|\s+and\s+", head)
    return [n.strip() for n in names if n.strip()]


def from_crossref(doi):
    msg = (fetch_json("https://api.crossref.org/works/" + urllib.parse.quote(doi)) or {}).get("message")
    if not msg:
        return None
    date = (msg.get("published-print") or msg.get("published") or msg.get("issued") or {}).get("date-parts", [[None]])[0]
    authors = []
    for a in msg.get("author", []):
        if a.get("family"):
            authors.append(f"{a['family']}, {a.get('given', '')}".strip(", "))
        elif a.get("name"):
            authors.append(a["name"])
    entry = {
        "type": CROSSREF_TYPES.get(msg.get("type"), "misc"),
        "title": clean_text((msg.get("title") or [""])[0]),
        "author": authors,
        "year": date[0] if date else None,
        "month": date[1] if date and len(date) > 1 else None,
        "doi": doi.lower(),
        "volume": msg.get("volume"),
        "number": msg.get("issue"),
        "pages": msg.get("page") or msg.get("article-number"),
        "publisher": msg.get("publisher"),
        "abstract": clean_text(msg.get("abstract")),
    }
    container = clean_text((msg.get("container-title") or [""])[0])
    short = clean_text((msg.get("short-container-title") or [""])[0])
    if entry["type"] == "article":
        entry["journal"] = container
    elif container:
        entry["booktitle"] = container
    if short and len(short) <= 20:
        entry["abbr"] = short
    return entry


def from_orcid(orcid, summary):
    work = fetch_json(f"https://pub.orcid.org/v3.0/{orcid}/work/{summary['put-code']}") or summary
    date = work.get("publication-date") or {}
    authors = [
        (c.get("credit-name") or {}).get("value")
        for c in (work.get("contributors") or {}).get("contributor", [])
        if (c.get("credit-name") or {}).get("value")
    ]
    citation = work.get("citation") or {}
    if not authors and citation.get("citation-type") == "formatted-ieee":
        authors = split_ieee_authors(citation.get("citation-value", ""))
    entry = {
        "type": ORCID_TYPES.get(work.get("type"), "misc"),
        "title": clean_text(work["title"]["title"]["value"]),
        "author": authors or [OWN_FAMILY_NAME + ", A."],
        "year": (date.get("year") or {}).get("value"),
        "month": (date.get("month") or {}).get("value"),
        "url": (work.get("url") or {}).get("value"),
    }
    venue = (work.get("journal-title") or {}).get("value")
    if venue:
        venue = clean_text(venue)
        venue += ")" * (venue.count("(") - venue.count(")"))  # ORCID truncates some long venue names
        entry["journal" if entry["type"] == "article" else "booktitle"] = venue
    ids = external_ids(work)
    for key in ("patent-number", "pat"):
        if key in ids:
            entry["number"] = ids[key]
    return entry


def make_key(entry, used):
    first = entry["author"][0] if entry["author"] else OWN_FAMILY_NAME
    family = first.split(",")[0] if "," in first else first.split()[-1]
    word = next((w for w in re.findall(r"[A-Za-z]+", entry["title"]) if len(w) > 3), "work")
    base = f"{ascii_slug(family)}{entry.get('year') or ''}{ascii_slug(word)}"
    key, n = base, 1
    while key in used:
        n += 1
        key = f"{base}{chr(ord('a') + n - 1)}"
    used.add(key)
    return key


def to_bibtex(key, entry):
    fields = []
    order = ["title", "author", "journal", "booktitle", "publisher", "volume", "number", "pages", "year", "month"]
    order += ["doi", "url", "abbr", "abstract", "selected", "bibtex_show"]
    for name in order:
        value = entry.get(name)
        if name == "author" and value:
            value = " and ".join(value)
        if value in (None, "", []):
            continue
        value = value if name in ("url", "doi") else bib_escape(value)
        fields.append(f"  {name} = {{{value}}}")
    return f"@{entry['type']}{{{key},\n" + ",\n".join(fields) + "\n}\n"


def build(orcid):
    groups = (fetch_json(f"https://pub.orcid.org/v3.0/{orcid}/works") or {}).get("group", [])
    papers, patents = [], []
    for group in groups:
        summary = group["work-summary"][0]
        doi = external_ids(summary).get("doi")
        entry = (from_crossref(doi) if doi else None) or from_orcid(orcid, summary)
        if doi:
            entry["doi"] = doi.lower()
        if summary.get("type") == "patent":
            entry["type"] = "patent"
        entry["bibtex_show"] = "true"
        # Highlight first-author journal papers on the about page.
        if entry["type"] == "article" and entry["author"] and entry["author"][0].startswith(OWN_FAMILY_NAME):
            entry["selected"] = "true"
        (patents if entry["type"] == "patent" else papers).append(entry)

    def by_date(e):
        return (int(e.get("year") or 0), int(e.get("month") or 0), e["title"])

    used = set()
    header = f"% Generated by bin/sync_orcid.py from https://orcid.org/{orcid}. Do not edit by hand:\n"
    papers_bib = header + "% add entries that are not on ORCID to _bibliography/manual.bib instead.\n\n"
    papers_bib += "\n".join(to_bibtex(make_key(e, used), e) for e in sorted(papers, key=by_date, reverse=True))
    manual = BIB_DIR / "manual.bib"
    if manual.exists():
        papers_bib += "\n% ---- Entries copied from _bibliography/manual.bib ----\n\n" + manual.read_text(encoding="utf-8")
    patents_bib = header + "% list patents as works of type 'Patent' on ORCID to have them appear here.\n\n"
    patents_bib += "\n".join(to_bibtex(make_key(e, used), e) for e in sorted(patents, key=by_date, reverse=True))
    return papers_bib, patents_bib, len(papers), len(patents)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--orcid", default=DEFAULT_ORCID)
    args = parser.parse_args()
    papers_bib, patents_bib, n_papers, n_patents = build(args.orcid)
    (BIB_DIR / "papers.bib").write_text(papers_bib, encoding="utf-8")
    (BIB_DIR / "patents.bib").write_text(patents_bib, encoding="utf-8")
    print(f"Wrote {n_papers} publications and {n_patents} patents from ORCID {args.orcid}", file=sys.stderr)


if __name__ == "__main__":
    main()
