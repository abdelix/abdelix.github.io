---
layout: page
permalink: /patents/
title: patents
description: Granted patents and patent applications.
nav: true
nav_order: 2
---

<!-- _pages/patents.md -->
<!-- Generated from _bibliography/patents.bib, which bin/sync_orcid.py rebuilds from EPO OPS, ORCID and _bibliography/patents_manual.bib. -->

{% capture patents_list %}{% bibliography --file patents %}{% endcapture %}

<div class="publications">
{% if patents_list contains '<li' %}
{{ patents_list }}
{% else %}
<p>The patent list is being updated. It will appear here automatically once it is available on ORCID.</p>
{% endif %}
</div>

<!-- Unpublished application: keep the description generic until it is published (it will then be listed above automatically). -->

_A further patent application on chip-to-fibre interfaces is pending._
