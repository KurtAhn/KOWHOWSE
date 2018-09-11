function schoice_toggle(button) {
    button.blur();
    input = $(button).find('input');
    input.attr('checked', 'true');
    input.trigger('change');
    // alert($(button).find('input').attr('checked'));
    // alert($(button).attr('checked'));
}

function schoice_input_change(input) {
    alert('hi');
    // if (input.attr('checked'))
    //     input.parentElement.attr('checked');
    // else
    //     input.parentElement.removeAttr('checked');
}
