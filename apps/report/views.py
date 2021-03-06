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
    apps.report.views

Purpose:
   This package is used to provide dynamically generated reports from the data.
"""
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from apps.admin.models import *
from apps.utilities import date_range

def get_date_from_request(request):
    """
    Retrieves and returns a tuple of dates from a http request.

    It raises an Exception or ValueError if an error occurs.
    """
    if ('start_date' in request.POST and 'end_date' in request.POST):
        if(request.POST['start_date'] == '' or request.POST['end_date'] == ''):
            raise Exception('empty date')
        else:
            start_date = datetime.datetime.strptime(
                request.POST['start_date'], '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(
                request.POST['end_date'], '%Y-%m-%d').date()
        if start_date > end_date:
            raise Exception('start_date greater than end_date')
        return (start_date, end_date)
    else:
        return Exception('no start_date and end_date in POST request')

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
        total_time = picker.get_time_worked(start_date, end_date)
        time_worked = total_time.seconds / 3600.0
        total_picked = picker.get_total_picked(start_date, end_date)
        avg_init_weight = picker.get_avg_init_weight(start_date, end_date)
        if time_worked > 0:
            total_kg_per_hour = total_picked / time_worked
        else:
            total_kg_per_hour = 0.0
        data.append({
            'picker_id':    picker.id,
            'first_name':   picker.first_name,
            'last_name':    picker.last_name,
            'total_picked': '{:.6f}'.format(total_picked),
            'kghr':         '{:.6f}'.format(total_kg_per_hour),
            'avg':          '{:.6f}'.format(avg_init_weight)
        })

    return render_to_response('report.html', {
        'report_type' : 'all_pickers',
        'data' :        json.dumps(data),
        'start_date' :  start_date.strftime('%Y-%m-%d'),
        'end_date' :    end_date.strftime('%Y-%m-%d'),
    })

@login_required
def generate_report_picker(request, picker_id):
    """
    Renders the report page for a particular picker.

    Builds a list of dates, total picked and average per day.
    It expects jqPlot to properly build the graph.
    """
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    picker_obj = get_object_or_404(Picker, pk = picker_id)
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime('%Y-%m-%d'),]
        tmp.append(picker_obj.get_total_picked(date))
        hours_worked = picker_obj.get_time_worked(date).seconds / 3600.0
        avg = (tmp[1]/hours_worked) if hours_worked != 0 else 0.0
        tmp.append(avg)
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'report_type' : 'picker',
        'picker' :      picker_obj,
        'jqplot_data':  daily_totals,
        'start_date':   start_date,
        'end_date':     end_date,
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
        tmp = [date.strftime('%Y-%m-%d'),]
        tmp.append(room_obj.get_total_picked(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'report_type' : 'room',
        'room' :        room_obj,
        'jqplot_data':  daily_totals,
    })

@login_required
def generate_report_flush(request, flush_id):
    """
    Renders the report page for a particular flush.

    Builds a list of dates and total picked.
    It expects jqPlot to properly build the graph.
    """
    flush_obj = get_object_or_404(Flush, pk = flush_id)
    start_date = flush_obj.start_date
    if flush_obj.end_date is not None:
        end_date = flush_obj.end_date
    else:
        end_date = datetime.date.today()
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime('%Y-%m-%d'),]
        tmp.append(flush_obj.get_total_picked(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'report_type' : 'flush',
        'flush' :       flush_obj,
        'jqplot_data':  daily_totals,
    })

@login_required
def generate_report_crop(request, crop_id):
    """
    Renders the report page for a particular crop.

    Builds a list of dates and total picked.
    It expects jqPlot to properly build the graph.
    """
    crop_obj = get_object_or_404(Crop, pk = crop_id)
    start_date = crop_obj.start_date
    if crop_obj.end_date is not None:
        end_date = crop_obj.end_date
    else:
        end_date = datetime.date.today()
    daily_totals = []
    for date in date_range(start_date, end_date):
        tmp = [date.strftime('%Y-%m-%d'),]
        tmp.append(crop_obj.get_total_picked(date))
        daily_totals.append(tmp)
    return render_to_response('report.html', {
        'report_type' : 'crop',
        'crop' :        crop_obj,
        'jqplot_data':  daily_totals,
    })

@login_required
def generate_report(request):
    """
    Renders the input page. The user selects the parameters for the report
    they require to be generated by submitting forms.
    """
    picker_list = Picker.objects.filter(
        active = True,
        discharged = False
    ).order_by('id')
    room_list = Room.objects.all().order_by('number')
    return render_to_response('report.html', {
        'report_type': 'default_page',
        'picker_list': picker_list,
        'room_list':   room_list,
    })

############
# AJAX calls
############

@login_required
def daily_totals(request, picker_id):
    picker = get_object_or_404(Picker, pk = picker_id)
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    boxes = (picker.get_daily_totals(start_date, end_date)
             .order_by('timestamp'))
    data = []
    for box in boxes:
        data.append({
            'initial_weight': box.initial_weight,
            'final_weight': box.initial_weight,
            'timestamp': box.timestamp.isoformat()
        })
    return HttpResponse(json.dumps(data), mimetype = 'application/json')

@login_required
def daily_hours(request, picker_id):
    picker = get_object_or_404(Picker, pk = picker_id)
    try:
        start_date, end_date = get_date_from_request(request)
    except Exception as exc:
        error_list = ['Got an exception: {}'.format(exc),]
        return render_to_response('error.html', {
            'error_list': error_list,
        })
    bundies = (picker.get_daily_hours(start_date, end_date)
               .order_by('time_in'))
    data = []
    for bundy in bundies:
        data.append({
            'time_in':   bundy.time_in.isoformat(),
            'time_out':  bundy.time_out.isoformat(),
            'had_lunch': bundy.had_lunch
        })
    return HttpResponse(json.dumps(data), mimetype = 'application/json')

@login_required
def picker_report_page(request, picker_id):
    picker = get_object_or_404(Picker, pk = picker_id)
    return render_to_response('picker_report.html')
