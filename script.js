let assetId = null;
let currentRoom = null;
let chatHistory = {};

// Show Status
function updateStatus(message, statusClass) {
    const statusElement = document.getElementById("status");
    statusElement.textContent = message;
    statusElement.className = "status " + statusClass;
    statusElement.style.display = "block";
}

function uploadFile() {
    let fileInput = document.getElementById("fileInput"); // Updated ID for file input
    if (!fileInput.files.length) {
        alert("Please select a file.");
        return;
    }

    let file = fileInput.files[0];
    // Check if the file is either a PDF or a TXT
    if (file.type !== "application/pdf" && file.type !== "text/plain") {
        alert("Please upload a valid PDF or TXT file.");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    let roomName = file.name.replace(/\.[^/.]+$/, ""); // Remove file extension
    chatHistory[roomName] = [];

    updateStatus("Uploading file...", "uploading");

    fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.asset_id) {
            assetId = data.asset_id;
            currentRoom = roomName;
            updateRoomList();
            switchRoom(roomName);

            updateStatus("Initializing document...", "initializing");

            setTimeout(() => {
                updateStatus("Ready to Answer", "ready");
            }, 2000);
        } else {
            updateStatus("Error uploading file", "error");
            alert("Error uploading file.");
        }
    })
    .catch(error => {
        console.error("Error:", error);
        updateStatus("Error uploading file", "error");
    });
}

function updateRoomList() {
    const roomList = document.getElementById("roomList");
    roomList.innerHTML = Object.keys(chatHistory)
        .map(room => `<div class="room" onclick="switchRoom('${room}')">${room}</div>`)
        .join("");
}

function switchRoom(room) {
    currentRoom = room;
    document.getElementById("chatHistory").innerHTML = chatHistory[room]
        .map(msg => `<div class="message ${msg.type}">${msg.text}</div>`)
        .join("");
}

async function askQuestion() {
    const questionInput = document.getElementById("questionInput");
    const question = questionInput.value.trim();

    if (question === "") {
        alert("Please enter a question.");
        return;
    }

    chatHistory[currentRoom].push({ type: "user", text: question });
    updateChatHistory();

    // Add "Thinking..." message
    const thinkingMsg = { type: "bot", text: "Thinking..." };
    chatHistory[currentRoom].push(thinkingMsg);
    updateChatHistory();

    questionInput.value = "";

    try {
        const response = await fetch("http://127.0.0.1:5000/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ asset_id: assetId, question: question })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let answerText = "";

        // Remove "Thinking..." message
        chatHistory[currentRoom] = chatHistory[currentRoom].filter(msg => msg.text !== "Thinking...");
        updateChatHistory();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            let chunk = decoder.decode(value, { stream: true });
            answerText += chunk;

            console.log("Received chunk:", chunk); // Log the chunk

            if (chatHistory[currentRoom].length > 0 && chatHistory[currentRoom].slice(-1)[0].type === "bot") {
                chatHistory[currentRoom].slice(-1)[0].text = answerText;
            } else {
                chatHistory[currentRoom].push({ type: "bot", text: answerText });
            }
            updateChatHistory();
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error communicating with the backend.");
    }
}

function updateChatHistory() {
    document.getElementById("chatHistory").innerHTML = chatHistory[currentRoom]
        .map(msg => `<div class="message ${msg.type}">${msg.text}</div>`)
        .join("");

    // Scroll to the latest message
    const chatHistoryDiv = document.getElementById("chatHistory");
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
}

// Allow pressing "Enter" to send a message
document.getElementById("questionInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        askQuestion();
    }
});
