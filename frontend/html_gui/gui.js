/////////////////////////////////////////
// WebGUI is the main object of this file
/////////////////////////////////////////
var WebGUI = {};

/////////////////////
// 'Global' variables
/////////////////////
WebGUI.AWAITING_BOX = 'Awaiting box';
WebGUI.ADJUSTING = 'Adjusting';
WebGUI.REMOVE_BOX = 'Remove box';
WebGUI.current_state = WebGUI.AWAITING_BOX;

WebGUI.current_picker = null;
WebGUI.current_batch = null;
WebGUI.current_variety = null;
WebGUI.current_weight = null;
WebGUI.picker_weight = null;
WebGUI.BOX_WEIGHT = 0.0;
WebGUI.weight_window = [];
WebGUI.stable_weight = -1;
WebGUI.current_min_weight = -1;
WebGUI.current_tolerance = -1;

////////////////////
// Utility functions
////////////////////

/* Function 'inspired' by the MDC docs.
 * Please see:
 * https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Date */
WebGUI.format_date = function(date) {
    function pad(n) {
        return n < 10 ? '0' + n : n;
    }
    return date.getFullYear() + '-' +
           pad(date.getMonth()) + '-' +
           pad(date.getDate()) + ' ' +
           pad(date.getHours()) + ':' +
           pad(date.getMinutes()) + ':' +
           pad(date.getSeconds());
}

WebGUI.get_picker_name = function(picker_id) {
    var query_string = '#picker_div > input[data-id="' + picker_id + '"]';
    var button = document.querySelector(query_string);
    if(button === null)
        return '';
    if(button.dataset) /* if browser supports dataset */
        return button.dataset.fname;
    else
        return button.getAttribute('data-fname');
}

WebGUI.get_variety_name = function(variety_id) {
    var query_string = '#variety_div > input[data-id="'+variety_id+'"]';
    var button = document.querySelector(query_string);
    if(button === null)
        return '';
    if(button.dataset)
        return button.dataset.name;
    else
        return button.getAttribute('data-name');
}

////////////////
// GUI callbacks
////////////////

WebGUI.picker_callback = function(button) {
    document.getElementById('button_audio').play();
    if(button.dataset) /* if browser supports dataset */
        WebGUI.current_picker = parseInt(button.dataset.id, 10);
    else
        WebGUI.current_picker = parseInt(button.getAttribute('data-id'), 10);
    WebGUI.picker_weight = WebGUI.current_weight;
    WebGUI.update_current_info_div();
}

WebGUI.batch_callback = function(select_box) {
    document.getElementById('button_audio').play();
    var selected_item = select_box[select_box.selectedIndex];
    if(selected_item.value === "-1")
        WebGUI.current_batch = null;
    else
        WebGUI.current_batch = parseInt(selected_item.value, 10);
    WebGUI.update_current_info_div();
}

WebGUI.variety_callback = function(button) {
    document.getElementById('button_audio').play();
    if(button.dataset) /* if browser supports dataset */
        WebGUI.current_variety = parseInt(button.dataset.id, 10);
    else
        WebGUI.current_variety = parseInt(button.getAttribute('data-id'), 10);
    WebGUI.update_current_info_div();
}

////////////////////////////
// History related functions
////////////////////////////

WebGUI.save_box = function() {
    /* get data from the context */
    if(WebGUI.current_batch === null)
        return WebGUI.show_error('No batch selected. Please select a batch.');
    else if(WebGUI.current_picker === null)
        return WebGUI.show_error('No picker selected. Please select a picker.');
    else if(WebGUI.current_variety === null)
        return WebGUI.show_error('No variety selected. Please select a variety.');
    if(WebGUI.stable_weight > 0 &&
       WebGUI.stable_weight > WebGUI.current_min_weight) {
        var picker = WebGUI.current_picker;
        var weight = WebGUI.picker_weight;
        var final_weight = WebGUI.stable_weight;
        WebGUI.stable_weight = -1;
        var variety = WebGUI.current_variety;
        var batch = WebGUI.current_batch;
        var timestamp = WebGUI.format_date(new Date());
        /* add row to history_table */
        var hist_table = document.getElementById('history_table');
        var new_row = hist_table.insertRow(-1); /* insert at the end */
        new_row.setAttribute('onclick', 'WebGUI.toggle_selected(this)');
        /* add cells in the beginning in opposite order */
        var timestamp_cell = new_row.insertCell(0);
        timestamp_cell.appendChild(document.createTextNode(timestamp));
        var batch_cell = new_row.insertCell(0);
        batch_cell.appendChild(document.createTextNode(batch));
        var variety_cell = new_row.insertCell(0);
        variety_cell.appendChild(document.createTextNode(WebGUI.get_variety_name(variety)));
        if(variety_cell.dataset)
            variety_cell.dataset.id = variety;
        else
            variety_cell.setAttribute('data-id', variety);
        var final_weight_cell = new_row.insertCell(0);
        final_weight_cell.appendChild(document.createTextNode(final_weight));
        var weight_cell = new_row.insertCell(0);
        weight_cell.appendChild(document.createTextNode(weight));
        var picker_cell = new_row.insertCell(0);
        picker_cell.appendChild(document.createTextNode(WebGUI.get_picker_name(picker)));
        if(picker_cell.dataset)
            picker_cell.dataset.id = picker;
        else
            picker_cell.setAttribute('data-id', picker);
        /* play sound */
        document.getElementById('success_audio').play();
    } else
        WebGUI.change_status('Weight not stable');
}

WebGUI.edit_callback = function() {
    var selec_row = document.querySelector('#history_table tr.selected');
    if(selec_row != null) {
        selec_row.classList.remove('selected'); /* remove selection */
        selec_row.classList.add('editable'); /* mark as editable */
        /* create Cancel/OK buttons */
        var cancel = document.createElement('input');
        var apply = document.createElement('input');
        cancel.setAttribute('id', 'cancel_edit');
        cancel.setAttribute('type', 'button');
        cancel.setAttribute('value', 'Cancel');
        cancel.setAttribute('onclick', 'WebGUI.cancel_edit()');
        apply.setAttribute('id', 'apply_edit');
        apply.setAttribute('type', 'button');
        apply.setAttribute('value', 'Apply');
        apply.setAttribute('onclick', 'WebGUI.apply_edit()');
        var par_div = document.getElementById('right_div');
        var edit_button = document.getElementById('edit_button');
        cancel = par_div.insertBefore(cancel, edit_button);
        apply = par_div.insertBefore(apply, edit_button);
        par_div.removeChild(edit_button);
        /* change status text */
        WebGUI.change_status('Please make your changes and then press Apply');
        WebGUI.mark_history_rows(false);
        /* mark all currents to be null */
        WebGUI.current_picker = WebGUI.current_variety =
                                WebGUI.current_batch = null;
    }
}

WebGUI.restore_edit = function() {
    /* insert back edit button */
    var right_div = document.getElementById('right_div');
    var cancel = document.getElementById('cancel_edit');
    var apply = document.getElementById('apply_edit');
    var edit_button = document.createElement('input');
    edit_button.setAttribute('id', 'edit_button');
    edit_button.setAttribute('type', 'button');
    edit_button.setAttribute('value', 'Edit');
    edit_button.setAttribute('onclick', 'WebGUI.edit_callback()');
    edit_button = right_div.insertBefore(edit_button, cancel);
    /* remove cancel/apply */
    right_div.removeChild(cancel);
    right_div.removeChild(apply);
    WebGUI.mark_history_rows(true);
}

WebGUI.cancel_edit = function() {
    var edit_row = document.querySelector('#history_table tr.editable');
    edit_row.classList.remove('editable');
    WebGUI.restore_edit();
    WebGUI.change_status('Edit cancelled');
}

WebGUI.apply_edit = function() {
    var row = document.querySelector('#history_table tr.editable');
    row.classList.remove('editable');
    if(WebGUI.current_picker != null)
        row.cells[0].firstChild.nodeValue = WebGUI.get_picker_name(WebGUI.current_picker);
    /* Note: We do not change the weights */
    if(WebGUI.current_variety != null)
        row.cells[3].firstChild.nodeValue = WebGUI.get_variety_name(WebGUI.current_variety);
    if(WebGUI.current_batch != null)
        row.cells[4].firstChild.nodeValue = WebGUI.current_batch;
    WebGUI.restore_edit();
    WebGUI.change_status('Changes successfully applied');
}

WebGUI.mark_history_rows = function(selectable) {
    var table = document.getElementById('history_table');
    if(selectable) /* restore selection in all entries */
        for(var i = 1; i < table.rows.length; i++)
            table.rows[i].setAttribute('onclick', 'WebGUI.toggle_selected(this)');
    else /* disallow selection in all entries when editing */
        for(var i = 1; i < table.rows.length; i++)
            table.rows[i].removeAttribute('onclick');
}

WebGUI.toggle_selected = function(row) {
    if(row.classList.contains('selected')) /* removing selection */
        row.classList.remove('selected');
    else { /* adding/changing selection */
        var old_row = document.querySelector('#history_table tr.selected');
        if(old_row != null) /* if there was a previously selected row */
            old_row.classList.remove('selected');
        row.classList.add('selected');
    }
}

///////////////////////
// Update GUI functions
///////////////////////

WebGUI.change_status = function(text) {
    var status_span = document.querySelector('#status_div > span');
    status_span.innerHTML = text;
}

WebGUI.show_error = function(error_msg) {
    WebGUI.change_status(error_msg);
    return null;
}

WebGUI.update_current_info_div = function() {
    var curr = document.getElementById('current_info_div');
    var curr_text = curr.childNodes[1].firstChild;
    curr_text.nodeValue = 'Current (batch, variety, picker): (' +
        WebGUI.current_batch + ', ' +
        WebGUI.get_variety_name(WebGUI.current_variety) + ', ' +
        WebGUI.get_picker_name(WebGUI.current_picker) + ')';
}

WebGUI.update_variety_info = function() {
    var query_string = '#variety_div > input[data-id="' + WebGUI.current_variety + '"]';
    var curr_variety = document.querySelector(query_string)
    var variety_min = parseFloat(curr_variety.getAttribute('data-minweight'));
    var variety_tolerance = parseFloat(curr_variety.getAttribute('data-tolerance'));
    WebGUI.current_min_weight = variety_min;
    WebGUI.current_tolerance = variety_tolerance;
}

WebGUI.update_weight_offset_labels = function() {
    var weight_div = document.getElementById('weight_div');
    var offset_div = document.getElementById('offset_div');
    var status_div = document.getElementById('status_div');
    var weight_text = weight_div.childNodes[1].firstChild;
    var offset_text = offset_div.childNodes[1].firstChild;
    var status_text = status_div.childNodes[1].firstChild;
    if(WebGUI.current_variety == null) {
        weight_text.nodeValue = '0.0000';
        offset_text.nodeValue = '0.0000';
        return;
    }
    WebGUI.update_variety_info();
    /* update the text */
    weight_text.nodeValue = WebGUI.current_weight.toFixed(5);
    offset_text.nodeValue = (WebGUI.current_weight-WebGUI.current_min_weight)
                            .toFixed(5);
    status_text.nodeValue = WebGUI.current_state;
    /* update the background */
    if(WebGUI.current_weight < WebGUI.current_min_weight) { /* underweight */
        weight_div.classList.add('underweight');
        weight_div.classList.remove('within_range');
        weight_div.classList.remove('overweight');
        offset_div.classList.add('underweight');
        offset_div.classList.remove('within_range');
        offset_div.classList.remove('overweight');
    } else if (WebGUI.current_weight < WebGUI.current_min_weight +
                                       WebGUI.current_tolerance) { /*good*/
        weight_div.classList.remove('underweight');
        weight_div.classList.add('within_range');
        weight_div.classList.remove('overweight');
        offset_div.classList.remove('underweight');
        offset_div.classList.add('within_range');
        offset_div.classList.remove('overweight');
    } else { /* overweight */
        weight_div.classList.remove('underweight');
        weight_div.classList.remove('within_range');
        weight_div.classList.add('overweight');
        offset_div.classList.remove('underweight');
        offset_div.classList.remove('within_range');
        offset_div.classList.add('overweight');
    }
}

/////////////////////////////////
// Server communication functions
/////////////////////////////////

WebGUI.get_weight_forever = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            WebGUI.current_weight = parseFloat(xhr.responseText, 10);
            WebGUI.update_weight_offset_labels();
            if(WebGUI.current_state == WebGUI.AWAITING_BOX &&
               WebGUI.current_weight > WebGUI.BOX_WEIGHT)
                WebGUI.current_state = WebGUI.ADJUSTING;
            else if(WebGUI.current_state == WebGUI.ADJUSTING) {
                if(WebGUI.current_weight < WebGUI.BOX_WEIGHT)
                    WebGUI.current_state = WebGUI.AWAITING_BOX;
                else if(WebGUI.current_variety) {
                    WebGUI.weight_window.shift();
                    WebGUI.weight_window.push(WebGUI.current_weight);
                    if(WebGUI.current_weight >= WebGUI.current_min_weight &&
                       WebGUI.current_weight < WebGUI.current_min_weight +
                                               WebGUI.current_tolerance) { // in range
                        document.getElementById('green_audio').play();
                        if(WebGUI.current_weight == WebGUI.weight_window[0]) {
                            WebGUI.stable_weight = WebGUI.current_weight;
                            WebGUI.current_state = WebGUI.REMOVE_BOX;
                        }
                    }
                }
            } else if(WebGUI.current_state == WebGUI.REMOVE_BOX &&
                      WebGUI.current_weight < WebGUI.BOX_WEIGHT) {
                WebGUI.save_box();
                WebGUI.current_state = WebGUI.AWAITING_BOX;
            }
        }
    };
    xhr.open('GET', 'weight', true);
    xhr.send(null);
    setTimeout('WebGUI.get_weight_forever()', 100); /* every 100 ms */
}

WebGUI.commit_callback = function() {
    var hist_table = document.getElementById('history_table');
    if(hist_table.rows.length < 2) /* remember rows also includes th */
        return WebGUI.show_error('Nothing to commit');
    while(hist_table.rows.length > 1) { /* always process the first row */
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if(xhr.readyState == 4 && xhr.status == 200 &&
               xhr.responseText != 'true')
                WebGUI.show_error(xhr.responseText);
        };
        /* get data from each row */
        if(hist_table.rows[1].childNodes[0].dataset) {
            var picker_id = hist_table.rows[1].childNodes[0].getAttribute('data-id');
            var variety_id = hist_table.rows[1].childNodes[3].getAttribute('data-id');
        } else {
            var picker_id = hist_table.rows[1].childNodes[0].dataset.id;
            var variety_id = hist_table.rows[1].childNodes[3].dataset.id;
        }
        var initial_weight = hist_table.rows[1].childNodes[1].firstChild.nodeValue;
        var final_weight = hist_table.rows[1].childNodes[2].firstChild.nodeValue;
        var batch_id = hist_table.rows[1].childNodes[4].firstChild.nodeValue;
        var timestamp = hist_table.rows[1].childNodes[5].firstChild.nodeValue;
        /* compile data into POST parameters */
        var params = 'picker_id=' + picker_id +
                     '&initial_weight=' + initial_weight +
                     '&final_weight=' + final_weight +
                     '&variety_id=' + variety_id +
                     '&batch_id=' + batch_id +
                     '&timestamp=' + timestamp;
        xhr.open('POST', 'add_box', true);
        xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
        xhr.send(params);
        /* remove this row */
        hist_table.deleteRow(1);
    }
}

WebGUI.get_active_pickers = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            picker_list = xhr.responseText;
            var picker_div = document.getElementById('picker_div');
            var list = JSON.parse(picker_list);
            for(var i in list) {
                var picker_id = list[i]['id'];
                var picker_fname = list[i]['first_name'];
                var picker_lname = list[i]['last_name'];
                var new_option = document.createElement('input');
                new_option.setAttribute('type', 'button');
                new_option.setAttribute('onclick', 'WebGUI.picker_callback(this)');
                new_option.classList.add('picker');
                if(new_option.dataset) {
                    new_option.dataset.id = picker_id;
                    new_option.dataset.fname = picker_fname;
                    new_option.dataset.lname = picker_lname;
                } else {
                    new_option.setAttribute('data-id', picker_id);
                    new_option.setAttribute('data-fname', picker_fname);
                    new_option.setAttribute('data-lname', picker_lname);
                }
                new_option.setAttribute('value', picker_id + '. ' + picker_fname);
                picker_div.appendChild(new_option);
            }
        }
    };
    xhr.open('GET', 'active_pickers.json', true);
    xhr.send(null);
}

WebGUI.get_active_batches = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            batch_list = xhr.responseText;
            var batch_select = document.getElementById('batch_div').childNodes[1];
            var list = JSON.parse(batch_list);
            for(var i in list) {
                var batch_number = list[i]['id'];
                var batch_date = list[i]['date']['year'] + '-' +
                                 list[i]['date']['month'] + '-' +
                                 list[i]['date']['day'];
                var batch_room = list[i]['room_number'];
                var new_option = document.createElement('option');
                new_option.classList.add('batch');
                new_option.setAttribute('value', batch_number);
                if(new_option.dataset) {
                    new_option.dataset.date = batch_date;
                    new_option.dataset.room = batch_room;
                } else {
                    new_option.setAttribute('data-date', batch_date);
                    new_option.setAttribute('data-room', batch_room);
                }
                var batch_text = 'Batch '+batch_number+' '+batch_date+' room '+batch_room;
                new_option.appendChild(document.createTextNode(batch_text));
                batch_select.add(new_option, null);
            }
        }
    };
    xhr.open('GET', 'active_batches.json', true);
    xhr.send(null);
}

WebGUI.get_active_varieties = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            variety_list = xhr.responseText;
            var variety_div = document.getElementById('variety_div');
            var list = JSON.parse(variety_list);
            for(var i in list) {
                var variety_id = list[i]['id'];
                var variety_name = list[i]['name'];
                var variety_minweight = list[i]['minimum_weight'];
                var variety_tolerance = list[i]['tolerance'];
                var new_option = document.createElement('input');
                new_option.setAttribute('type', 'button');
                new_option.setAttribute('onclick', 'WebGUI.variety_callback(this)');
                new_option.classList.add('variety');
                if(new_option.dataset) {
                    new_option.dataset.id = variety_id;
                    new_option.dataset.name = variety_name;
                    new_option.dataset.minweight = variety_minweight;
                    new_option.dataset.tolerance = variety_tolerance;
                } else {
                    new_option.setAttribute('data-id', variety_id);
                    new_option.setAttribute('data-name', variety_name);
                    new_option.setAttribute('data-minweight', variety_minweight);
                    new_option.setAttribute('data-tolerance', variety_tolerance);
                }
                new_option.setAttribute('value', variety_name);
                variety_div.appendChild(new_option);
            }
        }
    };
    xhr.open('GET', 'active_varieties.json', true);
    xhr.send(null);
}

WebGUI.get_box_weight = function() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200)
            WebGUI.BOX_WEIGHT = parseFloat(xhr.responseText);
    };
    xhr.open('GET', 'box_weight', true);
    xhr.send(null);
}

WebGUI.init_data = function() {
    WebGUI.get_active_batches();
    WebGUI.get_active_varieties();
    WebGUI.get_active_pickers();
    WebGUI.get_box_weight();
    for(var i=0; i<10; i++) /* fill weight window */
        WebGUI.weight_window[i] = 0.0;
    WebGUI.get_weight_forever();
}

window.onload = WebGUI.init_data;
