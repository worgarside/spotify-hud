let nowPlaying;
let estimatedPosition = 0;

function array_move(arr, old_index, new_index) {
    if (new_index >= arr.length) {
        let k = new_index - arr.length + 1;
        while (k--) {
            arr.push(undefined);
        }
    }
    arr.splice(new_index, 0, arr.splice(old_index, 1)[0]);
}

function getActivePlayer() {
    return new Promise((resolve, reject) => {
        let activePlayer = undefined;
        let returnCount = 0;

        window.mediaPlayers.forEach(player => {
            $.ajax({
                url: `${hassUrl}/api/states/${player}`,
                type: 'GET',
                beforeSend: xhr => {
                    xhr.setRequestHeader('Authorization', `Bearer ${hassAccessToken}`);
                },
                contentType: 'application/json',
                data: {},
                success: (state) => {
                    returnCount++;
                    if (state['state'] !== 'off' && state['state'] !== 'idle') {
                        activePlayer = state;
                    }
                },
                error: (err) => {
                    returnCount++;

                    console.log(`Error: ${JSON.stringify(err)}`); // TODO make this better
                    reject();
                }
            });
        });

        if (returnCount === window.mediaPlayers.length) {
            console.log('Best case');
            resolve(activePlayer);
        }

        const responseChecker = setInterval(() => {
            if (returnCount === window.mediaPlayers.length) {
                clearInterval(responseChecker);
                console.log('resolving');
                resolve(activePlayer);
            } else {
                console.log(`${returnCount} returned, waiting...`);
            }
        }, 250);
    });
}

function updateState() {
    getActivePlayer()
        .then((activePlayer) => {
            if (activePlayer) {
                if (mediaPlayers[0] !== activePlayer['entity_id']) {
                    array_move(
                        mediaPlayers,
                        window.mediaPlayers.indexOf(activePlayer['entity_id']),
                        0
                    );
                }

                updateGUI(activePlayer);
            } else {
                console.log('there are no active players');
                clearInterval(updateTimer);
                window.location.href = '/no_content';
            }

        })
        .catch(() => {
            clearInterval(updateTimer);
            window.location.href = '/no_content';
        });
}

function updateGUI(activePlayer) {

    if (activePlayer !== undefined) {
        if (nowPlaying === undefined || nowPlaying['attributes']['media_content_id'] !== activePlayer['attributes']['media_content_id']) {
            estimatedPosition = activePlayer['attributes']['media_position'];
            $('.artwork').attr('src', `${hassUrl}${activePlayer['attributes']['entity_picture']}`);
            $('.title.title__primary').text(activePlayer['attributes']['media_title']);
            $('.title.title__secondary').text(activePlayer['attributes']['media_artist']);
        }

        const glitchImages = $('.artwork.glitch');
        const paused = $('.paused-container');

        switch (activePlayer['state']) {
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
;}, updateDelay);

setTimeout(() => {
    scrollElement($('.title.title__primary'));
}, updateDelay);