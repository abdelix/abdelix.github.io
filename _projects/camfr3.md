---
layout: page
title: camfr3
description: CAMFR, the eigenmode expansion solver from Ghent University, ported to Python 3.
importance: 1
category: current
github: https://github.com/abdelix/camfr3
---

**camfr3** is a Python 3 port of [CAMFR](http://camfr.sourceforge.net/) (CAvity Modelling FRamework), a full-vectorial
Maxwell solver for nanophotonics based on **eigenmode expansion (EME)** and perfectly matched layers.

## Original authors

CAMFR was written by **Peter Bienstman** at the Photonics Research Group, Department of Information Technology (INTEC),
**Ghent University**, Belgium, with contributions from:

- **Lieven Vanholme** (Ghent University): generalised eigenvalue solver for Bloch modes, general excitations,
  visualisation
- **Mihai Ibanescu** (MIT): multiring circular structures

The code was later maintained on GitHub by [Demis D. John](https://github.com/demisjohn/CAMFR).

The solver, its physics and its numerical methods are entirely their work. **My contribution is only the port to
Python 3** and the packaging needed to publish it on PyPI. The package is called `camfr3` because the PyPI name
`camfr` belongs to the original author; it is still imported as `import camfr`.

If you use it in published work, please cite the original paper:

> P. Bienstman and R. Baets, "Optical modelling of photonic crystals and VCSELs using eigenmode expansion and perfectly
> matched layers", _Optical and Quantum Electronics_ 33, 327–341 (2001).
> [doi:10.1023/A:1010882531238](https://doi.org/10.1023/A:1010882531238)

## Install and links

```sh
pip install camfr3
```

- **Documentation:** [abdelix.com/camfr3](https://abdelix.com/camfr3/)
- **Source code (Python 3 port):** [github.com/abdelix/camfr3](https://github.com/abdelix/camfr3)
- **Package:** [pypi.org/project/camfr3](https://pypi.org/project/camfr3/)
- **Original project:** [camfr.sourceforge.net](http://camfr.sourceforge.net/) ·
  [github.com/demisjohn/CAMFR](https://github.com/demisjohn/CAMFR)

CAMFR and camfr3 are released under the GNU General Public License, version 2.
