#!/usr/bin/env python3
"""Regenerate the site bibliographies from a public ORCID record.

Writes two files that jekyll-scholar renders:

  _bibliography/papers.bib   every ORCID work that is not a patent, followed by
                             the hand-written entries in _bibliography/manual.bib
  _bibliography/patents.bib  every ORCID work of type "patent", followed by the
                             entries in _bibliography/patents_manual.bib whose
                             patent family was not found automatically

Works with a DOI are described from Crossref metadata (full author list, venue,
volume, pages, abstract); works without one fall back to what ORCID stores.

Patents are also searched on EPO Open Patent Services by inventor name, one entry
per patent family. This needs EPO_OPS_KEY and EPO_OPS_SECRET, read from the
environment or a git-ignored .env file; without them the EPO search is skipped.

Only the Python standard library is used so it runs anywhere, including CI.

Usage:  python3 bin/sync_orcid.py [--orcid 0000-0002-8363-7423]
"""

import argparse
import base64
import html
import json
import os
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
# Spellings of the surname found on patent documents; each one is searched as an inventor on EPO OPS.
SURNAME_VARIANTS = ["Hadij", "Hadij-ElHouati", "Hadij El Houati", "Hadij ElHouati", "HadijElHouati"]
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


def fetch_json(url, accept="application/json", retries=3, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers={"Accept": accept, "User-Agent": USER_AGENT, **(headers or {})})
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


PUB_NUMBER = re.compile(r"\b([A-Z]{2})\s?(\d{6,12})\s?([A-Z]\d?)?\b")


def normalize_pub_number(country, number):
    """Canonical form of a patent publication number, without kind code.

    US pre-grant publications are written with an 11-digit number (US20240004261A1)
    but EPO's DOCDB format drops the zero after the year (US2024004261).
    """
    if country == "US" and len(number) == 11 and number[4] == "0":
        number = number[:4] + number[5:]
    return country + number.lstrip("0")


def pub_numbers(text):
    """All publication numbers mentioned in a string, normalised."""
    return {normalize_pub_number(c, n) for c, n, _ in PUB_NUMBER.findall(text or "")}


def finish_patent(entry):
    """Fill the fields the al-folio bib layout shows for a patent."""
    number, holder = entry.get("number"), entry.get("holder")
    entry["additional_info"] = " · ".join(x for x in (number, holder) if x)
    if number and not entry.get("abbr"):
        # One badge per country the family is published in (split on "|" by _layouts/bib.liquid).
        countries = [number[:2]] + [country for country, _, _ in PUB_NUMBER.findall(entry.get("note") or "")]
        entry["abbr"] = "|".join(f"{country} Patent" for country in dict.fromkeys(countries))
    if entry.get("url") and not entry.get("website"):
        entry["website"] = entry.pop("url")
    return entry


def load_env_file():
    """Read KEY=VALUE lines from a local .env (git-ignored) without overriding the environment."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.strip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def as_list(value):
    return value if isinstance(value, list) else ([] if value is None else [value])


def ops_text(value):
    """Text of an OPS JSON node ({"$": "text"})."""
    return value.get("$", "") if isinstance(value, dict) else (value or "")


def ops_names(parties, kind):
    """Names of inventors/applicants.

    OPS lists each person in an 'original' and an 'epodoc' spelling. The original one reads
    better, but on some documents it is incomplete, so the longer of the two lists is used.
    """
    people = as_list((parties.get(f"{kind}s") or {}).get(kind))
    by_format = {}
    for p in people:
        name = ops_text((p.get(f"{kind}-name") or {}).get("name"))
        name = re.sub(r"\s*\[[A-Z]{2}\]\s*$", "", name).strip().strip(",").strip()
        by_format.setdefault(p.get("@data-format"), []).append(name)
    original, epodoc = by_format.get("original", []), by_format.get("epodoc", [])
    return original if len(original) >= len(epodoc) else epodoc


def ops_all_names(parties, kind):
    """Every spelling of every inventor/applicant, for matching the author's name."""
    return [ops_text((p.get(f"{kind}-name") or {}).get("name")) for p in as_list((parties.get(f"{kind}s") or {}).get(kind))]


def org_case(name):
    """'NATIONAL RESEARCH COUNCIL OF CANADA' -> 'National Research Council of Canada'."""
    if not name.isupper():
        return name
    small = {"of", "de", "del", "la", "las", "los", "the", "and", "y", "for", "et", "du", "des"}
    words = name.title().split()
    return " ".join(w.lower() if i and w.lower() in small else w for i, w in enumerate(words))


def ops_title(bib):
    """English title, preferring an official one over a machine translation."""
    titles = [t for t in as_list(bib.get("invention-title")) if ops_text(t)]
    english = [t for t in titles if t.get("@lang") == "en"]
    official = [t for t in english if "machine-translation" not in ops_text(t).lower()]
    title = clean_text(ops_text((official or english or titles or [{}])[0]))
    title = re.sub(r"\s*\(Machine-translation.*?\)\s*$", "", title, flags=re.I)
    return title.capitalize() if title.isupper() else title


def is_self(name):
    """True for any spelling of the author: Hadij-ElHouati, HADIJ EL HOUATI, 'Hadij, Abdelfettah', ..."""
    compact = re.sub(r"[^A-Z]", "", ascii_slug(name).upper())
    return "HADIJELHOUATI" in compact or (compact.startswith("HADIJ") and "ABDELFETTAH" in compact)


def ops_person(name):
    """'HADIJ EL HOUATI, Abdelfettah' / 'CHEBEN PAVEL' -> 'Family, Given'."""
    if is_self(name):
        return f"{OWN_FAMILY_NAME}, Abdelfettah"
    if "," in name:
        family, given = (part.strip() for part in name.split(",", 1))
    else:
        *family_parts, given = name.split()
        family = " ".join(family_parts)
    fix = lambda s: s.title() if s.isupper() else s
    return f"{fix(family)}, {fix(given)}".strip(", ")


def display_number(country, number, kind):
    """US20240004261A1 style (EPO's DOCDB drops the zero after the year in US publications)."""
    if country == "US" and len(number) == 10 and number.startswith("20"):
        number = number[:4] + "0" + number[4:]
    return f"{country}{number}{kind}"


def from_epo():
    """Patent families on EPO Open Patent Services where the author is an inventor.

    1. search published documents by inventor name (SURNAME_VARIANTS); OPS returns one
       document per family, often a national (ES, CA) publication;
    2. list every publication of each matching family;
    3. describe the family from its preferred publication (WO, then EP, then US, ...),
       which carries the official English title and the full inventor list.

    Needs EPO_OPS_KEY / EPO_OPS_SECRET (environment or .env); returns [] without them.
    """
    key, secret = os.environ.get("EPO_OPS_KEY"), os.environ.get("EPO_OPS_SECRET")
    if not (key and secret):
        print("EPO_OPS_KEY/EPO_OPS_SECRET not set: skipping the EPO patent search.", file=sys.stderr)
        return []
    basic = base64.b64encode(f"{key}:{secret}".encode()).decode()
    token = fetch_json(
        "https://ops.epo.org/3.2/auth/accesstoken",
        headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
        data=b"grant_type=client_credentials",
    )["access_token"]

    def ops(path):
        result = fetch_json(f"https://ops.epo.org/3.2/rest-services/{path}", headers={"Authorization": f"Bearer {token}"})
        return (result or {}).get("ops:world-patent-data") or {}

    def docdb_id(document_ids):
        docdb = next((d for d in as_list(document_ids) if d.get("@document-id-type") == "docdb"), None) or {}
        return {k: ops_text(docdb.get(k)) for k in ("country", "doc-number", "kind", "date")}

    # 1. search
    cql = " or ".join(f'in="{variant.lower()}"' for variant in SURNAME_VARIANTS)
    search = ops("published-data/search/biblio?" + urllib.parse.urlencode({"q": cql, "Range": "1-100"}))
    found = {}
    for item in as_list(((search.get("ops:biblio-search") or {}).get("ops:search-result") or {}).get("exchange-documents")):
        for doc in as_list(item.get("exchange-document")):
            parties = (doc.get("bibliographic-data") or {}).get("parties") or {}
            if any(is_self(n) for n in ops_all_names(parties, "inventor")):
                found.setdefault(doc.get("@family-id"), f"{doc['@country']}.{doc['@doc-number']}.{doc['@kind']}")

    preference = {"WO": 0, "EP": 1, "US": 2}
    entries = []
    for publication in found.values():
        # 2. family members
        family = ops(f"family/publication/docdb/{publication}")
        members = []
        for member in as_list((family.get("ops:patent-family") or {}).get("ops:family-member")):
            ref = docdb_id((member.get("publication-reference") or {}).get("document-id"))
            if ref["country"] and ref["doc-number"]:
                members.append(ref)
        if not members:
            country, number, kind = publication.split(".")
            members = [{"country": country, "doc-number": number, "kind": kind, "date": ""}]
        members.sort(key=lambda m: (preference.get(m["country"], 3), m["date"] or "99999999"))
        main = members[0]

        # 3. bibliographic data of the preferred publication
        biblio = ops(f"published-data/publication/docdb/{main['country']}.{main['doc-number']}.{main['kind']}/biblio")
        doc = next(iter(as_list((biblio.get("exchange-documents") or {}).get("exchange-document"))), {})
        bib = doc.get("bibliographic-data") or {}
        parties = bib.get("parties") or {}
        date = main["date"] or docdb_id((bib.get("publication-reference") or {}).get("document-id"))["date"]
        holders = [org_case(h) for h in ops_names(parties, "applicant")]
        number = display_number(main["country"], main["doc-number"], main["kind"])
        others = [display_number(m["country"], m["doc-number"], m["kind"]) for m in members[1:]]
        entries.append(
            {
                "type": "patent",
                "title": ops_title(bib),
                "author": [ops_person(n) for n in ops_names(parties, "inventor")],
                "holder": ", ".join(dict.fromkeys(holders)),
                "number": number,
                "year": date[:4] or None,
                "month": int(date[4:6]) if len(date) >= 6 else None,
                "note": "Also published as " + ", ".join(dict.fromkeys(others)) if others else None,
                "url": f"https://worldwide.espacenet.com/patent/search?q=pn%3D{number}",
                "bibtex_show": "true",
            }
        )
    return entries


def manual_patents(covered):
    """Entries of patents_manual.bib whose family is not already in `covered`."""
    path = BIB_DIR / "patents_manual.bib"
    if not path.exists():
        return []
    kept = []
    for text in re.split(r"\n(?=@)", path.read_text(encoding="utf-8")):
        if not text.startswith("@"):
            continue  # file header comments
        fields = re.findall(r"^\s*(?:number|note)\s*=\s*\{(.*?)\},?$", text, flags=re.M)
        if pub_numbers(" ".join(fields)) & covered:
            continue
        kept.append(text.strip() + "\n")
    return kept


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
    order = ["title", "author", "journal", "booktitle", "publisher", "holder", "volume", "number", "pages", "year", "month"]
    order += ["additional_info", "note", "doi", "url", "website", "abbr", "abstract", "selected", "bibtex_show"]
    for name in order:
        value = entry.get(name)
        if name == "author" and value:
            value = " and ".join(value)
        if value in (None, "", []):
            continue
        value = value if name in ("url", "website", "doi") else bib_escape(value)
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
        # Mark conference presentations with their own badge (badges are split on "|" by _layouts/bib.liquid).
        if entry["type"] == "inproceedings":
            entry["abbr"] = "|".join(b for b in ("Conference", entry.get("abbr")) if b)
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
    def numbers_of(entry):
        return pub_numbers(f"{entry.get('number', '')} {entry.get('note', '')}")

    # EPO is the most complete patent source; ORCID and manual entries only fill the gaps.
    covered = set()
    epo_patents = from_epo()
    for e in epo_patents:
        covered |= numbers_of(e)
    orcid_patents = [e for e in patents if not numbers_of(e) & covered]
    patents = [finish_patent(e) for e in epo_patents + orcid_patents]
    for e in patents:
        covered |= numbers_of(e)
    manual_entries = manual_patents(covered)
    patents_bib = header + "% add patents that are not found automatically to _bibliography/patents_manual.bib.\n\n"
    patents_bib += "\n".join(to_bibtex(make_key(e, used), e) for e in sorted(patents, key=by_date, reverse=True))
    if manual_entries:
        patents_bib += "\n% ---- Entries copied from _bibliography/patents_manual.bib ----\n\n" + "\n".join(manual_entries)
    return papers_bib, patents_bib, len(papers), len(patents) + len(manual_entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--orcid", default=DEFAULT_ORCID)
    args = parser.parse_args()
    load_env_file()
    papers_bib, patents_bib, n_papers, n_patents = build(args.orcid)
    (BIB_DIR / "papers.bib").write_text(papers_bib, encoding="utf-8")
    (BIB_DIR / "patents.bib").write_text(patents_bib, encoding="utf-8")
    print(f"Wrote {n_papers} publications and {n_patents} patents from ORCID {args.orcid}", file=sys.stderr)


if __name__ == "__main__":
    main()
