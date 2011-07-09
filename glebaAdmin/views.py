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
