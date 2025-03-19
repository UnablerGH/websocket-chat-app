let ws;
let nickname;
let room;

document.getElementById("connectBtn").onclick = function() {
    nickname = document.getElementById("nickname").value.trim();
    room = document.getElementById("room").value.trim();
    if (nickname === "" || room === "") {
        alert("Proszę wypełnić oba pola!");
        return;
    }
    // Nawiązanie połączenia WebSocket
    ws = new WebSocket(`ws://${location.host}/ws/${room}/${nickname}`);

    ws.onopen = function() {
        console.log("Połączono");
        // Powiadomienie o dołączeniu do pokoju
        let joinMsg = {
            type: "notification",
            message: nickname + " dołączył do pokoju " + room
        }
        ws.send(JSON.stringify(joinMsg));
        document.getElementById("login").style.display = "none";
        document.getElementById("chat").style.display = "block";
    };

    ws.onmessage = function(event) {
        let data = JSON.parse(event.data);
        if (data.type === "typing") {
            // Wyświetlamy informację o pisaniu tylko, gdy pochodzi od innego użytkownika
            if (data.nickname !== nickname) {
                document.getElementById("typingIndicator").innerText = data.nickname + " pisze...";
                setTimeout(() => {
                    document.getElementById("typingIndicator").innerText = "";
                }, 1000);
            }
        } else if (data.type === "chat") {
            addMessage(data, data.nickname === nickname);
        } else if (data.type === "notification") {
            addNotification(data.message);
        } else if (data.type === "image") {
            addImageMessage(data, data.nickname === nickname);
        }
    };

    ws.onclose = function() {
        addNotification("Rozłączono z serwerem");
    }
};

document.getElementById("messageInput").addEventListener("keydown", function() {
    let typingMsg = {
        type: "typing",
        nickname: nickname
    };
    ws.send(JSON.stringify(typingMsg));
});

document.getElementById("messageForm").onsubmit = function(event) {
    event.preventDefault();
    let message = document.getElementById("messageInput").value;
    let file = document.getElementById("imageInput").files[0];

    // Jeśli wybrano obrazek, odczytujemy go jako base64 i wysyłamy
    if (file) {
        let reader = new FileReader();
        reader.onload = function(e) {
            let imageData = e.target.result;
            let msgData = {
                type: "image",
                nickname: nickname,
                timestamp: new Date().toLocaleString(),
                data: imageData
            };
            ws.send(JSON.stringify(msgData));
            // Nie dodajemy wiadomości lokalnie, czekamy na broadcast
        };
        reader.readAsDataURL(file);
        document.getElementById("imageInput").value = "";
    }
    // Jeśli wpisano wiadomość tekstową
    if (message.trim() !== "") {
        let msgData = {
            type: "chat",
            nickname: nickname,
            timestamp: new Date().toLocaleString(),
            message: message
        };
        ws.send(JSON.stringify(msgData));
        // Usuwamy wpisany tekst – wiadomość pojawi się po broadcastzie
        document.getElementById("messageInput").value = "";
    }
};

function addMessage(data, isSelf = false) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    msgDiv.classList.add(isSelf ? "sent" : "received");
    msgDiv.innerHTML = `<strong>${data.nickname}</strong> <small>${data.timestamp}</small><br>${data.message}`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addImageMessage(data, isSelf = false) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");
    msgDiv.classList.add("message");
    msgDiv.classList.add(isSelf ? "sent" : "received");
    msgDiv.innerHTML = `<strong>${data.nickname}</strong> <small>${data.timestamp}</small><br>
                        <img src="${data.data}" alt="obrazek" style="max-width: 100%;">`;
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addNotification(text) {
    let chatBox = document.getElementById("chat-box");
    let notifDiv = document.createElement("div");
    notifDiv.classList.add("notification");
    notifDiv.innerText = text;
    chatBox.appendChild(notifDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}
