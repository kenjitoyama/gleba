var Bundy = {};

Bundy.submitForm = function(view) {
    var selected_value = Bundy.picker_id_input.value;
    if (selected_value) {
        var bundy_picker_form = document.getElementById('bundy_picker_form');
	bundy_picker_form.setAttribute('action', view + selected_value + '/');
	bundy_picker_form.submit();
    }
}

Bundy.appendNumber = function(x) {
    Bundy.audio_button.play();
    Bundy.picker_id_input.value += x;
}

Bundy.backspace = function() {
    Bundy.audio_button.play();
    Bundy.picker_id_input.value = Bundy.picker_id_input.value.substring(0,
                                  Bundy.picker_id_input.value.length - 1);
}

Bundy.clear = function() {
    Bundy.audio_button.play();
    Bundy.picker_id_input.value = '';
}

window.onload = function() {
    Bundy.audio_button = document.getElementById('button_audio');
    Bundy.picker_id_input = document.getElementById('picker_id');
}
