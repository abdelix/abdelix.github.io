---
layout: page
title: geo-traceroute
description: A traceroute that shows the geographical location of intermediate nodes.
importance: 3
category: archived
github: https://github.com/abdelix/geo-traceroute
---

> **Archived project.** This is one of my early student side projects (2014). It is kept here for reference and is no longer maintained.

A traceroute that gives you the geographical location of the intermediate nodes, based on their IP addresses.

#### Get the source

[GitHub repository](https://github.com/abdelix/geo-traceroute) · [Download as zip](https://github.com/abdelix/geo-traceroute/archive/master.zip)

#### Dependencies

- Standard Unix libraries
- [nxjson](https://bitbucket.org/yarosla/nxjson/overview)
- [curl](https://curl.se/)

#### Build and run

```sh
make
sudo ./geo-traceroute   # or grant the executable the required network capabilities
```
