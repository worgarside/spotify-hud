const updateDelay = 2500;
let allowScroll = true;

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