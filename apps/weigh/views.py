from django.shortcuts import render_to_response, get_object_or_404
from glebaAdmin.models import *

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
