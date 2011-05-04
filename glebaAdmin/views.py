from django.shortcuts import render_to_response
from gleba.glebaAdmin.models import Box
from gleba.glebaAdmin.models import Batch
from gleba.glebaAdmin.models import Bundy 
from gleba.glebaAdmin.models import Crop 
from gleba.glebaAdmin.models import Flush
from gleba.glebaAdmin.models import Mushroom
from gleba.glebaAdmin.models import Picker
from gleba.glebaAdmin.models import Room
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from time import sleep
import csv
import datetime
import Gnuplot
from django.db.models import Avg, Sum, Min, Max
"import django_tables as tables "

# TODO: Move this 'constant' to another file for easier customization
GRAPHS_OUTPUT_DIRECTORY = '/home/kenji/django-projects/gleba/glebaAdmin/static/media/graphs/'

################# General Utily Functions #################
def lastMonth():
    """ Returns a list of the last 31 days including today """
    return [datetime.date.today() - datetime.timedelta(days=i) for i in range(31)]

def dateRange(startDate, endDate):
    """ Returns a list of the days between startDate and endDate inclusive. """
    l=[]
    if startDate>endDate:
        startDate,endDate=endDate,startDate
    while startDate<=endDate:
        l.append(startDate)
        startDate+=datetime.timedelta(days=1)
    return l

################# Frontend Communications #################
def addBox(request):
    if ('picker' in request.GET and
        'initialWeight' in request.GET and
        'finalWeight' in request.GET and
        'timestamp' in request.GET and
        'contentVariety' in request.GET and
        'batch' in request.GET):
        p  = request.GET['picker']
        iw = request.GET['initialWeight']
        fw = request.GET['finalWeight']
        ts = request.GET['timestamp']
        cv = request.GET['contentVariety']
        b  = request.GET['batch']
        try:
            picker_ = Picker.objects.get(id=p)
            mushroom = Mushroom.objects.get(id=cv)
            batch_ = Batch.objects.get(id=b)
            box = Box(
                initialWeight = float(iw),
                finalWeight = float(fw),
                timestamp = ts,
                contentVariety = mushroom,
                picker = picker_,
                batch = batch_,
            )
            box.save()
        except Exception as e:
            return render_to_response('error.html', {'error_list' : e})
        return render_to_response('index.html')
    else:
        error_list = ['Not enough parameters']
        return render_to_response('error.html', {'error_list' : error_list})

def getPickerList(request):
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    return render_to_response(
        'pickerList.html', {
            'picker_list' : picker_list,
        }
    )

def getPickerListXML(request):
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    return render_to_response(
        'pickerList.xml', {
            'picker_list' : picker_list,
        }
    )

def getBatchList(request):
    batch_list = Batch.objects.filter(flush__endDate__isnull=True).order_by('id')
    return render_to_response(
        'batchList.html', {
            'batch_list' : batch_list,
        }
    )

def getBatchListXML(request):
    batch_list = Batch.objects.filter(flush__endDate__isnull=True).order_by('id')
    return render_to_response(
        'batchList.xml', {
            'batch_list' : batch_list,
        }
    )

def getVarietyList(request):
    variety_list = Mushroom.objects.filter(active=True).order_by('variety')
    return render_to_response(
        'varietyList.html', {
            'variety_list' : variety_list,
        }
    )

def getVarietyListXML(request):
    variety_list = Mushroom.objects.filter(active=True).order_by('variety')
    return render_to_response(
        'varietyList.xml', {
            'variety_list' : variety_list,
        }
    )


############### Report Generation ############### 

def setupGnuPlot(graphFile,
                 startDate=datetime.date.today()-datetime.timedelta(days=31),
                 endDate=datetime.date.today()):
    """ Given a filename, it returns a new gnuploter.
    
        If startDate is not given, 31 days in the past from today is used.
        If endDate is not given, today is used."""
    g = Gnuplot.Gnuplot()
    g('set terminal png size 640,480')
    g("set output '{directory}{filename}'".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = graphFile
    ))
    g('set style fill solid 1.00 border -1')
    g('set style histogram cluster gap 1')
    g("set xtics ("+"".join(['"'+d.strftime("%Y-%m-%d")+'"'+str(i)+',' for i,d in enumerate(dateRange(startDate,endDate)) if (i%5==0)])[:-1]+")")
    g("set xtics rotate by -60")
    g("unset key")
    return g   

def getDateFromRequest(request):
    """ 
    Retrieves and returns a tuple of dates from a http request.

        If request does not contain a valid startDate, 31 days in the past from today is used.
        If request does not contain a valid endDate, today is used.
    """
    try: 
        if 'startDate' in request.POST and 'endDate' in request.POST:
            startDate = datetime.datetime.strptime(request.POST['startDate'], "%d-%m-%Y").date()
            endDate = datetime.datetime.strptime(request.POST['endDate'], "%d-%m-%Y").date()
        elif 'startDate' in request.GET and 'endDate' in request.GET:  
            startDate = datetime.datetime.strptime(request.GET['startDate'], "%d-%m-%Y").date()
            endDate = datetime.datetime.strptime(request.GET['endDate'], "%d-%m-%Y").date()
    except: 
        endDate = datetime.date.today()
        startDate = endDate - datetime.timedelta(days=31)
            
    return (startDate, endDate) if startDate>endDate else (endDate,startDate)
    
#=== Reporting on pickers with a sortable table ===
# NOTE working on this
"""class PickingRateTable(tables.ModelTable):  
    "
        http://blog.elsdoerfer.name/2008/07/09/django-tables-a-queryset-renderer/

        Attempting to create a table for the pickers that is sortable by names or rates.

        This is work in progress.
    "
    cFirstName = tables.Column(name='First Name' data='firstName')  
    cLastName = tables.Column(name='Last Name' data='Last Name')  
    cTotalPicked = tables.Column(name='Total Picked')  
    cTotalPickedPerTime = tables.Column(name='Total Picked per Hour')  
    class Meta:  
        model = Picker"""


@login_required
def generateReportAllPicker(request): 
    """ 
    Renders a report detailing all picking
    
        Builds a dictionary picker objects will be the key and (total picked, kpi) will be value.
        It uses two dates from the http POST, if they don't make sense the last 31 days are used.
    """
    debug=""
    try:
        sort_by = request.GET.get('sort') 
        startDate, endDate = getDateFromRequest(request)
        data=[] # List: [Picker Firstname, Picker Lastname, total picked, kpi] will be value

        for p in Picker.objects.all():
            timeWorked=(p.getTimeWorkedBetween(startDate, endDate).seconds)/3600.0
            totalPicked=p.getTotalPickedBetween(startDate, endDate)
            avgInitWeight=p.getAvgInitWeightBetween(startDate,endDate);
            totalPickedPerHour= totalPicked/timeWorked if (timeWorked>0) else 0

            data.append([p.firstName, p.lastName, totalPicked, totalPickedPerHour, avgInitWeight])

        if sort_by=="fName":
            data.sort(key=lambda x: x[0])
        elif sort_by=="lName":
            data.sort(key=lambda x: x[1])
        elif sort_by=="totalPicked":
            data.sort(key=lambda x: x[2])
        elif sort_by=="kpi":
            data.sort(key=lambda x: x[3])
        elif sort_by=="avgBox": 
            data.sort(key=lambda x: x[4])

        return render_to_response(
            'report.html', {
                'data' :  data,
                'startDate' : startDate.strftime("%d-%m-%Y"),
                'endDate' : endDate.strftime("%d-%m-%Y"),
                'report_type_all_pickers' : 'True',
                'debug' : debug,
                'user' : request.user
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportPicker(request, picker_id):
    """ 
    Renders a report on picking for a particular picker.
    
        Builds a dictionary, dates are the keys and total picked will be value.
        Plots this with gnuplot and prints it in table form
    """
    try:
        debug = ""
        pickerObj=Picker.objects.get(id=picker_id)
        graphFile = 'pickerGraph.png'
        startDate, endDate = getDateFromRequest(request)
        gp = setupGnuPlot(graphFile, startDate, endDate)

        # Rolling monthly total picking
        dailyTotals = {}
        hoursDailyTotals = {}
        for d in dateRange(startDate, endDate):     
             dailyTotals[d.strftime("%Y-%m-%d")] = pickerObj.getTotalPickedOn(d)
             hoursDailyTotals[d.strftime("%Y-%m-%d")] = pickerObj.getTimeWorkedOn(d).seconds / 3600.0

        # Write data file
        dataFile = 'picker.data'
        aFile=open(GRAPHS_OUTPUT_DIRECTORY + dataFile, "w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(k)+'"\n')
        aFile.close()
        gp("plot '{directory}{filename}' with histogram".format(
            directory = GRAPHS_OUTPUT_DIRECTORY,
            filename = dataFile
        ))

        # Build Output Table
        outputTable = []
        for k in sorted(dailyTotals.keys()):
            if(hoursDailyTotals[k]==0):
                outputTable.append((k, dailyTotals[k], 0.0))
            else:
                outputTable.append((k, dailyTotals[k], dailyTotals[k]/hoursDailyTotals[k]))
        # Render Page
        return render_to_response(
            'report.html', {
                'data' : outputTable,
                'picker' : pickerObj,
                'graph_filename' : graphFile,
                'report_type_picker' : 'True',
                'debug' : debug,
                'user' : request.user
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportRoom(request, room_id):
    """ 
     Renders a report
    
        Builds a dictionary, dates are the keys and total picked in a room will be value.
        Plots this with gnuplot and prints it in table form
    """
    try:
        debug = ""
        startDate, endDate = getDateFromRequest(request)
        roomObj=Room.objects.get(id=room_id)
        graphFile = 'roomGraph.png'
        gp = setupGnuPlot(graphFile, startDate, endDate)
        startDate, endDate = getDateFromRequest(request)

        dailyTotals = {}
        for d in dateRange(startDate, endDate): 
             dailyTotals[d.strftime("%Y-%m-%d")]=roomObj.getTotalPickedOn(d)

        dataFile = 'room.data'
        aFile=open(GRAPHS_OUTPUT_DIRECTORY + dataFile, "w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '{directory}{filename}' with histogram".format(
            directory = GRAPHS_OUTPUT_DIRECTORY,
            filename = dataFile
        ))

        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
		        'room' : roomObj,
                'graph_filename' : graphFile,
                'report_type_room' : 'True',
                'debug':debug,
                'user' : request.user
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportFlush(request, flush_id):
    """ 
     Renders a report
    
        Builds a dictionary, dates are the keys and total picked for a flush will be value.
        Plots this with gnuplot and prints it in table form
    """
#Broken There is a problem with the the endDate  "local variable 'endDate' referenced before assignment"
    try:
        debug = ""
        flushObj=Flush.objects.get(id=flush_id)
        if 'startDate' in request.POST and 'endDate' in request.POST \
            or 'startDate' in request.GET and 'endDate' in request.GET:
            startDate, EndDate = getDateFromRequest(request)
        else: 
            startDate=flushObj.startDate
            endDate=flushObj.endDate if flushObj.endDate is not None else datetime.today()

        graphFile = 'flushGraph.png'
        gp = setupGnuPlot(graphFile, startDate, endDate)

        dailyTotals = {}
        for d in dateRange(startDate, endDate):    
             dailyTotals[d.strftime("%Y-%m-%d")]=flushObj.getTotalPickedOn(d)

        dataFile = 'flush.data'
        aFile=open(GRAPHS_OUTPUT_DIRECTORY + dataFile, "w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '{directory}{filename}' with histogram".format(
            directory = GRAPHS_OUTPUT_DIRECTORY,
            filename = dataFile
        ))

        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
                'total' : sum([(dailyTotals[k]) for k in dailyTotals.keys()]),
		        'flush' : flushObj,
                'graph_filename' : graphFile,
                'report_type_flush' : 'True',
                'user' : request.user
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportCrop(request, crop_id):
    """ 
     Renders a report
    
        Builds a dictionary, dates are the keys and total picked for a flush will be value.
        Plots this with gnuplot and prints it in table form
    """
    try:
        debug = ""
        startDate, endDate = getDateFromRequest(request)
        cropObj=Crop.objects.get(id=crop_id)
        graphFile = 'cropGraph.png'
        gp = setupGnuPlot(graphFile, startDate, endDate)

        dailyTotals = {}
        for d in dateRange(startDate, endDate):    
             dailyTotals[d.strftime("%Y-%m-%d")]=cropObj.getTotalPickedOn(d)

        dataFile = 'crop.data'
        aFile=open(GRAPHS_OUTPUT_DIRECTORY + dataFile, "w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '{directory}{filename}' with histogram".format(
            directory = GRAPHS_OUTPUT_DIRECTORY,
            filename = dataFile
        ))

        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
                'total' : sum([(dailyTotals[k]) for k in dailyTotals.keys()]),
		        'crop' : cropObj,
                'graph_filename' : graphFile,
                'report_type_crop' : 'True',
                'user' : request.user
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReport(request):
    """ 
     Renders the input page, the user selects the parameters for the report they require to
     be genereateed using it
    """
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    room_list = Room.objects.all().order_by('number')
    return render_to_response(
        'report.html', {
            'default_page':'True',
            'picker_list': picker_list,
            'room_list': room_list,
            'user' : request.user
    })

# NOTE: Working from here downward refactoring

##### Bundy Clock handling #####
def bundy(request):
    """
    The default bundy page. Renders the keypad for emp_ID input.
    """
    return render_to_response('bundy.html',{'user' : request.user})

def bundyOnOff(request, bundy_action, picker_id):
    bundy_action=bundy_action.lower()
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    picker_entry = Bundy.objects.filter(picker__id=picker_id, timeOut__isnull=True)
    try:
        picker_ = Picker.objects.get(id=picker_id)
    except Exception as e:
        return render_to_response('bundy.html', {'error_message' : e})
    if bundy_action=="signon":
        session = Bundy(picker=picker_, timeIn=datetime.datetime.now())
        session.save()
        return render_to_response(
            'bundy.html', {
                'picker_list':picker_list,
                'signon_flag':False,
                'show_confirmation': False,
                'user' : request.user
        });
    elif bundy_action=="signoff":
        session = Bundy.objects.get(picker=picker_id, timeOut__isnull=True)
        try: 
            if 'lunch' in request.GET and len(request.GET['lunch'])>1:
                hadLunch_= (str(request.GET['lunch'])=="True")
            else:
                raise NameError("Lunch parameter in http request not found")
        except Exception as e:
            return render_to_response(
                'bundy.html', {
                    'error_message' : e,
                    'user' : request.user
                });
        session.timeOut=datetime.datetime.now()
        session.hadLunch=hadLunch_
        session.save()
        return render_to_response(
            'bundy.html', {
                'picker_list':picker_list,
                'signon_flag':False,
                'show_confirmation': False,
                'user' : request.user
        });
    else: # display the confirmation
        if(len(picker_entry)==0): # picker is trying to sign on
            return render_to_response(
                'bundy.html', {
                    'picker_list':picker_list,
                    'picker':picker_,
                    'signon_flag':True,
                    'show_confirmation': True,
                    'user' : request.user
            });
        else:
            return render_to_response(
                'bundy.html', {
                    'picker_list':picker_list,
                    'picker':picker_,
                    'signon_flag':False,
                    'show_confirmation': True,
                    'user' : request.user
            });

##### CSV export handling #####
def writeListToFile(filename, exportList):
    exportFile = open(filename, "wb")
    exportWriter = csv.writer(exportFile)
    exportWriter.writerows(exportList)
    exportFile.close()

def buildExportList(period=31): #period in days
    header = ("Name", "Hours worked")
    exportList = [header]
    employedPickers = Picker.objects.filter(discharged=False)
    for p in employedPickers:
        daysWorked = Bundy.objects.filter(
            timeIn__gte = datetime.date.today()-datetime.timedelta(days=period),
            picker = p,
            timeOut__isnull=False
        )
        totalHoursWorked=0
        for b in daysWorked:
            totalHoursWorked+=(b.timeOut-b.timeIn).seconds/3600.0
        exportList.append(((p.firstName + " " + p.lastName), totalHoursWorked))
    return exportList

def buildExportListRange(startDate, endDate=datetime.date.today()):
    header = ("Name", "Hours worked")
    exportList = [header]
    employedPickers = Picker.objects.filter(discharged=False)
    for p in employedPickers:
        daysWorked = Bundy.objects.filter(
            timeIn__gte = startDate,
            timeIn__lte = endDate,
            picker = p,
            timeOut__isnull=False
        )
        totalHoursWorked=0
        for b in daysWorked:
            totalHoursWorked+=(b.timeOut-b.timeIn).seconds/3600.0
        exportList.append(((p.firstName + " " + p.lastName), totalHoursWorked))
    return exportList

@login_required
def generateCSV(request):
    fpath = "/var/www/media/csv/"
    fname = "timesheet_" + datetime.date.today().isoformat() + ".csv"
    writeListToFile(fpath+fname, buildExportList() )
    return render_to_response(
        'csv.html', {
            'csvfile' : "/media/csv/" + fname,
            'csvfilename' : fname,
        }
    )

@login_required
def generateCSVRange(request):
    endDate = None
    if 'endDate' in request.POST:
        endDate = datetime.datetime.strptime(request.POST['endDate'], "%d-%m-%Y")
    if 'startDate' in request.POST:
        startDate = datetime.datetime.strptime(request.POST['startDate'], "%d-%m-%Y")
        fpath = "/var/www/media/csv/"
        fname = "timesheet_" + datetime.date.today().isoformat() + ".csv"
        if endDate is None:
            writeListToFile(fpath+fname, buildExportListRange(startDate) )
        else:
            writeListToFile(fpath+fname, buildExportListRange(startDate, endDate) )
        return render_to_response(
            'csv.html', {
                'csvfile' : "/media/csv/" + fname,
                'csvfilename' : fname,
            }
        )
    else:
        return render_to_response(
            'csv.html', {
            }
        )
