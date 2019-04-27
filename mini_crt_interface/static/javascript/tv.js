let nowPlaying;
let estimatedPosition = 0;
const updateDelay = 2500;

function array_move(arr, old_index, new_index) {
    if (new_index >= arr.length) {
        let k = new_index - arr.length + 1;
        while (k--) {
            arr.push(undefined);
        }
    }
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}

function scrollElement(elem) {
    const elemWidth = $(elem).width();
    const outerWidth = $(elem).parent().width();

    if (elemWidth < outerWidth) {
        $(elem).css('left', 0);
        setTimeout(() => {
            scrollElement(elem);
        }, 5000);
    } else {
        const time = (elem.position().left !== 0 ? elemWidth + outerWidth : elemWidth) * 5;

        $(elem).animate(
            {
                'left': -elemWidth
            },
            {
                duration: time,
                easing: 'linear',
                complete: () => {
                    $(elem).css('left', '100%');
                    scrollElement(elem);
                }
            }
        )
    }
}

function checkPlex() {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: '/api/tv',
            type: 'GET',
            contentType: 'application/json',
            data: {},
            success: (response) => {
                if (!response.hasOwnProperty('error')) {
                    resolve(response);
                } else {
                    console.log(`Error: ${JSON.stringify(response)}`);
                }
            },
            error: (err) => {
                console.log(`Error: ${JSON.stringify(err)}`);
            }
        });
    });
}

function updateState() {
    checkPlex()
        .then((activeContent) => {
            $('.art').attr('src', activeContent['art']);
            $('.title__primary').text(activeContent['attributes']);
        })
        .catch((err) => {
            console.log(err);
        });
}

function updateGUI(activePlayer) {

    if (activePlayer !== undefined) {
        if (nowPlaying === undefined || nowPlaying['attributes']['media_content_id'] !== activePlayer['attributes']['media_content_id']) {
            estimatedPosition = activePlayer['attributes']['media_position'];
            $('.artwork').attr('src', `${hassUrl}${activePlayer['attributes']['entity_picture']}`);
            $('#title').text(activePlayer['attributes']['media_title']);
            $('#artist').text(activePlayer['attributes']['media_artist']);
        }

        const glitchImages = $('.artwork.glitch');
        const paused = $('.paused-container');

        switch (activePlayer['state']) {
            case 'playing':
                glitchImages.css('display', 'initial');
                paused.css('display', 'none');
                estimatedPosition += updateDelay / 1000;
                break;
            case 'paused':
                glitchImages.css('display', 'none');
                paused.css('display', 'flex');
                break;
            default:
                break;
        }

        let mediaProgress = 100 * estimatedPosition / activePlayer['attributes']['media_duration'];

        if (mediaProgress > 100) {
            mediaProgress = 100;
        }

        $('#current-progress').css('width', `${mediaProgress}%`);

        const volume = activePlayer['attributes']['volume_level'];

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
    nowPlaying = activePlayer;
}

updateState();

const updateTimer = setInterval(() => {
    console.log('');
    updateState()
    ;
}, updateDelay);

// setTimeout(() => {
//     scrollElement($('#title'));
// }, updateDelay);