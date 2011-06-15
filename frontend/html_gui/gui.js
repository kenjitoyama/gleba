var current_batch = null;
var current_variety = null;
var current_picker = null;
var current_weight = null;

function change_status(text) {
    var status_span = document.querySelector('#status_div > span');
    status_span.innerHTML = text;
}

function show_error(error_msg) {
    change_status(error_msg);
    return null;
}

/* Function 'inspired' by the MDC docs.
 * Please see: https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Date */
function format_date(date) {
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

function get_picker_name(picker_id) {
    var query_string = '#picker_div > input[data-id="' + picker_id + '"]';
    var button = document.querySelector(query_string);
    if(button === null)
        return show_error('No picker with id ' + picker_id);
    if(button.dataset) /* if browser supports dataset */
        return button.dataset.fname;
    else
        return button.getAttribute('data-fname');
}

function get_variety_name(variety_id) {
    var query_string = '#variety_div > input[data-id="'+variety_id+'"]';
    var button = document.querySelector(query_string);
    if(button === null)
        return show_error('No variety with id ' + variety_id);
    if(button.dataset)
        return button.dataset.name;
    else
        return button.getAttribute('data-name');
}

function batch_callback(select_box) {
    document.getElementById('button_audio').play();
    var selected_item = select_box[select_box.selectedIndex];
    if(selected_item.value === "-1")
        current_batch = null;
    else
        current_batch = parseInt(selected_item.value, 10);
}

function variety_callback(button) {
    document.getElementById('button_audio').play();
    if(button.dataset) /* if browser supports dataset */
        current_variety = parseInt(button.dataset.id, 10);
    else
        current_variety = parseInt(button.getAttribute('data-id'), 10);
}

function picker_callback(button) {
    document.getElementById('button_audio').play();
    if(button.dataset) /* if browser supports dataset */
        current_picker = parseInt(button.dataset.id, 10);
    else
        current_picker = parseInt(button.getAttribute('data-id'), 10);
}

function add_box() {
    /* get data from the context */
    if(current_batch === null)
        return show_error('No batch selected. Please select a batch.');
    else if(current_picker === null)
        return show_error('No picker selected. Please select a picker.');
    else if(current_variety === null)
        return show_error('No variety selected. Please select a variety.');
    var picker = current_picker;
    var weight = current_weight;
    var final_weight = current_weight; /* FIXME: adjust this later */
    var variety = current_variety;
    var batch = current_batch;
    var timestamp = format_date(new Date());
    /* add row to history_table */
    var hist_table = document.getElementById('history_table');
    var new_row = hist_table.insertRow(-1); /* insert at the end */
    new_row.setAttribute('onclick', 'toggle_selected(this)');
    /* add cells in the beginning in opposite order */
    var timestamp_cell = new_row.insertCell(0);
    timestamp_cell.appendChild(document.createTextNode(timestamp));
    var batch_cell = new_row.insertCell(0);
    batch_cell.appendChild(document.createTextNode(batch));
    var variety_cell = new_row.insertCell(0);
    variety_cell.appendChild(document.createTextNode(get_variety_name(variety)));
    if(variety_cell.dataset)
        variety_cell.dataset.id = variety;
    else
        variety_cell.setAttribute('data-id', variety);
    var final_weight_cell = new_row.insertCell(0);
    final_weight_cell.appendChild(document.createTextNode(final_weight));
    var weight_cell = new_row.insertCell(0);
    weight_cell.appendChild(document.createTextNode(weight));
    var picker_cell = new_row.insertCell(0);
    picker_cell.appendChild(document.createTextNode(get_picker_name(picker)));
    if(picker_cell.dataset)
        picker_cell.dataset.id = picker;
    else
        picker_cell.setAttribute('data-id', picker);
    /* play sound */
    document.getElementById('success_audio').play();
}

function edit_callback() {
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
        cancel.setAttribute('onclick', 'cancel_edit()');
        apply.setAttribute('id', 'apply_edit');
        apply.setAttribute('type', 'button');
        apply.setAttribute('value', 'Apply');
        apply.setAttribute('onclick', 'apply_edit()');
        var par_div = document.getElementById('right_div');
        var edit_button = document.getElementById('edit_button');
        cancel = par_div.insertBefore(cancel, edit_button);
        apply = par_div.insertBefore(apply, edit_button);
        par_div.removeChild(edit_button);
        /* change status text */
        change_status('Please make your changes and then press Apply');
        mark_history_rows(false);
        /* mark all currents to be null */
        current_picker = current_variety = current_batch = null;
    }
}

function restore_edit() {
    /* insert back edit button */
    var right_div = document.getElementById('right_div');
    var cancel = document.getElementById('cancel_edit');
    var apply = document.getElementById('apply_edit');
    var edit_button = document.createElement('input');
    edit_button.setAttribute('id', 'edit_button');
    edit_button.setAttribute('type', 'button');
    edit_button.setAttribute('value', 'Edit');
    edit_button.setAttribute('onclick', 'edit_callback()');
    edit_button = right_div.insertBefore(edit_button, cancel);
    /* remove cancel/apply */
    right_div.removeChild(cancel);
    right_div.removeChild(apply);
    mark_history_rows(true);
}

function cancel_edit() {
    var edit_row = document.querySelector('#history_table tr.editable');
    edit_row.classList.remove('editable');
    restore_edit();
    change_status('Edit cancelled');
}

function apply_edit() {
    var row = document.querySelector('#history_table tr.editable');
    row.classList.remove('editable');
    if(current_picker != null)
        row.cells[0].firstChild.nodeValue = get_picker_name(current_picker);
    /* Note: We do not change the weights */
    if(current_variety != null)
        row.cells[3].firstChild.nodeValue = get_variety_name(current_variety);
    if(current_batch != null)
        row.cells[4].firstChild.nodeValue = current_batch;
    restore_edit();
    change_status('Changes successfully applied');
}

function mark_history_rows(selectable) {
    var table = document.getElementById('history_table');
    if(selectable) /* restore selection in all entries */
        for(var i = 0; i < table.rows.length; i++)
            table.rows[i].setAttribute('onclick', 'toggle_selected(this)');
    else /* disallow selection in all entries when editing */
        for(var i = 0; i < table.rows.length; i++)
            table.rows[i].removeAttribute('onclick');
}

function commit_callback() {
    console.log('commit_callback() fired');
}

function update_weight_offset_labels() {
    var mushroom_ideal = 4; /* change this to mushroom's real ideal */
    var mushroom_tolerance = 0.050; /* change this to mushroom's real tolerance */
    var weight_div = document.getElementById('weight_div');
    var offset_div = document.getElementById('offset_div');
    var weight_text = weight_div.childNodes[1].firstChild;
    var offset_text = offset_div.childNodes[1].firstChild;
    /* update the text */
    weight_text.nodeValue = current_weight.toFixed(5);
    offset_text.nodeValue = (current_weight-mushroom_ideal).toFixed(5);
    /* update the background */
    if(current_weight < mushroom_ideal) { /* underweight */
        weight_div.classList.add('underweight');
        weight_div.classList.remove('within_range');
        weight_div.classList.remove('overweight');
        offset_div.classList.add('underweight');
        offset_div.classList.remove('within_range');
        offset_div.classList.remove('overweight');
    } else if (current_weight < mushroom_ideal + mushroom_tolerance) { /*good*/
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

function get_weight_forever() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            current_weight = parseFloat(xhr.responseText, 10);
            update_weight_offset_labels();
        }
    };
    xhr.open('GET', 'weight', true);
    xhr.send(null);
    setTimeout('get_weight_forever()', 100); /* every 100 ms */
}

function toggle_selected(row) {
    if(row.classList.contains('selected')) /* removing selection */
        row.classList.remove('selected');
    else { /* adding/changing selection */
        var old_row = document.querySelector('#history_table tr.selected');
        if(old_row != null) /* if there was a previously selected row */
            old_row.classList.remove('selected');
        row.classList.add('selected');
    }
}

function add_batches(batch_list) {
    var batch_select = document.getElementById('batch_div').childNodes[1];
    var list = eval(batch_list);
    for(var i in list) {
        var batch_number = list[i][0];
        var batch_date = list[i][1];
        var batch_room = list[i][2];
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

function add_varieties(variety_list) {
    var variety_div = document.getElementById('variety_div');
    var list = eval(variety_list);
    for(var i in list) {
        var variety_id = list[i][0];
        var variety_name = list[i][1];
        var variety_idealweight = list[i][2];
        var variety_tolerance = list[i][3];
        var new_option = document.createElement('input');
        new_option.setAttribute('type', 'button');
        new_option.setAttribute('onclick', 'variety_callback(this)');
        new_option.classList.add('variety');
        if(new_option.dataset) {
            new_option.dataset.id = variety_id;
            new_option.dataset.name = variety_name;
            new_option.dataset.idealweight = variety_idealweight;
            new_option.dataset.tolerance = variety_tolerance;
        } else {
            new_option.setAttribute('data-id', variety_id);
            new_option.setAttribute('data-name', variety_name);
            new_option.setAttribute('data-idealweight', variety_idealweight);
            new_option.setAttribute('data-tolerance', variety_tolerance);
        }
        new_option.setAttribute('value', variety_name);
        variety_div.appendChild(new_option);
    }
}

function add_pickers(picker_list) {
    var picker_div = document.getElementById('picker_div');
    var list = eval(picker_list);
    for(var i in list) {
        var picker_id = list[i][0];
        var picker_fname = list[i][1];
        var picker_lname = list[i][2];
        var new_option = document.createElement('input');
        new_option.setAttribute('type', 'button');
        new_option.setAttribute('onclick', 'picker_callback(this)');
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

function get_active_batches() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            add_batches(xhr.responseText);
        }
    };
    xhr.open('GET', 'active_batches', true);
    xhr.send(null);
}

function get_active_varieties() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            add_varieties(xhr.responseText);
        }
    };
    xhr.open('GET', 'active_varieties', true);
    xhr.send(null);
}

function get_active_pickers() {
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == 4 && xhr.status == 200) {
            add_pickers(xhr.responseText);
        }
    };
    xhr.open('GET', 'active_pickers', true);
    xhr.send(null);
}

function init_data() {
    get_active_batches();
    get_active_varieties();
    get_active_pickers();
    get_weight_forever();
}

window.onload = init_data;
