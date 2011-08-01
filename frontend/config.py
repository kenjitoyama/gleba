#!/usr/bin/python
"""
This file contains all the configuration for the Gleba frontend.

It includes server settings and testing settings.
Requirements for testing:
On GNU/Linux:
- socat (www.dest-unreach.org/socat/)
"""

# - Serial Configuration
ser_port = '/dev/pts/5'

# - Django Configuration
#    Full http path to the root of the django web app 
django_http_path = 'http://localhost:8000/'

WEIGHT_WINDOW_SIZE = 100

# BOX_WEIGHT represents the actual weight of a box in Kg without contents.
BOX_WEIGHT = 0.2

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
WEIGHT_STYLE = '<span foreground="#ffffff" font="Calibri 30">{0:.3f}</span>'
OFFSET_STYLE = '<span foreground="#ffffff" font="Calibri 30">{0:+.3f}</span>'
NA_MARKUP = '<span foreground="#000000" font_desc="Calibri 30">N/A</span>'

WHITE_COLOR = (0xffff, 0xffff, 0xffff)
BLACK_COLOR = (0x0000, 0x0000, 0x0000)
RED_COLOR   = (0xffff, 0x0000, 0x0000)
GREEN_COLOR = (0x0000, 0xffff, 0x0000)
BLUE_COLOR  = (0x0000, 0x0000, 0xffff)
