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

##### Report Handling #####

# Functions for generating reports
def setupGnuPlot(graphFile):
    """ Given a filename, it returns a new gnuploter """
    g = Gnuplot.Gnuplot()
    g('set terminal png size 640,480')
    g("set output '/var/www%s'" % graphFile)
    g('set style fill solid 1.00 border -1')
    g('set style histogram cluster gap 1')
    g("set xtics ("+"".join(['"'+d.strftime("%Y-%m-%d")+'"'+str(i)+',' for i,d in enumerate(sorted(lastMonth())) if (i%5==0)])[:-1]+")")
    g("set xtics rotate by -60")
    g("unset key")
    return g

def setupGnuPlotRange(graphFile, startDate, endDate):
    """ Given a filename and two dates, it returns a new gnuploter """
    g = setupGnuPlot(graphFile)
    g("set xtics ("+"".join(['"'+d.strftime("%Y-%m-%d")+'"'+str(i)+',' for i,d in enumerate(dateRange(startDate,endDate)) if (i%5==0)])[:-1]+")")
    return g

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
    

def getDateFromRequest(request):
    """ Retrieves and returns a tuple of dates from a http request.

        If request does not contain a valid startDate, 31 days in the past from today is used.
        If request does not contain a valid endDate, today is used."""
    if 'startDate' in request.POST and len(request.POST['startDate'])>1:
        startDate = datetime.datetime.strptime(request.POST['startDate'], "%d-%m-%Y").date()
    else:
        startDate = datetime.date.today() - datetime.timedelta(days=31)
    if 'endDate' in request.POST and len(request.POST['endDate'])>1:
        endDate = datetime.datetime.strptime(request.POST['endDate'], "%d-%m-%Y").date()
    else:
        endDate = datetime.date.today()
    if endDate<startDate:
        debug+="The end date is before the start date."
    return (startDate, endDate)
    
@login_required
def generateReportAllPickerRange(request): 
    """ Renders a report
    
        Builds a dictionary picker objects will be the key and (total picked, kpi) will be value.
        It uses two dates from the http POST, if they don't make sense the last 31 days are used.
    """
    try:
        debug=""
        startDate, endDate = getDateFromRequest(request)
        data={} # Dictionary: picker objects will be the key and (total picked, kpi) will be value
        for p in Picker.objects.all():
            # timeWorked for picker p in hours
            timeWorked=(p.getTimeWorkedBetween(startDate, endDate).seconds)/3600.0
            if timeWorked>0: # p has worked
                totalPicked=p.getTotalPickedBetween(startDate, endDate)
                data[p]=(totalPicked, totalPicked/timeWorked)
        return render_to_response(
            'report.html', {
                'data' :  data,
                'startDate' : startDate,
                'endDate' : endDate,
                'report_type_all_pickers' : 'True',
                'debug' : debug,
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportPicker(request, picker_id):
    """ Renders a report
    
        Builds a dictionary, dates are the keys and total picked will be value.
        Plots this with gnuplot and prints it in table form
    """
    try:
        debug = ""
        pickerObj=Picker.objects.get(id=picker_id)
        graphFile = "/media/graphs/pickerGraph.png"
        startDate, endDate = getDateFromRequest(request)
        gp = setupGnuPlotRange(graphFile, startDate, endDate)

        # Rolling monthly total picking
        dailyTotals = {}
        hoursDailyTotals = {}
        for d in dateRange(startDate, endDate):     
             dailyTotals[d.strftime("%Y-%m-%d")] = pickerObj.getTotalPickedOn(d)
             hoursDailyTotals[d.strftime("%Y-%m-%d")] = pickerObj.getTimeWorkedOn(d).seconds / 3600.0

        # Write data file
        dataFile = "/media/graphs/picker.data"
        aFile=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(k)+'"\n')
        aFile.close()
        gp("plot '/var/www"+dataFile+"' with histogram")

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
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportRoom(request, room_id):
    """ Renders a report
    
        Builds a dictionary, dates are the keys and total picked in a room will be value.
        Plots this with gnuplot and prints it in table form
    """
    try:
        debug = ""
        startDate, endDate = getDateFromRequest(request)
        roomObj=Room.objects.get(id=room_id)
        graphFile = "/media/graphs/roomGraph.png"
        gp = setupGnuPlot(graphFile)
        startDate, endDate = getDateFromRequest(request)

        dailyTotals = {}
        for d in dateRange(startDate, endDate): 
             dailyTotals[d.strftime("%Y-%m-%d")]=roomObj.getTotalPickedOn(d)

        dataFile="/media/graphs/room.data"
        aFile=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '/var/www"+dataFile+"' with histogram")

        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
		        'room' : roomObj,
                'graph_filename' : graphFile,
                'report_type_room' : 'True',
                'debug':debug,
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})


# NOTE: Working from here downward refactoring

@login_required
def generateReportFlush(request, flush_id):
    try:
        debug = ""
        flushObj=Flush.objects.get(id=flush_id)
        graphFile = "/media/graphs/flushGraph.png"
        gp = setupGnuPlot(graphFile)
        #rolling monthly
        dailyTotals = {}
        for d in lastMonth():    
             boxes  = Box.objects.filter(batch__flush=flushObj, batch__date=d)
             dailyTotals[d.strftime("%Y-%m-%d")]=sum([b.initialWeight for b in boxes])
        dataFile="/media/graphs/flush.data"
        aFile=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '/var/www"+dataFile+"' with histogram")
        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
                'total' : sum([(dailyTotals[k]) for k in dailyTotals.keys()]),
		        'flush' : flushObj,
                'graph_filename' : graphFile,
                'report_type_flush' : 'True',
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportFlushRange(request, flush_id):
    debug = ""
    startDate, endDate = getDateFromRequest(request)
    flushObj=Flush.objects.get(id=flush_id)
    graphFile = "/media/graphs/flushGraph.png"
    gp = setupGnuPlot(graphFile)
    #rolling monthly
    dailyTotals = {}
    boxes = Box.objects.filter(batch__flush=flushObj,
                               batch__date__gte=startDate,
                               batch__date__lt=endDate)
    sumTotal=0.0
    while startDate!=endDate:
        sumToday=0.0
        sumTmp=boxes.filter(batch__date=startDate).aggregate(Sum('initialWeight'))
        if sumTmp['initialWeight__sum'] is not None:
            sumToday=sumTmp['initialWeight__sum']
        sumTotal+=sumToday
        startDateStr=startDate.strftime("%Y-%m-%d")
        dailyTotals[startDateStr]=sumToday
        startDate+=datetime.timedelta(days=1)
    dataFile="/media/graphs/flush.data"
    aFile=open("/var/www"+dataFile,"w")
    for i,k in enumerate(sorted(dailyTotals.keys())):
        aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
    aFile.close()
    gp("plot '/var/www"+dataFile+"' with histogram")
    return render_to_response(
        'report.html', {
            'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
            'total' : sumTotal,
            'flush' : flushObj,
            'graph_filename' : graphFile,
            'report_type_flush' : 'True',
        }
    )

@login_required
def generateReportCrop(request, crop_id):
    try:
        debug = ""
        cropObj=Crop.objects.get(id=crop_id)
        graphFile = "/media/graphs/cropGraph.png"
        gp = setupGnuPlot(graphFile)
        #rolling monthly
        dailyTotals = {}
        for d in lastMonth():    
             boxes  = Box.objects.filter(batch__flush__crop=cropObj, batch__date=d)
             dailyTotals[d.strftime("%Y-%m-%d")]=sum([b.initialWeight for b in boxes])
        dataFile="/media/graphs/flush.data"
        aFile=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        aFile.close()
        gp("plot '/var/www"+dataFile+"' with histogram")
        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
                'total' : sum([(dailyTotals[k]) for k in dailyTotals.keys()]),
		        'crop' : cropObj,
                'graph_filename' : graphFile,
                'report_type_crop' : 'True',
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

@login_required
def generateReportCropRange(request, crop_id):
    debug = ""
    startDate, endDate = getDateFromRequest(request)
    cropObj=Crop.objects.get(id=crop_id)
    graphFile = "/media/graphs/cropGraph.png"
    gp = setupGnuPlot(graphFile)
    #rolling monthly
    dailyTotals = {}
    boxes = Box.objects.filter(batch__date__gte=startDate,
                               batch__date__lt=endDate,
                               batch__flush__crop=cropObj)
    sumTotal=0.0
    while startDate!=endDate:
        sumToday=0.0
        sumTmp=boxes.filter(batch__date=startDate).aggregate(Sum('initialWeight'))
        if sumTmp['initialWeight__sum'] is not None:
            sumToday=sumTmp['initialWeight__sum']
        sumTotal+=sumToday
        startDateStr=startDate.strftime("%Y-%m-%d")
        dailyTotals[startDateStr]=sumToday
        startDate+=datetime.timedelta(days=1)
    dataFile="/media/graphs/flush.data"
    aFile=open("/var/www"+dataFile,"w")
    for i,k in enumerate(sorted(dailyTotals.keys())):
        aFile.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
    aFile.close()
    gp("plot '/var/www"+dataFile+"' with histogram")
    return render_to_response(
        'report.html', {
            'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
            'total' : sumTotal,
            'crop' : cropObj,
            'graph_filename' : graphFile,
            'report_type_crop' : 'True',
        }
    )

@login_required
def generateReport(request):
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    room_list = Room.objects.all().order_by('number')
    return render_to_response(
        'report.html', {
            'default_page':'True',
            'picker_list': picker_list,
            'room_list': room_list,
    })

##### Bundy Clock handling #####
def bundy(request):
    return render_to_response('bundy.html')
    #picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    #return render_to_response(
    #    'bundy.html', {
    #        'picker_list':picker_list,
    #});

def bundyOnOff(request, bundy_action, picker_id):
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    picker_entry = Bundy.objects.filter(picker=picker_id, timeOut__isnull=True)
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
        });
    elif bundy_action=="signoff":
        session = Bundy.objects.get(picker=picker_id, timeOut__isnull=True)
        try: 
            if 'lunch' in request.GET and len(request.GET['lunch'])>1:
                hadLunch_= (str(request.GET['lunch'])=="True")
            else:
                raise NameError("Lunch parameter in http request not found")
        except Exception as e:
            return render_to_response('bundy.html', {'error_message' : e})
        session.timeOut=datetime.datetime.now()
        session.hadLunch=hadLunch_
        session.save()
        return render_to_response(
            'bundy.html', {
                'picker_list':picker_list,
                'signon_flag':False,
                'show_confirmation': False,
        });
    else: # display the confirmation
        if(len(picker_entry)==0): # picker is trying to sign on
            return render_to_response(
                'bundy.html', {
                    'picker_list':picker_list,
                    'picker':picker_,
                    'signon_flag':True,
                    'show_confirmation': True,
            });
        else:
            return render_to_response(
                'bundy.html', {
                    'picker_list':picker_list,
                    'picker':picker_,
                    'signon_flag':False,
                    'show_confirmation': True,
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
