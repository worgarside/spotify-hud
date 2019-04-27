let timeInSeconds = 91;

function checkMusicPlaying() {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: '/api/music',
            type: 'GET',
            contentType: 'application/json',
            data: {},
            success: (response) => {
                if (response) {
                    resolve(response);
                } else {
                    reject();
                }
            },
            error: (err) => {
                console.log(`Error: ${JSON.stringify(err)}`);
            }
        });
    });
}

function checkTvPlaying() {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: '/api/tv',
            type: 'GET',
            contentType: 'application/json',
            data: {},
            success: (response) => {
                if (response && !response.hasOwnProperty('error')) {
                    resolve(response);
                } else {
                    reject();
                }
            },
            error: (err) => {
                console.log(`Error: ${JSON.stringify(err)}`);
            }
        });
    });
}

function get_endpoint(endpoint) {
    $.ajax({
        url: endpoint,
        type: 'GET',
        contentType: 'application/json',
        success: (response) => {
            return response;
        },
        error: (err) => {
            console.log(`Error: ${JSON.stringify(err)}`);
        }
    });
}

function str_pad_left(string, pad, length) {
    return (new Array(length + 1).join(pad) + string).slice(-length);
}

setInterval(() => {
    timeInSeconds--;

    if (timeInSeconds > 0) {

        let displayMinutes = Math.floor(timeInSeconds / 60);
        let displaySeconds = timeInSeconds % 60;

        $('.warning-countdown__clock').text(`${str_pad_left(displayMinutes, '0', 2)}:${str_pad_left(displaySeconds, '0', 2)}`);
    }

    if (timeInSeconds % 5 === 0) {
        checkMusicPlaying()
            .then(() => {
                get_endpoint('/crt_on');
                window.location.href = '/music';
            })
            .catch(() => {
                checkTvPlaying()
                    .then(() => {
                        get_endpoint('/crt_on');
                        window.location.href = '/tv';
                    })
                    .catch(() => {
                    })
            });
    }

    if (timeInSeconds === 0) {
        get_endpoint('/shutdown');
    }

}, 1000);