// --- Global State ---
let socket;
let mediaRecorder;
let audioContext;
let audioQueue = [];
let isSpeaking = false;

// --- North Indian Chart Layout (House Polygons) ---
// A 400x400 Grid.
// House 1 is Top Diamond.
// Coordinates are [x,y] points string.
const HOUSE_PATHS = {
    1:  "200,200 100,100 200,0 300,100",   // Top Diamond (Lagna)
    2:  "100,100 0,0 200,0",               // Top Left Triangle
    3:  "0,0 0,200 100,100",               // Top Left Side Triangle
    4:  "200,200 100,100 0,200 100,300",   // Left Diamond
    5:  "0,200 0,400 100,300",             // Bottom Left Side Triangle
    6:  "100,300 0,400 200,400",           // Bottom Left Triangle
    7:  "200,200 100,300 200,400 300,300", // Bottom Diamond
    8:  "200,400 400,400 300,300",         // Bottom Right Triangle
    9:  "400,400 400,200 300,300",         // Bottom Right Side Triangle
    10: "200,200 300,300 400,200 300,100", // Right Diamond
    11: "400,200 400,0 300,100",           // Top Right Side Triangle
    12: "300,100 400,0 200,0"              // Top Right Triangle
};

// Text Placement coordinates (Centroids)
const HOUSE_CENTERS = {
    1:  [200, 100], 2:  [100, 50],  3:  [50, 100],
    4:  [100, 200], 5:  [50, 300],  6:  [100, 350],
    7:  [200, 300], 8:  [300, 350], 9:  [350, 300],
    10: [300, 200], 11: [350, 100], 12: [300, 50]
};

// --- Initialization ---
function initChart() {
    const svg = document.getElementById('kundliSvg');
    svg.innerHTML = ''; 

    // Draw Houses
    for (let i = 1; i <= 12; i++) {
        // Polygon
        let poly = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        poly.setAttribute("points", HOUSE_PATHS[i]);
        poly.setAttribute("class", "house-poly");
        poly.setAttribute("id", `house-${i}`);
        svg.appendChild(poly);

        // Text Group
        let text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", HOUSE_CENTERS[i][0]);
        text.setAttribute("y", HOUSE_CENTERS[i][1]);
        text.setAttribute("id", `text-${i}`);
        text.textContent = ""; // Filled later
        svg.appendChild(text);
        
        // House Number (Small)
        let num = document.createElementNS("http://www.w3.org/2000/svg", "text");
        num.setAttribute("x", HOUSE_CENTERS[i][0]);
        num.setAttribute("y", HOUSE_CENTERS[i][1] + 15); // Slightly below
        num.setAttribute("fill", "#555");
        num.setAttribute("font-size", "10");
        num.textContent = i;
        svg.appendChild(num);
    }
    
    // Draw Outer Border
    let border = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    border.setAttribute("x", "2"); border.setAttribute("y", "2");
    border.setAttribute("width", "396"); border.setAttribute("height", "396");
    border.setAttribute("fill", "none");
    border.setAttribute("stroke", "#d4af37");
    border.setAttribute("stroke-width", "2");
    svg.appendChild(border);
}

function updateChartData(visualData) {
    // visualData = { "1": ["Sun", "Merc"], "2": [], ... }
    for (let i = 1; i <= 12; i++) {
        const el = document.getElementById(`text-${i}`);
        const planets = visualData[i.toString()] || [];
        el.textContent = planets.join(" ");
    }
}

function highlightHouse(houseStr) {
    // Expected input: "HOUSE_7" or "ASCENDANT"
    
    // Clear old
    document.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));

    if (!houseStr) return;

    let targetId = null;
    if (houseStr.includes("HOUSE_")) {
        let num = houseStr.split("_")[1];
        targetId = `house-${num}`;
    } else if (houseStr.includes("ASCENDANT")) {
        targetId = `house-1`; // North Indian Lagna is always Top
    }

    if (targetId) {
        let el = document.getElementById(targetId);
        if (el) el.classList.add('highlight');
    }
}

// --- Connection Logic ---
async function startSession() {
    initChart();
    
    const btn = document.getElementById('connectBtn');
    const name = document.getElementById('userName').value;
    const date = document.getElementById('birthDate').value;
    const time = document.getElementById('birthTime').value;
    const location = document.getElementById('birthPlace').value;

    btn.innerText = "ALIGNING STARS...";

    try {
        const res = await fetch('http://127.0.0.1:8000/api/v1/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, date, time, location })
        });
        const data = await res.json();
        
        document.getElementById('setupPanel').classList.add('hidden');
        document.getElementById('gamePanel').style.display = 'flex';
        
        connectWS(data.session_id);
        
        // Fill chart if data is present (assuming API sends it, or WS will send it)
        // For now, WS greeting usually triggers first logic.

    } catch (e) {
        alert("Error: " + e);
        btn.innerText = "RETRY";
    }
}

function connectWS(id) {
    socket = new WebSocket(`ws://127.0.0.1:8000/api/v1/game/ws/${id}`);
    socket.binaryType = 'arraybuffer'; // Using AudioContext flow

    socket.onopen = () => updateStatus("CONNECTED TO ETHER");
    
    socket.onmessage = (event) => {
        if (typeof event.data === "string") {
            handleJson(JSON.parse(event.data));
        } else {
            playAudioChunk(event.data);
        }
    };
}

// --- Audio Logic (Low Latency Queue) ---
let nextStartTime = 0;

function initAudioCtx() {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
}

function playAudioChunk(buffer) {
    initAudioCtx();
    const float32 = new Float32Array(new Int16Array(buffer).length);
    const int16 = new Int16Array(buffer);
    for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768.0;

    const audioBuf = audioContext.createBuffer(1, float32.length, 24000);
    audioBuf.getChannelData(0).set(float32);
    
    const source = audioContext.createBufferSource();
    source.buffer = audioBuf;
    source.connect(audioContext.destination);
    
    let start = Math.max(audioContext.currentTime, nextStartTime);
    source.start(start);
    nextStartTime = start + audioBuf.duration;
}

// --- Message Handling ---
function handleJson(msg) {
    if (msg.status === "ai_speaking") {
        updateStatus("ACHARYA IS SPEAKING...");
        document.getElementById('chartContainer').classList.add('speaking-glow');
        // Extract Focus?
        // In this architecture, backend sends focus inside ai_response_text usually, 
        // OR we can parse it here if backend sends a specific "focus" field.
    } 
    else if (msg.status === "ai_finished_speaking") {
        updateStatus("LISTENING...");
        document.getElementById('chartContainer').classList.remove('speaking-glow');
        highlightHouse(null); // Remove highlight
    }
    else if (msg.status === "ai_response_text") {
        // PARSE FOCUS SIGNAL: [FOCUS:HOUSE_7]
        let text = msg.text;
        let focusMatch = text.match(/\[FOCUS:(.*?)\]/);
        
        if (focusMatch) {
            let focusTarget = focusMatch[1];
            highlightHouse(focusTarget);
            text = text.replace(/\[FOCUS:.*?\]/, ""); // Clean UI text
        }
        
        addLog("Acharya", text);
    }
    else if (msg.status === "user_response_text") {
        addLog("You", msg.text);
    }
    
    // If using the visual_data from backend helper:
    // Note: We need to ensure the backend sends "visual_data" in a message or initial handshake.
    // For simplicity, assume session start or greeting passes chart data context if implemented.
}

function updateStatus(txt) { document.getElementById('status').innerText = txt; }

function addLog(role, text) {
    let div = document.createElement('div');
    div.className = `msg ${role.toLowerCase()}`;
    div.innerHTML = `<strong>${role}:</strong> ${text}`;
    document.getElementById('transcript').appendChild(div);
}

// --- Mic ---
function startMic() {
    initAudioCtx();
    navigator.mediaDevices.getUserMedia({audio:true}).then(stream => {
        mediaRecorder = new MediaRecorder(stream, {mimeType: 'audio/webm'});
        mediaRecorder.ondataavailable = e => {
            if (socket && socket.readyState === 1) socket.send(e.data);
        };
        mediaRecorder.start(250);
        socket.send(JSON.stringify({action: 'start_speaking'}));
        updateStatus("RECORDING...");
    });
}

function stopMic() {
    if (mediaRecorder) {
        mediaRecorder.stop();
        socket.send(JSON.stringify({action: 'stop_speaking'}));
        updateStatus("TRANSMITTING...");
    }
}