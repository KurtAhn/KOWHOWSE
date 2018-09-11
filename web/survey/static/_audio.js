function audio_play(button) {
    button.blur();
    audio = $(button).parent().children('audio')[0];
    icon = $(button).children('span')[0];

    if ($(icon).hasClass('glyphicon-play')) {
        $(icon).removeClass('glyphicon-play').addClass('glyphicon-pause');
        audio.addEventListener("ended", function() {
            $(icon).removeClass('glyphicon-pause').addClass('glyphicon-play');
        });
        audio.play();
    } else {
        $(icon).removeClass('glyphicon-pause').addClass('glyphicon-play');
        audio.pause();
    }
}
