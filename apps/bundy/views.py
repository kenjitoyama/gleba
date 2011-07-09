from django.shortcuts import render_to_response, get_object_or_404
from django.shortcuts import redirect
from glebaAdmin.models import *

##### Bundy Clock handling #####
def bundy(request, picker_id = None):
    bundy_action = 'default_page'
    if picker_id == None: # display the keypad
        return render_to_response('bundy.html', {
            'bundy_action': bundy_action,
        })
    else: # signing in/off
        picker = get_object_or_404(Picker, pk = picker_id)
        flag = Bundy.objects.filter(picker = picker,
                                    timeOut__isnull = True).count()
        bundy_action = 'signoff' if flag else 'signin'
        if bundy_action == 'signin':
            if 'confirmed' in request.GET: # create a Bundy
                session = Bundy(picker = picker,
                                timeIn = datetime.datetime.now())
                session.save()
                return redirect(bundy)
        else: # signoff
            session = Bundy.objects.get(picker = picker_id,
                                        timeOut__isnull = True)
            if ('lunch' in request.GET and
                len(request.GET['lunch']) > 1):
                hadLunch = (str(request.GET['lunch']) == "True")
                session.timeOut = datetime.datetime.now()
                session.hadLunch = hadLunch
                session.save()
                return redirect(bundy)
        # display the confirmation request or lunch prompt
        return render_to_response('bundy.html', {
            'picker':       picker,
            'bundy_action': bundy_action,
        })
