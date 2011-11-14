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
    apps.weigh.views

Purpose:
    This package is used to provide a web api to allow data creation and 
    retrieval.
"""
import json
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import Context
from django.template.loader import get_template
from django.http import HttpResponse
from apps.admin.models import Picker, Batch, Variety, Box

################################################################################
# Add data to the database
################################################################################
@login_required
def add_boxes(request):
    """
    Processes a batch of boxes in one go.

    The request must be a POST request with a parameter 'boxes'
    that contains a list of boxes in a dictionary format as follows:
        {'picker': picker_id,
          'batch':  batch_id,
          'variety': variety_id,
          'initial_weight': initial_weight,
          'final_weight': final_weight,
          'timestamp': timestamp}
    The processing must be correct for ALL the boxes, otherwise
    nothing will be added to the database (i.e. everything or nothing).
    """
    if (request.method == 'POST' and
        'boxes' in request.POST):
        boxes_to_save = []
        boxes = json.loads(request.POST.get('boxes'))
        for box in boxes:
            if ('picker'         in box and
                'batch'          in box and
                'variety'        in box and
                'initial_weight' in box and
                'final_weight'   in box and
                'timestamp'      in box):
                picker_id          = box['picker']
                batch_id           = box['batch']
                variety_id         = box['variety']
                initial_weight_tmp = box['initial_weight']
                final_weight_tmp   = box['final_weight']
                timestamp_tmp      = box['timestamp']

                picker_obj = get_object_or_404(Picker, pk = picker_id)
                batch_obj = get_object_or_404(Batch, pk = batch_id)
                variety_obj = get_object_or_404(Variety, pk = variety_id)
                boxes_to_save.append(Box(
                    initial_weight = float(initial_weight_tmp),
                    final_weight = float(final_weight_tmp),
                    timestamp = timestamp_tmp,
                    variety = variety_obj,
                    picker = picker_obj,
                    batch = batch_obj,
                ))
            else: # something missing in this box
                error_list = ['Not enough parameters in box {}.'.format(i)]
                return render_to_response('error.html', {
                    'error_list' : error_list
                })
        # all boxes were processed, just save all of them
        for box in boxes_to_save:
            box.save()
        return render_to_response('success.html')

################################################################################
# Retrieve data from the database
################################################################################
@login_required
def get_picker_list(request, result_format):
    """
    Returns the list of Pickers that are active and not discharged.

    The result is either an XML or JSON file depending on result_format.
    """
    picker_list = (Picker.objects.filter(active = True, discharged = False)
                                .order_by('id'))
    if result_format == 'xml':
        templ = get_template('picker_list.xml')
        context = Context({'picker_list': picker_list,})
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [{
            'id': picker.id,
            'first_name': picker.first_name,
            'last_name': picker.last_name
        } for picker in picker_list]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {
            'error_list' : ['URL Pattern Matched failed to parse (xml|json)',]
        })

@login_required
def get_batch_list(request, result_format):
    """
    Returns the list of Batches that are not finished yet
    (i.e. end_date is null).

    The result is either an XML or JSON file depending on result_format.
    """
    batch_list = (Batch.objects.filter(flush__end_date__isnull = True)
                              .order_by('id'))
    if result_format == 'xml':
        templ = get_template('batch_list.xml')
        context = Context({'batch_list': batch_list,})
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [{
            'id': batch.id,
            'flush_number': batch.flush.flush_no,
            'room_number': batch.flush.crop.room.number,
            'date': {
                'day': batch.date.day,
                'month': batch.date.month,
                'year': batch.date.year,
            }
        } for batch in batch_list]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {
            'error_list' : ['URL Pattern Matched failed to parse (xml|json)',]
        })

@login_required
def get_variety_list(request, result_format):
    """
    Returns the list of Varieties that are still being used.

    The result is either an XML or JSON file depending on result_format.
    """
    variety_list = Variety.objects.filter(active = True).order_by('name')
    if result_format == 'xml':
        templ = get_template('variety_list.xml')
        context = Context({'variety_list': variety_list,}) 
        return HttpResponse(templ.render(context), mimetype = 'text/xml')
    elif result_format == 'json':
        data = [{
            'id': variety.id,
            'name': variety.name,
            'minimum_weight': variety.minimum_weight,
            'tolerance': variety.tolerance
        } for variety in variety_list]
        return HttpResponse(json.dumps(data), mimetype = 'application/json')
    else:
        return render_to_response('error.html', {
            'error_list' : ['URL Pattern Matched failed to parse (xml|json)',]
        })

