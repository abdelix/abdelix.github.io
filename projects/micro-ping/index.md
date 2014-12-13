---
layout: default-comments
title: "micro-ping"
category: 'projects'
description : A minimal implementation of the classical ping command.

---
## muSH or µSH
By Abdelfetah Hadij 
A Micro Unix SHell.



#### Features

* Works on any Unix-like system.
* Configurable interval between ping's (-i commandline option)
* Configurable number of pings to send (-c commandline option)
* Configurable pattern to send         (-p commandline option)
* Flood pinging 		         (-f commandline option)
* Play sound on every response         (-a commandline option)


#### Get the source

[Go to GitHub Repository](https://github.com/abdelix/micro-ping)
  
  
[Download git repository as zip](https://github.com/abdelix/micro-ping/archive/master.zip)

#### Dependencies

This program only depends on standard POSIX libraries (i.e. standard libraries present on every UNIX-like system).

#### Build

In a shell you must run in the main directory of the project :
	
	
	$ cd build/
	$ cmake
	$ make

#### Usage
In the same directory as before (build) you must run the shell as :

	./ping [-i interval] [-c count] [-p pattern] [-f] [-a] [-h]
	[-i interval] : interval between sent pings in seconds
	[-c count] Number of pings to send before exit. If not provided pings are continuously sent until the program is finished (CTRL-C)
	[-p pattern] The payload of each packet as an HEX string
	[-f] : enable flood pinging (use with caution)[-a] : play an sound on every response received.
	[-h] print this help

------------
    
Last time updated : {{site.time | date_to_string}}.


