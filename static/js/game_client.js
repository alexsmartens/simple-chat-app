let rooms =  JSON.parse(document.getElementById("chat_client").getAttribute("rooms").replace(/'/g, '"')),
    username = "",
    currentRoomName = "",
    socket = io.connect(window.location.href),
    noMsgHtml = "<h1 id=\"no-msg-boilerplate\" style=\"color: #ccc\">No New Messages </h1>";

// OnFirstConnection
socket.on("connect", function () {
    // Select default room
    navigate2NewRoom(rooms[0]);
});

// OnLoginClicked function
$("#noname_form").on("submit", function (e) {
    e.preventDefault()
    username = $("input.username").val();
    if (username.length) {
        $("[id^=noname]").prop("disabled", true);
        $("[id^=registered]").removeAttr('disabled');

        joinRoom(currentRoomName);
    };
});

// OnSendMessageClicked function
function send_msg() {
    let msg_element = $("textarea.msg");
    if (msg_element.val().length) {
        let msg2server = {
            username: username,
            msg: msg_element.val(),
            room: currentRoomName,
        };
        socket.emit("server_receive", msg2server);
        // Empty message field
        msg_element.val("").focus();
    };
};

// Receive a message
socket.on("message", function (msg2client, callback) {
    if (typeof msg2client.msg == "string") {
        // Clean up the initial message
        if ($("#no-msg-boilerplate").length == 1)
            $("#no-msg-boilerplate").remove();

        // Message content and style
        let msg_inf = {
            bg_type: msg2client.username === username ? "bg-primary " : msg2client.username ? "bg-secondary " : "bg-white ",
            style: msg2client.username === username ? "margin-left: 20%; " : "margin-right:20%; ",
            font: msg2client.username === username ? "" : msg2client.username ? "" : "font-italic ",
            text_color: msg2client.username ? "text-white " : "text-dark ",
            username: msg2client.username ? "<b>" + msg2client.username + "</b> " : "",
            msg: msg2client.msg,
        }
        // Post a new message
        $("div.msg-wrapper").append(
            "<div class='chat_msg " + msg_inf.bg_type + msg_inf.font + msg_inf.text_color + "' style='" + msg_inf.style + "'>" +
            msg_inf.username + msg_inf.msg +
            "</div>"
        );
    } else
        console.error("Received message has unexpected content");

    // Call back to the server (just for testing)
    if (callback)
        callback({
            username: username,
            new_info: "info",
        });
});

// Room navigation
function navigate2NewRoom(newRoomName) {
    let oldRoomName = currentRoomName.length ? currentRoomName : "";
    if (newRoomName == currentRoomName) {
    } else {
        let oldRoomButton = $(`#nav-room-${oldRoomName}`),
            newRoomButton = $(`#nav-room-${newRoomName}`);
        // Clean up old messages
        if ($("#no-msg-boilerplate").length == 1) {
        } else {
            $(".chat_msg").remove();
            $(".msg-wrapper").append(noMsgHtml);
        };
        // Update room selection on the nav bar
        if (oldRoomButton.length === 1)
            $(oldRoomButton).parent()[0].className = "nav-item";
        $(newRoomButton).parent()[0].className = "nav-item active";
        currentRoomName = newRoomName;
        if (username.length) {
            leaveRoom(oldRoomName);
            joinRoom(newRoomName);
        };
    };
};

// Join room
function joinRoom(roomName) {
    socket.emit(
        "join",
        {
            "username": username,
            "room": roomName,
        }
    );
};

// Leave room
function leaveRoom(roomName) {
    socket.emit(
        "leave",
        {
            "username": username,
            "room": roomName,
        }
    );
};
