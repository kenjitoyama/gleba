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

def getBatchList(request):
    batch_list = Batch.objects.filter(flush__endDate__isnull=True).order_by('id')
    return render_to_response(
        'batchList.html', {
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

##### Report Handling #####

# functions for generating reports
def setupGnuPlot(graphFile):
    g = Gnuplot.Gnuplot()
    g('set terminal png size 640,480')
    g("set output '/var/www%s'" % graphFile)
    g('set style fill solid 1.00 border -1')
    g('set style histogram cluster gap 1')
    g("set xtics ("+"".join(['"'+d.strftime("%Y-%m-%d")+'"'+str(i)+',' for i,d in enumerate(sorted(lastMonth())) if (i%5==0)])[:-1]+")")
    g("set xtics rotate by -60")
    g("unset key")
    return g

def lastMonth():
  return [datetime.date.today() - datetime.timedelta(days=i) for i in range(31)]

@login_required
def generateReportPicker(request, picker_id):
    try:
        debug = ""
        pickerObj=Picker.objects.get(id=picker_id)
        graphFile = "/media/graphs/pickerGraph.png"
        gp = setupGnuPlot(graphFile)
        # Rolling monthly total picking
        #   Can be refactored to use pure SQL to increase performance
        dailyTotals = {}
        hoursDailyTotals = {}
        for d in lastMonth():    
             boxes  = Box.objects.filter(picker=pickerObj, batch__date=d)
             dailyTotals[d.strftime("%Y-%m-%d")]=sum([b.initialWeight for b in boxes])
             #boxes  = Box.objects.filter(picker=pickerObj, batch__date=d).aggregate(Sum('initialWeight'))
             #sumBox=0.0
             #if boxes['initialWeight__sum'] is not None:
             #    sumBox=boxes['initialWeight__sum']
             #dailyTotals[d.strftime("%Y-%m-%d")]=sumBox
             bundies = Bundy.objects.filter(picker=pickerObj, timeIn__startswith=d, timeOut__isnull=False)
             hoursDailyTotals[d.strftime("%Y-%m-%d")]=sum([(b.timeOut-b.timeIn).seconds/3600.0 for b in bundies])
             #bundies = Bundy.objects.filter(picker=pickerObj, timeIn__startswith=d, timeOut__isnull=False).aggregate(Sum('timeWorked'))
             #sumBundy = 0.0
             #if bundies['timeWorked__sum'] is not None:
                #sumBundy = bundies['timeWorked__sum']
             #hoursDailyTotals[d.strftime("%Y-%m-%d")]=sumBundy
        dataFile="/media/graphs/picker.data"
# Kenji: rename file to something less conflicting (like aFile etc). file is a 'reserved' word in Python (well, not really. but it's better to be different).
        file=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            file.write(str(dailyTotals[k])+' "'+str(k)+'"\n')
        file.close()
        gp("plot '/var/www"+dataFile+"' with histogram")
        outputTable = []
        for k in sorted(dailyTotals.keys()):
            if(hoursDailyTotals[k]==0):
                outputTable.append((k, dailyTotals[k], 0.0))
            else:
                outputTable.append((k, dailyTotals[k], dailyTotals[k]/hoursDailyTotals[k]))
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
    try:
        debug = ""
        roomObj=Room.objects.get(id=room_id)
        graphFile = "/media/graphs/roomGraph.png"
        gp = setupGnuPlot(graphFile)
        #rolling monthly
        dailyTotals = {}
        for d in lastMonth():    
             boxes  = Box.objects.filter(batch__flush__crop__room=roomObj, batch__date=d)
             dailyTotals[d.strftime("%Y-%m-%d")]=sum([b.initialWeight for b in boxes])
        dataFile="/media/graphs/room.data"
        file=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            file.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        file.close()
        gp("plot '/var/www"+dataFile+"' with histogram")
        return render_to_response(
            'report.html', {
                'data' : [(k,dailyTotals[k]) for k in sorted(dailyTotals.keys())],
		        'room' : roomObj,
                'graph_filename' : graphFile,
                'report_type_room' : 'True',
            }
        )
    except Exception as e:
        return render_to_response('error.html', {'error_list' : e, 'debug' : debug})

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
        file=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            file.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        file.close()
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
        file=open("/var/www"+dataFile,"w")
        for i,k in enumerate(sorted(dailyTotals.keys())):
            file.write(str(dailyTotals[k])+' "'+str(i)+'"\n')
        file.close()
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
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    return render_to_response(
        'bundy.html', {
            'picker_list':picker_list,
    });

def bundyOnOff(request, bundy_action, picker_id):
    picker_list = Picker.objects.filter(active=True, discharged=False).order_by('id')
    picker_entry = Bundy.objects.filter(picker=picker_id, timeOut__isnull=True)
    picker_ = Picker.objects.get(id=picker_id)
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
        session.timeOut=datetime.datetime.now()
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
