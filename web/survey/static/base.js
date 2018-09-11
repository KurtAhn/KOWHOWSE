$(document).ready(function() {
    // Set up play
    $('.play').each(function() {
        $(this).click(function(event) {
            event.stopPropagation();
            audio_play(this);
        })
    });
});
