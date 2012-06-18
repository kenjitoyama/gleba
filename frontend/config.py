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
from argparse import ArgumentParser

arg_parser = ArgumentParser(description = 'Gleba frontend')

################################################################################
# Command line arguments
################################################################################

arg_parser.add_argument(
    '--serial_port',
    help = 'Serial port to read from.')

arg_parser.add_argument(
    '--django_http_url',
    default = 'http://localhost:8000/',
    help = 'Full http url to the root of the django backend.')

arg_parser.add_argument(
    '--username',
    help = 'Backend username (login).')

arg_parser.add_argument(
    '--password',
    help = 'Backend password.')

arg_parser.add_argument(
    '--weight_window_size',
    type = int,
    default = 100,
    help = 'Amount of measurements for a sliding window to achieve weight '
           'stability.')

arg_parser.add_argument(
    '--box_weight',
    type = float,
    default = 0.2,
    help = 'The actual weight of a box in Kg without contents.')

arg_parser.add_argument(
    '--window_width',
    type = float,
    default = 800.0,
    help = 'The width (in pixels) of the GUI window')

arg_parser.add_argument(
    '--window_height',
    type = float,
    default = 600.0,
    help = 'The height (in pixels) of the GUI window')

args = arg_parser.parse_args()

################################################################################
# GUI settings
################################################################################

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
