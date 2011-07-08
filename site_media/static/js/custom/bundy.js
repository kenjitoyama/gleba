var Bundy = {};

Bundy.submitForm = function(view) {
    var selected_value = document.getElementById('picker_id').value;
    $('#bundy_picker_form').attr('action', view + selected_value + '/');
    $('#bundy_picker_form').submit();
}

Bundy.appendNumber = function(x) {
    var pickerIDInput = document.getElementById('picker_id');
    pickerIDInput.value += x;
}

Bundy.backspace = function() {
    var pickerIDInput = document.getElementById('picker_id');
    pickerIDInput.value =
        pickerIDInput.value.substring(0, pickerIDInput.value.length - 1);
}
