let timeInSeconds = 121;

function str_pad_left(string, pad, length) {
    return (new Array(length + 1).join(pad) + string).slice(-length);
}

function shutdown(){
    console.log('bye');
}


const countdown = setInterval(() => {
    timeInSeconds--;
    let displayMinutes = Math.floor(timeInSeconds / 60);
    let displaySeconds = timeInSeconds % 60;

    $('.warning-countdown__clock').text(`${str_pad_left(displayMinutes, '0', 2)}:${str_pad_left(displaySeconds, '0', 2)}`);

    if (timeInSeconds <= 0){
        clearInterval(countdown);
        shutdown();
    }

}, 1000);