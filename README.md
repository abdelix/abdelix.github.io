# abdelix.com

Personal website of **Abdelfettah Hadij-ElHouati**, photonic design engineer with a PhD in integrated photonics.
The site has a short bio, a CV, publications, patents, archived side projects and a blog.

It is built with [Jekyll](https://jekyllrb.com/) and the [al-folio](https://github.com/alshedivat/al-folio) theme,
and hosted on GitHub Pages.

## Local preview

```sh
bundle install
bundle exec jekyll serve   # http://localhost:4000/
```

Or, without a local Ruby setup: `docker compose up` (serves on http://localhost:8080/).

## Publications and patents

Both lists are generated from my [ORCID record](https://orcid.org/0000-0002-8363-7423):

```sh
python3 bin/sync_orcid.py
```

The **Sync publications from ORCID** GitHub Action runs this every Monday. When anything changed, it commits the updated
`_bibliography/*.bib` files and redeploys the site. Items that are not on ORCID can be added to
`_bibliography/manual.bib`.

## Deployment

Pushing to `master` runs the **Deploy site** workflow, which builds the site and publishes it to the `gh-pages` branch.
In the repository settings, *Pages → Build and deployment* must use **Deploy from a branch: `gh-pages` / root**.

## License

Site content © Abdelfettah Hadij-ElHouati. The al-folio template is MIT-licensed (see `LICENSE`).
