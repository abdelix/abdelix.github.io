# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal academic website of Abdelfettah Hadij-ElHouati (photonic design engineer, PhD in integrated photonics), served at `https://abdelix.com` (see `CNAME`). It is built with Jekyll using the **al-folio v1.x** starter. al-folio v1 is a thin starter, not a theme: layouts, includes, Sass and feature JS live in versioned `al_*` gems pinned in `Gemfile`. This repo holds only configuration and content.

## Commands

```sh
bundle install
bundle exec jekyll serve          # http://localhost:4000/ (baseurl is empty)
bundle exec jekyll build          # output in _site/
python3 bin/sync_orcid.py         # regenerate _bibliography/papers.bib and patents.bib from ORCID
```

There is no test suite. A change is validated by running `jekyll build` and checking the rendered pages. The system `bundle` binary on the author's machine may point to a missing Ruby. If it does, install Bundler under Ruby 3.3, or use `docker compose up`, which uses the prebuilt al-folio image.

## Architecture

- **Content locations:**
  - `_pages/` holds the navbar pages: about (`/`), publications, patents, projects, blog. `nav_order` sets their order. The CV page (`cv.md`) is currently hidden from the navbar with `nav: false` but is still built at `/cv/`.
  - `_projects/` holds the project pages.
  - `_posts/` holds the blog posts. It is currently empty.
  - `_data/cv.yml` is the CV data, a condensed version of the author's PDF CV.
  - `_data/socials.yml` holds the social links.
- **Do not add** `_layouts/`, `_includes/`, `_sass/` or `assets/tailwind/` unless you are deliberately overriding a gem file. Look at the gem source first: `bundle info al_folio_core --path`.
- **Local override:** `_layouts/bib.liquid` is a copy of al_folio_core's layout, changed only so that `abbr` can hold several badges separated by `|` (one badge per patent country, plus "Conference"). When upgrading al_folio_core, diff it against the gem's version and re-apply that one block. Badge colours come from `_data/venues.yml`, keyed by badge text.
- **Plugins must be listed in two places.** A plugin has to appear in both `Gemfile` and the `plugins:` list in `_config.yml`, otherwise it is inert. Disabled features render nothing and raise no error.
- **Publications and patents are generated.** `bin/sync_orcid.py` (standard library only) reads the public ORCID record `0000-0002-8363-7423`:
  - Works with a DOI are filled in from Crossref; the rest fall back to ORCID metadata.
  - Non-patent works go to `_bibliography/papers.bib`, followed by the contents of `_bibliography/manual.bib`.
  - Patents go to `patents.bib`. They are searched on EPO Open Patent Services by inventor name, which needs `EPO_OPS_KEY`/`EPO_OPS_SECRET` (GitHub repository secrets in CI, a git-ignored `.env` locally; without them the search is skipped). ORCID patents and `_bibliography/patents_manual.bib` fill the gaps. Entries are deduplicated per patent family using the publication numbers in `number` and `note`.
  - First-author journal articles get `selected = {true}`, which shows them on the about page.
  - Never edit `papers.bib` or `patents.bib` by hand. Add missing items to `manual.bib`, or better, add them to ORCID.
- **CI:**
  - `.github/workflows/deploy.yml` builds on pushes to `master` and publishes `_site` to the `gh-pages` branch. GitHub Pages must be set to serve from `gh-pages`.
  - `.github/workflows/sync-orcid.yml` runs the sync every Monday, commits any changes, and then starts `deploy.yml` explicitly. It has to, because a push made with `GITHUB_TOKEN` does not trigger other workflows.
- **Projects:** the old 2013–2014 student projects live in `_projects/` with `category: archived` and an "Archived project" notice. Their permalinks `/projects/<name>/` match the legacy site.
- **Page descriptions:** front-matter `description` values end up in `<meta>` tags, so keep them plain text with no HTML links.
- `downloads/memo.html` is a legacy standalone file, kept only so that existing external links keep working.

## Conventions

- Commit every change, grouped logically, using Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `ci:` …). Each commit needs a descriptive subject and a body explaining what changed and why.
- Do not publish private contact details such as the phone number from the PDF CV.
