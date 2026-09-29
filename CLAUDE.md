# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Personal website/blog ("Abdelix Lab") built with Jekyll and served by GitHub Pages at the custom domain `abdelix.com` (see `CNAME`). Pushing to `master` deploys. There is no Gemfile, test suite, or linter. Most content and comments are in English, and some text is in Spanish.

## Local preview

```sh
jekyll serve        # builds into _site/ (gitignored) and serves at http://localhost:4000
jekyll build        # build only
```

`_config.yml` sets `paginate`/`paginate_path` but doesn't list the `jekyll-paginate` plugin. GitHub Pages' legacy build handles this, but a modern local Jekyll may need `plugins: [jekyll-paginate]` (and the gem) before `blog/index.html` paginates.

## Architecture

- **Layouts**: `_layouts/default.html` is the base (header + Bootstrap 2 `row-fluid` with an 8/4 split: content on the left, `_includes/sidebar.html` on the right, then the footer). `post.html` and `default-comments.html` both extend `default` and add Disqus comments (shortname `abdelix`). `old-default.html` isn't used.
- **Blog posts** live in `_posts/`. Jekyll ignores files that start with `_` (e.g. `_2014-...md`), and that is how drafts and unpublished posts are hidden here. Posts use `layout: post`.
  - `index.html` shows the full content of the latest 5 posts.
  - `blog/index.html` is the paginated list of post excerpts.
  - `index.xml` is the RSS feed (`layout: nil`).
- **Projects** are regular pages at `projects/<name>/index.md` with front matter `category: 'projects'`, a `title`, a `description`, and usually `layout: default-comments`. Any page with that category is picked up automatically in two places: the "My Projects" dropdown in `_includes/header.html` and the listing in `projects/index.md`. Both loop over `site.pages`. To hide a project, prefix its directory with `_` (e.g. `projects/_muftp`).
- **Styling**: Bootstrap 2 (`css/bootstrap*.css`, `js/bootstrap.js`, jQuery 2.0.2) plus `css/main.css` and `css/syntax.css` (Rouge highlighting). Markdown is rendered with kramdown, so kramdown syntax such as `{::comment}...{:/comment}` appears in content.
- **Static files**: `downloads/` holds standalone static files (e.g. `memo.html`). `img/` and `images/` hold assets.
- **Leftover files**: `_index.html`, `index.md.back`, `_config.yml.save`, and the empty `about.md` are not active. The real About page is `about/index.md`.
