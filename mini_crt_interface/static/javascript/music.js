let estimatedPosition = 0;
let lastKnownPosition = 0;
const glitchImages = $('.artwork.glitch');
const paused = $('.paused-container');

function getActivePlayer() {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: '/api/music',
            type: 'GET',
            contentType: 'application/json',
            data: {},
            success: (response) => {
                if (!response) {
                    reject('No active music playing');
                } else {
                    resolve(response);
                }
            },
            error: (err) => {
                console.log(`Error: ${JSON.stringify(err)}`);
            }
        });
    });
}

function updateGUI(activeContent) {
    if (activeContent['position'] !== lastKnownPosition){
        lastKnownPosition = activeContent['position'];
        estimatedPosition = activeContent['position'];
    }

    $('.artwork').attr('src', activeContent['artwork']);
    $('.title.title__primary').text(activeContent['title']);
    $('.title.title__secondary').text(activeContent['artist']);

    switch (activeContent['state']) {
        case 'playing':
            glitchImages.css('display', 'initial');
            paused.css('display', 'none');
            estimatedPosition += updateDelay / 1000;
            allowScroll = true;
            break;
        case 'paused':
            glitchImages.css('display', 'none');
            paused.css('display', 'flex');
            allowScroll = false;
            break;
        default:
            break;
    }

    let mediaProgress = 100 * estimatedPosition / activeContent['duration'];

    if (mediaProgress > 100) {
        mediaProgress = 100;
    }

    $('#current-progress').css('width', `${mediaProgress}%`);

    const volume = activeContent['volume'];

    for (let i = 1; i < 11; i++) {
        if (i <= volume * 10) {
            $(`#volume-meter-${i}`).css('background-color', '#989898');
        } else {
            $(`#volume-meter-${i}`).css('background-color', 'unset');
        }
    }

    const volumeSvg = $('#volume-icon-svg');

    switch (true) {
        case (volume === 0):
            volumeSvg.attr('href', '#volume-mute');
            break;
        case (volume < (1 / 3)):
            volumeSvg.attr('href', '#volume-low');
            break;
        case (volume < (2 / 3)):
            volumeSvg.attr('href', '#volume-medium');
            break;
        case (volume <= 1):
            volumeSvg.attr('href', '#volume-high');
            break;
        default:
            volumeSvg.attr('href', '#volume-low');
    }
}