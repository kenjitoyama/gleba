"""
Copyright (C) 2010-2011 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 

 Path: 
   gleba.weigh.views

 Purpose:
   This package is used to provide a web api to allow data creation and 
   retrieval.

    This file is part of Gleba 

    This program file is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

 Author:
    Simon Dawson
    Daniel Kenji Toyama
"""

from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.http import HttpResponse
from glebaAdmin.models import *
import json

"""
- Create data within the database
"""

def add_box(request):
    """
       Creates a box object. Requires picker, contentVariety, batch, initialWeight,
       finalWeight and timestamp to be in the request header.
    """
    if ('picker'         in request.GET and
        'contentVariety' in request.GET and
        'batch'          in request.GET and
        'initialWeight'  in request.GET and
        'finalWeight'    in request.GET and
        'timestamp'      in request.GET):
        picker_id          = request.GET['picker']
        content_variety_id = request.GET['contentVariety']
        batch_id           = request.GET['batch']
        initial_weight_tmp = request.GET['initialWeight']
        final_weight_tmp   = request.GET['finalWeight']
        timestamp_tmp      = request.GET['timestamp']

        picker_obj = get_object_or_404(Picker, pk = picker_id)
        variety = get_object_or_404(Variety, pk = content_variety_id)
        batch_obj = get_object_or_404(Batch, pk = batch_id)
        box = Box(initialWeight = float(initial_weight_tmp),
                  finalWeight = float(final_weight_tmp),
                  timestamp = timestamp_tmp,
                  contentVariety = variety,
                  picker = picker_obj,
                  batch = batch_obj,
        )
        box.save()
        return render_to_response('success.html')
    else:
        error_list = ['Not enough parameters']
        return render_to_response('error.html', {'error_list' : error_list})

"""
- Retrieve data from within the database
""" 
def get_picker_list(request,result_format):
    """
    Returns the list of Pickers that are active and not discharged.

    The result is a Django QuerySet.
    """
    picker_list = Picker.objects.filter(active = True, discharged = False)\
                                .order_by('id')
    if result_format == 'xml':
        templ = get_template('pickerList.xml')
        context = Context({'picker_list': picker_list,})
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [{
                    'id': picker.id,
                    'first_name': picker.firstName,
                    'last_name': picker.lastName
                }
                for picker in picker_list ]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {'error_list' : ['URL Pattern Matched failed to parse (xml|json)']})

def get_batch_list(request, result_format):
    """
    Returns the list of Batches that are not finished yet
    (i.e. endDate is null).

    The result is a Django QuerySet.
    """
    batch_list = Batch.objects.filter(flush__endDate__isnull = True)\
                              .order_by('id')
    if result_format == 'xml':
        templ = get_template('batchList.xml')
        context = Context({'batch_list': batch_list,})
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [
            {
                'id': batch.id,
                'flush_number': batch.flush.flushNo,
                'room_number': batch.flush.crop.room.number,
                'date': {
                    'day': batch.date.day,
                    'month': batch.date.month,
                    'year': batch.date.year,
                }
            }
            for batch in batch_list ]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {'error_list' : ['URL Pattern Matched failed to parse (xml|json)']})

def get_variety_list(request):
    """
    Returns the list of Varieties that are still being used.

    The result is a Django QuerySet.
    """
    variety_list = Variety.objects.filter(active = True).order_by('name')
    if result_format == 'xml':
        templ = get_template('varietyList.xml')
        context = Context({'variety_list': variety_list,}) 
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [
            { 
                'id': variety.id,
                'name': variety.name,
                'ideal_weight': variety.idealWeight,
                'tolerance': variety.tolerance
            }
            for variety in variety_list ]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {'error_list' : ['URL Pattern Matched failed to parse (xml|json)']})

