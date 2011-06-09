var current_batch = null;
var current_variety = null;
var current_picker = null;

function change_status(text) {
    status_span = document.querySelector('#status_div > span');
    status_span.innerHTML = text;
}

function show_error(error_msg) {
    change_status(error_msg);
    return null;
}

function get_picker_name(picker_id) {
    query_string = '#picker_div > input[data-id="' + picker_id + '"]';
    button = document.querySelector(query_string);
    if(button === null)
        return show_error('No picker with id ' + picker_id);
    return button.dataset.name;
}

function get_variety_name(variety_id) {
    query_string = '#variety_div > input[data-id="'+variety_id+'"]';
    button = document.querySelector(query_string);
    if(button === null)
        return show_error('No variety with id ' + variety_id);
    return button.dataset.name;
}

function batch_callback(select_box) {
    selected_index = select_box.selectedIndex;
    selected_item = select_box[selected_index];
    if(selected_item.value === "-1")
        current_batch = null;
    else
        current_batch = parseInt(selected_item.value, 10);
}

function variety_callback(button) {
    current_variety = parseInt(button.dataset.id, 10);
}

function picker_callback(button) {
    current_picker = parseInt(button.dataset.id, 10);
}

function add_box() {
    // get data from the context
    if(current_batch === null)
        return show_error('No batch selected. Please select a batch.');
    else if(current_picker === null)
        return show_error('No picker selected. Please select a picker.');
    else if(current_variety === null)
        return show_error('No variety selected. Please select a variety.');
    picker = current_picker;
    weight = 4.045;
    final_weight = 4.025;
    variety = current_variety;
    batch = current_batch;
    timestamp = '2011-05-20 19:31:30';
    // add row to history_table
    hist_table = document.getElementById('history_table');
    new_row = hist_table.insertRow(-1); /* insert at the end */
    /* add cells in the beginning in opposite order */
    timestamp_cell = new_row.insertCell(0);
    timestamp_cell.appendChild(document.createTextNode(timestamp));
    batch_cell = new_row.insertCell(0);
    batch_cell.appendChild(document.createTextNode(batch));
    variety_cell = new_row.insertCell(0);
    variety_cell.appendChild(document.createTextNode(get_variety_name(variety)));
    variety_cell.dataset.id = variety;
    final_weight_cell = new_row.insertCell(0);
    final_weight_cell.appendChild(document.createTextNode(final_weight));
    weight_cell = new_row.insertCell(0);
    weight_cell.appendChild(document.createTextNode(weight));
    picker_cell = new_row.insertCell(0);
    picker_cell.appendChild(document.createTextNode(get_picker_name(picker)));
    picker_cell.dataset.id = picker;
}

function edit_callback() {
    console.log('edit_callback() fired');
}

function commit_callback() {
    console.log('commit_callback() fired');
}
