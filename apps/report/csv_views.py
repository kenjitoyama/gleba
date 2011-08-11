"""
Copyright (C) 2010-2011 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 

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
    gleba.report.csv_views

Purpose:
    This package is used to build and deliver reports on pickers time at work.
"""
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from glebaAdmin.models import *
import datetime
import csv
from django.http import HttpResponse

def write_list_to_file(file_handle, export_list):
    """
    Writes a list of lines (export_list) to a file (file_handle).
    """
    csv.writer(file_handle).writerows(export_list)

def build_export_list(period = 31): #period in days
    """
    Builds a list of Pickers and the total time they've worked.
    """
    header = ("Name", "Hours worked")
    export_list = [header]
    employed_pickers = Picker.objects.filter(discharged = False)
    for picker in employed_pickers:
        days_worked = Bundy.objects.filter(
            timeIn__gte = (datetime.date.today() -
                           datetime.timedelta(days = period)),
            picker = picker,
            timeOut__isnull = False
        )
        total_hours_worked = 0
        for bundy in days_worked:
            total_hours_worked += (bundy.timeOut-bundy.timeIn).seconds/3600.0
        export_list.append(('{} {}'.format(picker.firstName, picker.lastName),
                            total_hours_worked))
    return export_list

def build_export_list_range(start_date, end_date = datetime.date.today()):
    """
    Builds a list of Pickers and the total time they've worked during a
    date range.
    """
    header = ("Name", "Hours worked")
    export_list = [header]
    employed_pickers = Picker.objects.filter(discharged = False)
    for picker in employed_pickers:
        days_worked = Bundy.objects.filter(
            timeIn__gte = start_date,
            timeIn__lte = end_date,
            picker = picker,
            timeOut__isnull = False
        )
        total_hours_worked = 0
        for bundy in days_worked:
            total_hours_worked += (bundy.timeOut-bundy.timeIn).seconds/3600.0
        export_list.append(('{} {}'.format(picker.firstName, picker.lastName),
                            total_hours_worked))
    return export_list

@login_required
def generate_csv(request):
    """
    Generates a CSV file for all employed Pickers.

    Returns a simple file with the name of each Picker and the total amount
    of hours worked according to the Bundy records.
    """
    fname = 'timesheet_{}.csv'.format(datetime.date.today().isoformat())
    response = HttpResponse(mimetype = 'text/csv')
    response['Content-Disposition'] = 'attachment; filename={0}'.format(fname)
    write_list_to_file(response, build_export_list() )
    return response

@login_required
def generate_csv_range(request):
    """
    Generates a CSV file for all employed Pickers over a date range.

    Returns a simple file with the name of each Picker and the total amount
    """
    if 'endDate' in request.POST and 'startDate' in request.POST:
        if request.POST['endDate'] == '': # blank endDate
            end_date = datetime.date.today().isoformat()
        else:
            try:
                end_date = datetime.datetime.strptime(
                    request.POST['endDate'], '%Y-%m-%d')
            except ValueError:
                return render_to_response('csv.html', {
                    'date_error': 'Incorrect format for the end date .',
                    'start_date': request.POST['startDate'],
                    'end_date':   request.POST['endDate']
                })
        if request.POST['startDate'] == '': # blank startDate
            start_date = (datetime.date.today() -
                          datetime.timedelta(days = 31)).isoformat()
        else:
            try:
                start_date = datetime.datetime.strptime(
                    request.POST['startDate'], '%Y-%m-%d')
            except ValueError:
                return render_to_response('csv.html', {
                    'date_error': 'Incorrect format for the start date .',
                })
        fname = 'timesheet_{}.csv'.format(datetime.date.today().isoformat())
        response = HttpResponse(mimetype = 'text/csv')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(fname)
        write_list_to_file(response, build_export_list_range(start_date, end_date))
        return response
    else:
        return render_to_response('csv.html', {})
