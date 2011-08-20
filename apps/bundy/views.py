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
    apps.bundy.views

Purpose:
   This package is used to provide user interaction with the Bundy objects
   allowing pickers to be sign in and out for the days work.
"""
from django.shortcuts import render_to_response, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from apps.admin.models import *

@login_required
def bundy(request, picker_id = None):
    """
       Signs picker with id picker_id on or off if no picker_id the form
       to enter a picker_id is rendered 
    """
    print(picker_id)
    bundy_action = 'default_page'
    if picker_id == None: # display the keypad
        return render_to_response('bundy.html', {
            'bundy_action': bundy_action,
        })
    else: # signing in/off
        picker = get_object_or_404(Picker, pk = picker_id)
        flag = Bundy.objects.filter(picker = picker,
                                    time_out__isnull = True).count()
        bundy_action = 'signoff' if flag else 'signin'
        if bundy_action == 'signin':
            if 'confirmed' in request.GET: # create a Bundy
                session = Bundy(picker = picker,
                                time_in = datetime.datetime.now())
                session.save()
                return redirect(bundy)
        else: # signoff
            session = Bundy.objects.get(picker = picker_id,
                                        time_out__isnull = True)
            if ('lunch' in request.GET and
                len(request.GET['lunch']) > 1):
                had_lunch = (str(request.GET['lunch']) == "True")
                session.time_out = datetime.datetime.now()
                session.had_lunch = had_lunch
                session.save()
                return redirect(bundy)
        # display the confirmation request or lunch prompt
        return render_to_response('bundy.html', {
            'picker':       picker,
            'bundy_action': bundy_action,
        })
