var Report = {};

Report.submitForm = function(report_type) {
    var form = $('#'+report_type+'report_form');
    var form_url = form.attr('action');
    var selected_value = $('#'+report_type+'menu').val();
    form_url = report_type.substring(0, report_type.length-1)+'/' + selected_value + '/';
    form.attr('action', form_url);
    form.append($('#start_date'));
    form.append($('#end_date'));
    form.submit();
}

Report.submitAllPickerForm = function() {
    var form = $("#all_picker_report_form")    
    form.append($("#start_date"));
    form.append($("#end_date"));
    form.submit();
}

Report.plot_report_graph = function(elem_id, data) {
    $.jqplot.config.enablePlugins = true;
    $.jqplot(elem_id, [data], {
        axes: {
            xaxis: {
                renderer: $.jqplot.DateAxisRenderer,
                tickRenderer: $.jqplot.CanvasAxisTickRenderer,
                tickOptions: {
                    formatString: '%Y-%m-%d',
                    angle: -60,
                }
            }
        }
    });
}

/*
calculates the total in a jqplot_data given by the server.
This functions returns the sum of all the second element in
the internal lists of data.
*/
Report.calculate_total = function(data) {
    var total = 0;
    for(i=0; i<data.length; i++)
        total += data[i][1];
    return total;
}
