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

function get_picker_name(picker_id) {
    var query_string = '#picker_div > input[data-id="' + picker_id + '"]';
    var button = document.querySelector(query_string);
    if(button === null)
        return show_error('No picker with id ' + picker_id);
    if(button.dataset) /* if browser supports dataset */
        return button.dataset.name;
    else
        return button.getAttribute('data-name');
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
    var timestamp = '2011-05-20 19:31:30';
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
    /* assign new timestamp */
    row.cells[5].firstChild.nodeValue = '2011-05-05 12:13:14';
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
