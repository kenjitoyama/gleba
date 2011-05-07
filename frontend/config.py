#!/usr/bin/python
"""
This file contains all the configuration for the Gleba frontend.

It includes server settings and testing settings.
Requirements for testing:
On GNU/Linux:
- socat (www.dest-unreach.org/socat/)
"""

# - Serial Configuration
#ser_port=1#"/dev/ttyS0"
ser_port = '/dev/pts/7'

# - Django Configuration
#    Full http path to the root of the django web app 
#         Change before deployment
django_http_path = 'http://localhost:8000/'

WEIGHT_WINDOW_SIZE = 100

################################################################################
# GUI settings
################################################################################

# Window size
WINDOW_WIDTH  = 800.0
WINDOW_HEIGHT = 600.0

# Number of Picker columns
PICKER_COLS = 3

# Number of Variety columns
VARIETY_COLS = 2

# Status appearance (don't change the stuff inside the curly brackets}
STATUS_STYLE = '<span foreground="#000000" font="Calibri 30">{text}</span>'
WEIGHT_STYLE = '<span foreground="#ffffff" font="Calibri 30">{0:.3}</span>'
OFFSET_STYLE = '<span foreground="#ffffff" font="Calibri 30">{0:+.3}</span>'
NA_MARKUP = '<span foreground="#000000" font_desc="Calibri 30">N/A</span>'
