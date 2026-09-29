---
layout: page
title: micro-ping
description: A minimal implementation of the classic ping command.
importance: 2
category: archived
github: https://github.com/abdelix/micro-ping
---

> **Archived project.** This is one of my early student side projects (2014). It is kept here for reference and is no longer maintained.

A minimal implementation of the classic `ping` command.

#### Features

- Works on any Unix-like system.
- Configurable interval between pings (`-i`) and number of pings (`-c`).
- Configurable payload pattern (`-p`).
- Flood pinging (`-f`).
- Sound on every response (`-a`).

#### Get the source

[GitHub repository](https://github.com/abdelix/micro-ping) · [Download as zip](https://github.com/abdelix/micro-ping/archive/master.zip)

Only standard POSIX libraries are required.

#### Build and usage

```sh
cd build/
cmake
make
./ping [-i interval] [-c count] [-p pattern] [-f] [-a] [-h]
```

| Option        | Meaning                                                                  |
| ------------- | ------------------------------------------------------------------------ |
| `-i interval` | Interval between pings in seconds                                        |
| `-c count`    | Number of pings to send before exiting (default: until Ctrl-C)           |
| `-p pattern`  | Payload of each packet as a hex string                                   |
| `-f`          | Flood pinging (use with caution)                                         |
| `-a`          | Play a sound on every response received                                  |
| `-h`          | Print help                                                               |
