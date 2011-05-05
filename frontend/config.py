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
