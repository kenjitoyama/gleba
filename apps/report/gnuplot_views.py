import Gnuplot

# Kenji TODO: Move this 'constant' to another file for easier customization
GRAPHS_OUTPUT_DIRECTORY = ('/home/kenji/django-projects/gleba/glebaAdmin/' +
                          'static/media/graphs/')
def setupGnuPlot(graphFile,
                 startDate = datetime.date.today() - datetime.timedelta(days=31),
                 endDate = datetime.date.today()):
    """
    Given a filename, it returns a new gnuploter.
    
    If startDate is not given, 31 days in the past from today is used.
    If endDate is not given, today is used.
    """
    g = Gnuplot.Gnuplot()
    g('set terminal png size 640,480')
    g("set output '{directory}{filename}'".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = graphFile
    ))
    g('set style fill solid 1.00 border -1')
    g('set style histogram cluster gap 1')
    g("set xtics ({0})".format(
        "".join(['"' + d.strftime("%Y-%m-%d") + '"' + str(i) + ','\
        for i, d in enumerate(date_range(startDate, endDate)) \
            if (i % 5 == 0)])[:-1]
    ))
    g("set xtics rotate by -60")
    g("unset key")
    return g   

@login_required
def generateReportPicker(request, picker_id):
    """ 
    Renders a report on picking for a particular picker.
    
    Builds a dictionary, dates are the keys and total picked will be value.
    Plots this with gnuplot and prints it in table form
    """
    debug = ""
    picker_obj = get_object_or_404(Picker, pk = picker_id)
    graph_filename = 'pickerGraph.png'
    start_date, end_date = getDateFromRequest(request)
    gp = setupGnuPlot(graph_filename, start_date, end_date)

    # Rolling monthly total picking
    daily_totals = {}
    hours_daily_totals = {}
    for d in date_range(start_date, end_date):     
        daily_totals[d.strftime("%Y-%m-%d")] =\
            picker_obj.getTotalPickedOn(d)
        hours_daily_totals[d.strftime("%Y-%m-%d")] =\
            picker_obj.getTimeWorkedOn(d).seconds / 3600.0

    # Write data file
    data_filename = 'picker.data'
    data_file = open(GRAPHS_OUTPUT_DIRECTORY + data_filename, "w")
    for idx, key in enumerate(sorted(daily_totals.keys())):
        data_file.write('{0} "{1}"\n '.format(
            str(daily_totals[key]), str(key))
        )
    data_file.close()
    gp("plot '{directory}{filename}' with histogram".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = data_filename
    ))

    # Build Output Table
    outputTable = []
    for key in sorted(daily_totals.keys()):
        if(hours_daily_totals[key] == 0):
            outputTable.append((key, daily_totals[key], 0.0))
        else:
            outputTable.append((key, daily_totals[key],
                                daily_totals[key]/hours_daily_totals[key]))
    # Render Page
    return render_to_response('report.html', {
            'data' : outputTable,
            'picker' : picker_obj,
            'graph_filename' : graph_filename,
            'report_type' : 'picker',
            'debug' : debug,
            'user' : request.user
    })

@login_required
def generateReportRoom(request, room_id):
    """ 
    Renders a report
    
    Builds a dictionary, dates are the keys and total picked in a room will
    be value.
    Plots this with gnuplot and prints it in table form
    """
    debug = ""
    room_obj = get_object_or_404(Room, pk = room_id)
    graph_filename = 'roomGraph.png'
    start_date, end_date = getDateFromRequest(request)
    gp = setupGnuPlot(graph_filename, start_date, end_date)

    daily_totals = {}
    for d in date_range(start_date, end_date): 
        daily_totals[d.strftime("%Y-%m-%d")] = room_obj.getTotalPickedOn(d)

    data_filename = 'room.data'
    data_file = open(GRAPHS_OUTPUT_DIRECTORY + data_filename, "w")
    for idx, key in enumerate(sorted(daily_totals.keys())):
        data_file.write('{0} "{1}"\n'.format(
            str(daily_totals[key]), str(idx))
        )
    data_file.close()
    gp("plot '{directory}{filename}' with histogram".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = data_filename
    ))

    return render_to_response('report.html', {
        'data' : [(k, daily_totals[k])
                  for k in sorted(daily_totals.keys())],
        'room' : room_obj,
        'graph_filename' : graph_filename,
        'report_type' : 'room',
        'debug':debug,
        'user' : request.user
    })

@login_required
def generateReportFlush(request, flush_id):
    """ 
    Renders a report
    
    Builds a dictionary, dates are the keys and total picked for a flush will
    be value.
    Plots this with gnuplot and prints it in table form
    """
    debug = ""
    flushObj = get_object_or_404(Flush, pk = flush_id)
    start_date = flushObj.startDate
    end_date = (flushObj.endDate if flushObj.endDate is not None
                                 else datetime.date.today())

    graph_filename = 'flushGraph.png'
    gp = setupGnuPlot(graph_filename, start_date, end_date)

    daily_totals = {}
    for d in date_range(start_date, end_date):    
        daily_totals[d.strftime("%Y-%m-%d")] = flushObj.getTotalPickedOn(d)

    data_filename = 'flush.data'
    data_file = open(GRAPHS_OUTPUT_DIRECTORY + data_filename, "w")
    for idx, key in enumerate(sorted(daily_totals.keys())):
        data_file.write('{0} "{1}"\n'.format(
            str(daily_totals[key]), str(idx)
        ))
    data_file.close()
    gp("plot '{directory}{filename}' with histogram".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = data_filename
    ))

    return render_to_response(
        'report.html', {
            'data' : [(key, daily_totals[key])
                      for key in sorted(daily_totals.keys())],
            'total' : sum([(daily_totals[key])
                          for key in daily_totals.keys()]),
	        'flush' : flushObj,
            'graph_filename' : graph_filename,
            'report_type' : 'flush',
            'user' : request.user
        }
    )

@login_required
def generateReportCrop(request, crop_id):
    """ 
    Renders a report
    
    Builds a dictionary, dates are the keys and total picked for a flush will
    be value.
    Plots this with gnuplot and prints it in table form
    """
    debug = ""
    crop_obj = get_object_or_404(Crop, pk = crop_id)
    start_date = crop_obj.startDate
    end_date = (crop_obj.endDate if crop_obj.endDate is not None
                                 else datetime.date.today())
    graph_filename = 'cropGraph.png'
    gp = setupGnuPlot(graph_filename, start_date, end_date)

    daily_totals = {}
    for d in date_range(start_date, end_date):    
        daily_totals[d.strftime("%Y-%m-%d")] = crop_obj.getTotalPickedOn(d)

    data_filename = 'crop.data'
    data_file = open(GRAPHS_OUTPUT_DIRECTORY + data_filename, "w")
    for idx, key in enumerate(sorted(daily_totals.keys())):
        data_file.write('{0} "{1}"\n'.format(
            str(daily_totals[key]), str(idx)
        ))
    data_file.close()
    gp("plot '{directory}{filename}' with histogram".format(
        directory = GRAPHS_OUTPUT_DIRECTORY,
        filename = data_filename
    ))

    return render_to_response('report.html', {
        'data' : [(key, daily_totals[key])
                  for key in sorted(daily_totals.keys())],
        'total' : sum([(daily_totals[key])
                       for key in daily_totals.keys()]),
        'crop' : crop_obj,
        'graph_filename' : graph_filename,
        'report_type' : 'crop',
        'user' : request.user
    })

