var current_batch = null;
var current_variety = null;
var current_picker = null;

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
    // get data from the context
    if(current_batch === null)
        return show_error('No batch selected. Please select a batch.');
    else if(current_picker === null)
        return show_error('No picker selected. Please select a picker.');
    else if(current_variety === null)
        return show_error('No variety selected. Please select a variety.');
    var picker = current_picker;
    var weight = 4.045;
    var final_weight = 4.025;
    var variety = current_variety;
    var batch = current_batch;
    var timestamp = '2011-05-20 19:31:30';
    // add row to history_table
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
    console.log('edit_callback() fired');
}

function commit_callback() {
    console.log('commit_callback() fired');
}

function toggle_selected(row) {
    if(row.hasAttribute('data-selected')) /* removing selection */
        row.removeAttribute('data-selected');
    else { /* adding/changing selection */
        old_row = document.querySelector('#history_table tr[data-selected]');
        if(old_row != null) /* if there was a previously selected row */
            old_row.removeAttribute('data-selected');
        row.setAttribute('data-selected', 'true');
    }
}
