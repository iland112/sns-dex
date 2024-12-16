var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
    window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.VideoImageRenderer = function (props) {
    var url = props.value
    return React.createElement(
        "span",
        null,
        React.createElement("img", {src: url, style: {width: '100px', height: "auto", filter: "brightness(1.1)"} })
    )
}

dagcomponentfuncs.CountyFlagRenderer = function (props) {
    let flag_image = props.value.toLowerCase() + ".png";
    return React.createElement(
        "img",
        {
            src: "https://flagcdn.com/32x24/" + flag_image,
            with: "32",
            height: "24",
            alt: props.value
        }
    );
}

dagcomponentfuncs.VideoIdRenderer = function (props) {
    var strArr = props.value.split(":")
    var id = strArr[0]
    var title = strArr[1]
    return React.createElement(
        'a',
        {href: '/video/' + id},
        title
    )
}

dagcomponentfuncs.ChannelIdRenderer = function (props) {
    var strArr = props.value.split(":")
    var id = strArr[0]
    var title = strArr[1]
    return React.createElement(
        'a',
        {href: '/channel/' + id},
        title
    )
}