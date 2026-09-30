---
layout: page
permalink: /patents/
title: patents
description: Granted patents and patent applications.
nav: true
nav_order: 2
---

This list is updated automatically every week from my [ORCID record](https://orcid.org/0000-0002-8363-7423).

<!-- _pages/patents.md -->
<!-- Generated from _bibliography/patents.bib, which bin/sync_orcid.py rebuilds from ORCID works of type "patent". -->

{% capture patents_list %}{% bibliography --file patents %}{% endcapture %}

<div class="publications">
{% if patents_list contains '<li' %}
{{ patents_list }}
{% else %}
<p>The patent list is being updated. It will appear here automatically once it is available on ORCID.</p>
{% endif %}
</div>
