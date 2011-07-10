from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from glebaAdmin.models import *
from glebaAdmin.views import date_range
import json

def getDateFromRequest(request):
    """
    Retrieves and returns a tuple of dates from a http request.

    If request does not contain a valid startDate, 31 days in the past from
    today is used.
    If request does not contain a valid endDate, today is used.
    """
    if ('startDate' in request.POST and
        'endDate' in request.POST and
        request.POST['startDate'] != '' and
        request.POST['endDate'] != ''):
        start_date = datetime.datetime.strptime(
            request.POST['startDate'], "%d-%m-%Y").date()
        end_date = datetime.datetime.strptime(
            request.POST['endDate'], "%d-%m-%Y").date()
    elif ('startDate' in request.GET and
          'endDate' in request.GET and
          request.GET['startDate'] != '' and
          request.GET['endDate'] != ''):
        start_date = datetime.datetime.strptime(
            request.GET['startDate'], "%d-%m-%Y").date()
        end_date = datetime.datetime.strptime(
            request.GET['endDate'], "%d-%m-%Y").date()
    else:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days = 31)

    return ((start_date, end_date) if start_date < end_date
                                  else (end_date, start_date))

@login_required
def generate_report_all_picker(request):
    """
    Renders a report detailing all picking

    Builds a dictionary picker objects will be the key and (total picked, kpi)
    will be value.
    It uses two dates from the http POST, if they don't make sense the
    last 31 days are used.
    """
    start_date, end_date = getDateFromRequest(request)
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
    start_date, end_date = getDateFromRequest(request)
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
    start_date, end_date = getDateFromRequest(request)
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
    return render_to_response('report.html', {
        'report_type': 'default_page',
        'picker_list':  picker_list,
        'room_list':    room_list,
        'user' :        request.user
    })

