"""
Copyright (C) 2010 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 
Copyright (C) 2011 Simon Dawson, Daniel Kenji Toyama

This file is part of Gleba 

Gleba is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Gleba is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Gleba.  If not, see <http://www.gnu.org/licenses/>.

Path: 
    frontend.config

Purpose:
    This file contains all the configuration for the Gleba frontend.
    It includes server settings and testing settings.
"""
from os import getcwd

# Serial Configuration
SERIAL_PORT = '/dev/pts/5'

# Django Configuration
#    Full http url to the root of the django backend
DJANGO_HTTP_URL = 'http://localhost:8000/'

# Backend username/password
BACKEND_USERNAME = 'kenji'
BACKEND_PASSWORD = 'k'

# Amount of measurements for a sliding window to achieve weight stability
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

# Picker, batch and variety formats
PICKER_BUTTON_FORMAT = '{picker_id}. {first_name} {last_name}'
BATCH_COMBO_FORMAT = 'Batch No. {batch_id} ({year}-{month}-{day}) Room {room_number}'
VARIETY_BUTTON_FORMAT = '{variety_name}\n[{min_weight} ~ {max_weight}]'

# sound files used for feedback.
# Default SOUND_DIRECTORY is the current working directory of config.py
SOUND_DIRECTORY = 'file://{0}/'.format(getcwd())
BUTTON_SOUND = SOUND_DIRECTORY + 'button.ogg'
GREEN_SOUND = SOUND_DIRECTORY + 'green.ogg'
SUCCESS_SOUND = SOUND_DIRECTORY + 'success.ogg'
