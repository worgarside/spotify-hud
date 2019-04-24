let timeInSeconds = 121;

function checkMusicPlaying() {
    return new Promise((resolve, reject) => {
        let resolutionValue = false;
        let criticalError = false;
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
                        resolutionValue = 'music';
                    }
                },
                error: (err) => {
                    criticalError = true;
                    reject(err);
                }
            });
        });

        if (!criticalError) {
            if (returnCount === window.mediaPlayers.length) resolve(resolutionValue);


            const responseChecker = setInterval(() => {
                if (returnCount === window.mediaPlayers.length) {
                    clearInterval(responseChecker);
                    resolve(resolutionValue);
                }
            }, 250);
        }
    })
}

function checkTvPlaying() {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve('tv');
        }, 3000);
    })
}

function str_pad_left(string, pad, length) {
    return (new Array(length + 1).join(pad) + string).slice(-length);
}

function shutdown() {
    window.location.href = '/shutdown';
}


const countdown = setInterval(() => {
    timeInSeconds--;
    let displayMinutes = Math.floor(timeInSeconds / 60);
    let displaySeconds = timeInSeconds % 60;

    $('.warning-countdown__clock').text(`${str_pad_left(displayMinutes, '0', 2)}:${str_pad_left(displaySeconds, '0', 2)}`);

    if (timeInSeconds % 5 === 0) {
        Promise.all([checkMusicPlaying(), checkTvPlaying()])
            .then(values => {
                console.log(values);
            })
            .catch(err => {
                console.log(err);
            });
    }

    if (timeInSeconds <= 0) {
        clearInterval(countdown);
        shutdown();
    }

}, 1000);