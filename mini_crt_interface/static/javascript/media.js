const updateDelay = 2500;
let allowScroll = true;
let updateTimer;

function scrollElement(elem) {
    const elemWidth = $(elem).width();
    const outerWidth = $(elem).parent().width();

    if (elemWidth < outerWidth || !allowScroll) {
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

function updateState() {
    getActivePlayer()
        .then((activeContent) => {
            updateGUI(activeContent);
        })
        .catch((err) => {
            console.log(err);
            clearInterval(updateTimer);
            window.location.href = '/no_content';
        });
}

$(() => {
    updateTimer = setInterval(() => {
        console.log('');
        updateState();
    }, updateDelay);

    setTimeout(() => {
        scrollElement($('.title.title__primary'));
    }, updateDelay);

    updateState();
});
