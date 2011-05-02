#!/usr/bin/python
"""
This file contains all the configuration for the Gleba frontend.

It includes server settings and testing settings.
Requirements for testing:
On GNU/Linux:
- socat (www.dest-unreach.org/socat/)
"""

SOCAT_EXECUTABLE = '/usr/bin/socat'

SOCAT_ARGS = '-d -d -u pty,raw,echo=0 pty,raw,echo=0'
