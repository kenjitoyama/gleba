"""
Copyright (C) Simon Dawson, Kenji Toyama, Meryl Baquiran, Chris Ellis 2010-2011
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

Author(s):
    Simon Dawson
    Daniel Kenji Toyama

Path: 
    apps.utilities

Purpose:
    This file contains some utility functions used by other parts
    of Gleba.
"""
import datetime

def date_range(start_date, end_date):
    """
    Returns a list of the days between startDate and endDate inclusive.
    """
    date_list = []
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    while start_date <= end_date:
        date_list.append(start_date)
        start_date += datetime.timedelta(days = 1)
    return date_list
