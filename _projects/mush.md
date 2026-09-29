---
layout: page
title: muSH / µSH
description: A micro Unix shell.
importance: 1
category: archived
github: https://github.com/abdelix/mush
---

> **Archived project.** This is one of my early student side projects (2013). It is kept here for reference and is no longer maintained.

A micro Unix shell.

#### Features

- Works on any Unix-like system.
- Executes commands in the foreground and in the background.
- Built-in `cd` command.
- Persistent history and history navigation.
- Path completion with tab.
- Pipelines.

#### Get the source

[GitHub repository](https://github.com/abdelix/mush) · [Download as zip](https://github.com/abdelix/mush/archive/master.zip)

#### Dependencies

Standard POSIX libraries and [GNU Readline](https://tiswww.case.edu/php/chet/readline/rltop.html).

#### Build and run

```sh
cd build/
cmake
make
./mush
```
