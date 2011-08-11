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
    apps.report.views

Purpose:
   This package is used to provide dynamically generated reports from the data.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from apps.admin.models import *
from apps.utilities import date_range
import json

def get_date_from_request(request):
    """
    Retrieves and returns a tuple of dates from a http request.

    It raises an Exception or ValueError if an error occurs.
    """
    if ('startDate' in request.POST and 'endDate' in request.POST):
        if(request.POST['startDate'] == '' or request.POST['endDate'] == ''):
            raise Exception('empty date')
        else:
            start_date = datetime.datetime.strptime(
                request.POST['startDate'], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(
                request.POST['endDate'], "%Y-%m-%d").date()
        if start_date > end_date:
            raise Exception('start_date greater than end_date')
        return (start_date, end_date)
    else:
        return Exception('no startDate and endDate in POST request')

@login_required
def generate_report_all_picker(request):
    """
    Renders a report detailing all picking

    Builds a dictionary picker objects will be the key and (total picked, kpi)
    will be value.
    It uses two dates from the http POST, if they don't make sense the
    last 31 days are used.
    """
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    data = [] # [{id, first name, last name, total picked, kpi}]

    for picker in Picker.objects.all():
        total_time = picker.getTimeWorkedBetween(start_date, end_date)
        time_worked = (total_time.seconds)/3600.0
        total_picked = picker.getTotalPickedBetween(start_date, end_date)
        avg_init_weight = picker.getAvgInitWeightBetween(start_date,
                                                         end_date)
        total_kg_per_hour = (total_picked/time_worked
                             if (time_worked>0) else 0)
        data.append({'picker_id':    picker.id,
                     'first_name':   picker.firstName,
                     'last_name':    picker.lastName,
                     'total_picked': '{:.6f}'.format(total_picked),
                     'kghr':         '{:.6f}'.format(total_kg_per_hour),
                     'avg':          '{:.6f}'.format(avg_init_weight)})

    return render_to_response('report.html', {
        'user' :        request.user,
        'data' :        json.dumps(data),
        'startDate' :   start_date.strftime("%d-%m-%Y"),
        'endDate' :     end_date.strftime("%d-%m-%Y"),
        'report_type' : 'all_pickers',
    })

@login_required
def generate_report_picker(request, picker_id):
    """
    Renders the report page for a particular picker.

    Builds a list of dates, total picked and average per day.
    It expects jqPlot to properly build the graph.
    """
    picker_obj = get_object_or_404(Picker, pk = picker_id)
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime("%Y-%m-%d"),]
        tmp.append(picker_obj.getTotalPickedOn(date))
        hours_worked = picker_obj.getTimeWorkedOn(date).seconds / 3600.0
        avg = (tmp[1]/hours_worked) if hours_worked != 0 else 0.0
        tmp.append(avg)
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'picker' : picker_obj,
        'report_type' : 'picker',
        'jqplot_data': daily_totals,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def generate_report_room(request, room_id):
    """
    Renders the report page for a particular room.

    Builds a list of dates and total picked.
    It expects jqPlot to properly build the graph.
    """
    room_obj = get_object_or_404(Room, pk = room_id)
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime("%Y-%m-%d"),]
        tmp.append(room_obj.getTotalPickedOn(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'room' : room_obj,
        'report_type' : 'room',
        'jqplot_data': daily_totals,
    })

@login_required
def generate_report_flush(request, flush_id):
    """
    Renders the report page for a particular flush.

    Builds a list of dates and total picked.
    It expects jqPlot to properly build the graph.
    """
    flush_obj = get_object_or_404(Flush, pk = flush_id)
    start_date = flush_obj.startDate
    end_date = (flush_obj.endDate if flush_obj.endDate is not None
                                 else datetime.date.today())
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime("%Y-%m-%d"),]
        tmp.append(flush_obj.getTotalPickedOn(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'flush' : flush_obj,
        'report_type' : 'flush',
        'jqplot_data': daily_totals,
    })

@login_required
def generate_report_crop(request, crop_id):
    """
    Renders the report page for a particular crop.

    Builds a list of dates and total picked.
    It expects jqPlot to properly build the graph.
    """
    crop_obj = get_object_or_404(Crop, pk = crop_id)
    start_date = crop_obj.startDate
    end_date = (crop_obj.endDate if crop_obj.endDate is not None
                                 else datetime.date.today())
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime("%Y-%m-%d"),]
        tmp.append(crop_obj.getTotalPickedOn(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'crop' : crop_obj,
        'report_type' : 'crop',
        'jqplot_data': daily_totals,
    })

@login_required
def generate_report(request):
    """
    Renders the input page. The user selects the parameters for the report
    they require to be generated by submitting forms.
    """
    picker_list = Picker.objects.filter(active = True,
                                        discharged = False).order_by('id')
    room_list = Room.objects.all().order_by('number')
    context = {
        'report_type': 'default_page',
        'picker_list':  picker_list,
        'room_list':    room_list,
        'user' :        request.user
    }
    return render_to_response('report.html', context)
