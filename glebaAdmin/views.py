from django.shortcuts import render_to_response, get_object_or_404
from django.shortcuts import redirect
from glebaAdmin.models import *
from django.contrib.auth.decorators import login_required
import csv
import datetime
import json

# Kenji TODO: Move this 'constant' to another file for easier customization
CSV_OUTPUT_DIRECTORY = ('/home/kenji/django-projects/gleba/glebaAdmin/' +
                        'static/media/csv/')

################# General Utily Functions #################
def last_month():
    """
    Returns a list of the last 31 days including today
    """
    return [datetime.date.today() - datetime.timedelta(days = i)
            for i in range(31)]

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

################# Frontend Communications #################
def addBox(request):
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
        mushroom = get_object_or_404(Mushroom, pk = content_variety_id)
        batch_obj = get_object_or_404(Batch, pk = batch_id)
        box = Box(initialWeight = float(initial_weight_tmp),
                  finalWeight = float(final_weight_tmp),
                  timestamp = timestamp_tmp,
                  contentVariety = mushroom,
                  picker = picker_obj,
                  batch = batch_obj,
        )
        box.save()
        return render_to_response('success.html')
    else:
        error_list = ['Not enough parameters']
        return render_to_response('error.html', {'error_list' : error_list})

def getPickerList(request):
    """
    Returns the list of Pickers that are active and not discharged.

    The result is a Django QuerySet.
    """
    picker_list = Picker.objects.filter(active = True, discharged = False)\
                                .order_by('id')
    return render_to_response('pickerList.html', {
        'picker_list' : picker_list,
    })

def getPickerListXML(request):
    """
    Returns the list of Pickers that are active and not discharged.

    The result is given in an XML format.
    """
    picker_list = Picker.objects.filter(active = True, discharged = False)\
                                .order_by('id')
    return render_to_response('pickerList.xml', {
        'picker_list' : picker_list,
    })

def getBatchList(request):
    """
    Returns the list of Batches that are not finished yet
    (i.e. endDate is null).

    The result is a Django QuerySet.
    """
    batch_list = Batch.objects.filter(flush__endDate__isnull = True)\
                              .order_by('id')
    return render_to_response('batchList.html', {
        'batch_list' : batch_list,
    })

def getBatchListXML(request):
    """
    Returns the list of Batches that are not finished yet
    (i.e. endDate is null).

    The result is given in an XML format.
    """
    batch_list = Batch.objects.filter(flush__endDate__isnull = True)\
                              .order_by('id')
    return render_to_response('batchList.xml', {
        'batch_list' : batch_list,
    })

def getVarietyList(request):
    """
    Returns the list of Varieties that are still being used.

    The result is a Django QuerySet.
    """
    variety_list = Mushroom.objects.filter(active = True).order_by('variety')
    return render_to_response('varietyList.html', {
        'variety_list' : variety_list,
    })

def getVarietyListXML(request):
    """
    Returns the list of Varieties that are still being used.

    The result is given in an XML format.
    """
    variety_list = Mushroom.objects.filter(active = True).order_by('variety')
    return render_to_response('varietyList.xml', {
        'variety_list' : variety_list,
    })

############### Report Generation ############### 

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
    
#=== Reporting on pickers with a sortable table ===
# NOTE working on this
"""class PickingRateTable(tables.ModelTable):  
    "
    http://blog.elsdoerfer.name/2008/07/09/django-tables-a-queryset-renderer/

    Attempting to create a table for the pickers that is sortable by names
    or rates.

    This is work in progress.
    "
    cFirstName = tables.Column(name='First Name' data='firstName')  
    cLastName = tables.Column(name='Last Name' data='Last Name')  
    cTotalPicked = tables.Column(name='Total Picked')  
    cTotalPickedPerTime = tables.Column(name='Total Picked per Hour')  
    class Meta:  
        model = Picker"""

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

# NOTE: Working from here downward refactoring

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

##### CSV export handling #####
def write_list_to_file(filename, export_list):
    """
    Writes a list of lines (export_list) to a file (filename).
    """
    export_file = open(filename, "wb")
    export_writer = csv.writer(export_file)
    export_writer.writerows(export_list)
    export_file.close()

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
                           datetime.timedelta(days=period)),
            picker = picker,
            timeOut__isnull=False
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
    employed_pickers = Picker.objects.filter(discharged=False)
    for picker in employed_pickers:
        days_worked = Bundy.objects.filter(
            timeIn__gte = start_date,
            timeIn__lte = end_date,
            picker = picker,
            timeOut__isnull=False
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
    fpath = CSV_OUTPUT_DIRECTORY
    fname = 'timesheet_{}.csv'.format(datetime.date.today().isoformat())
    write_list_to_file(fpath + fname, build_export_list() )
    return render_to_response('csv.html', {
        'csvfile' : '/static/media/csv/' + fname,
        'csvfilename' : fname,
    })

@login_required
def generate_csv_range(request):
    """
    Generates a CSV file for all employed Pickers over a date range.

    Returns a simple file with the name of each Picker and the total amount
    """
    end_date = None
    if 'endDate' in request.POST:
        end_date = datetime.datetime.strptime(
            request.POST['endDate'], "%d-%m-%Y")
    if 'startDate' in request.POST:
        start_date = datetime.datetime.strptime(
            request.POST['startDate'], "%d-%m-%Y")
        fpath = CSV_OUTPUT_DIRECTORY
        fname = 'timesheet_{}.csv'.format(datetime.date.today().isoformat())
        if end_date is None:
            write_list_to_file(fpath + fname,
                               build_export_list_range(start_date))
        else:
            write_list_to_file(fpath + fname,
                               build_export_list_range(start_date, end_date))
        return render_to_response('csv.html', {
            'csvfile' : '/static/media/csv/' + fname,
            'csvfilename' : fname,
        })
    else:
        return render_to_response('csv.html', {})
