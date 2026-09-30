# To-do

## Blog

- [ ] **Write the modal simulators comparison post.** The comparison itself is done; it only needs writing up for
      *Evanescently Coupled Ideas*. Plan: which simulators were compared, the test structures, a results table and
      the conclusions. If the data is available as CSV, it can be shown as interactive Plotly charts.

## Site

- [ ] **Track visitors and where they come from with Cloudflare Web Analytics.** It's free, needs no cookie banner,
      and shows visits, countries and referrers.
  1. At [dash.cloudflare.com](https://dash.cloudflare.com/), go to **Analytics & Logs → Web Analytics → Add a site**
     and enter `abdelix.com`. Pick the JavaScript-snippet option; DNS stays at IONOS.
  2. Copy the 32-character `token` from the snippet into `_config.yml`:
     ```yaml
     analytics:
       cloudflare: <token>
     ```
     The token is public (it appears in every page's source), so committing it is fine.
  3. Optional: add Google Search Console through `google_site_verification` in `_config.yml` to see which searches
     lead to the site.
