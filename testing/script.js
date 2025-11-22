// --- Global State ---
let socket;
let mediaRecorder;
let audioContext;
let audioQueue = [];
let isSpeaking = false;
let chartData = null; // Store chart data for later use

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

function populateChartFromPlanetData(chartFull) {
    // chartFull is the full chart object with planets data
    // planets: { sun: {house: 1, ...}, moon: {house: 2, ...}, ... }
    
    console.log("[Chart] 🌍 Populating chart from planet data");
    
    if (!chartFull || !chartFull.planets) {
        console.warn("[Chart] ⚠️ No planet data available");
        return;
    }
    
    // Clear all houses first
    for (let i = 1; i <= 12; i++) {
        const el = document.getElementById(`text-${i}`);
        if (el) el.textContent = "";
    }
    
    // Build map of houses to planets
    const housePlanets = {};
    for (let i = 1; i <= 12; i++) {
        housePlanets[i] = [];
    }
    
    // Populate from planets
    for (const [planetKey, planetData] of Object.entries(chartFull.planets)) {
        const house = planetData.house;
        // Capitalize planet name
        const planetName = planetKey.charAt(0).toUpperCase() + planetKey.slice(1);
        
        if (house >= 1 && house <= 12) {
            housePlanets[house].push(planetName);
            console.log(`[Chart] ✓ Placed ${planetName} in House ${house}`);
        }
    }
    
    // Display planets in each house
    for (let i = 1; i <= 12; i++) {
        const el = document.getElementById(`text-${i}`);
        if (el && housePlanets[i].length > 0) {
            el.textContent = housePlanets[i].join(" ");
            console.log(`[Chart] 📍 House ${i}: ${housePlanets[i].join(", ")}`);
        }
    }
    
    console.log("[Chart] ✅ Chart populated with planets");
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

function displayPlanetsInHouses(houses, planets) {
    // Display planets for specified houses and highlight them.
    // houses: array of house numbers [7, 10]
    // planets: array of planet names ['Venus', 'Saturn']
    // chartData: the full chart data object with planet positions
    
    console.log(`[Chart] 🏠 Highlighting houses: ${houses}`);
    
    // Clear old highlights
    document.querySelectorAll('.highlight').forEach(el => el.classList.remove('highlight'));
    
    // Highlight the mentioned houses only - don't change planet display
    houses.forEach(houseNum => {
        const el = document.getElementById(`house-${houseNum}`);
        if (el) {
            el.classList.add('highlight');
            console.log(`[Chart] ✓ Highlighted House ${houseNum}`);
        }
    });
}

// --- Connection Logic ---
async function startSession() {
    initChart();
    
    const btn = document.getElementById('connectBtn');
    const name = document.getElementById('userName').value;
    const date = document.getElementById('birthDate').value;
    const time = document.getElementById('birthTime').value;
    const location = document.getElementById('birthPlace').value;

    console.log(`[Session] 🌟 Starting session - Name: ${name}, Date: ${date}, Time: ${time}, Location: ${location}`);
    btn.innerText = "ALIGNING STARS...";

    try {
        const res = await fetch('http://127.0.0.1:8000/api/v1/game/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, date, time, location })
        });
        const data = await res.json();
        console.log(`[Session] ✅ Session started with ID: ${data.session_id}`);
        
        document.getElementById('setupPanel').classList.add('hidden');
        document.getElementById('gamePanel').style.display = 'flex';
        
        // Start constellation animation
        if (typeof startConstellations === 'function') {
            console.log("[Session] 🌌 Starting constellation background");
            startConstellations();
        } else {
            console.warn("[Session] ⚠️ startConstellations not available");
        }
        
        connectWS(data.session_id);

    } catch (e) {
        console.error(`[Session] ❌ Error: ${e}`);
        alert("Error: " + e);
        btn.innerText = "RETRY";
    }
}

function connectWS(id) {
    socket = new WebSocket(`ws://127.0.0.1:8000/api/v1/game/ws/${id}`);
    socket.binaryType = 'arraybuffer'; // Using AudioContext flow

    socket.onopen = () => {
        console.log("[WS] 🟢 WebSocket connected successfully");
        updateStatus("CONNECTED TO ETHER");
    };
    
    socket.onmessage = (event) => {
        if (typeof event.data === "string") {
            console.log("[WS] 📨 Received JSON:", event.data.substring(0, 100));
            handleJson(JSON.parse(event.data));
        } else {
            console.log(`[WS] 🔊 Received audio: ${event.data.byteLength} bytes`);
            playAudioChunk(event.data);
        }
    };
    
    socket.onerror = (error) => {
        console.error("[WS] ❌ WebSocket error:", error);
        updateStatus("CONNECTION ERROR");
    };
    
    socket.onclose = () => {
        console.log("[WS] 🔴 WebSocket closed");
        updateStatus("DISCONNECTED");
    };
}

// --- Audio Logic (Low Latency Queue) ---
let nextStartTime = 0;

function initAudioCtx() {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
}

function playAudioChunk(buffer) {
    console.log(`[Audio] 🎵 Playing chunk: ${buffer.byteLength} bytes`);
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
    console.log(`[Audio] ✓ Scheduled to play at ${start.toFixed(3)}s`);
}

// --- Message Handling ---
function handleJson(msg) {
    console.log(`[MSG] Received: ${msg.status}`);
    
    if (msg.status === "ai_speaking") {
        console.log("[MSG] 🎙️ AI is speaking");
        updateStatus("ACHARYA IS SPEAKING...");
        document.getElementById('chartContainer').classList.add('speaking-glow');
    } 
    else if (msg.status === "ai_finished_speaking") {
        console.log("[MSG] ✅ AI finished speaking");
        updateStatus("LISTENING...");
        document.getElementById('chartContainer').classList.remove('speaking-glow');
        highlightHouse(null);
    }
    else if (msg.status === "ai_response_text") {
        console.log("[MSG] 💬 AI response:", msg.text.substring(0, 80));
        let text = msg.text;
        let focusMatch = text.match(/\[FOCUS:(.*?)\]/);
        
        if (focusMatch) {
            let focusTarget = focusMatch[1];
            console.log("[MSG] ✨ Focus detected:", focusTarget);
            highlightHouse(focusTarget);
            text = text.replace(/\[FOCUS:.*?\]/, "");
        }
        
        addLog("Acharya", text);
    }
    else if (msg.status === "user_response_text") {
        console.log("[MSG] 🎤 User transcript:", msg.text);
        addLog("You", msg.text);
    }
    else if (msg.status === "ai_thinking") {
        console.log("[MSG] 🧠 AI is thinking...");
        updateStatus("ACHARYA THINKS...");
    }
    else if (msg.status === "chart_data") {
        console.log("[MSG] 📊 Chart data received");
        chartData = msg;  // Store full message for later planet lookup
        populateChartFromPlanetData(msg.chart);  // Use the new function to populate
    }
    else if (msg.status === "chart_focus") {
        console.log(`[MSG] 🌟 Chart focus - Houses: ${msg.houses}, Planets: ${msg.planets}`);
        displayPlanetsInHouses(msg.houses, msg.planets);
    }
    else if (msg.status === "astro_ui_update") {
        console.log(`[MSG] ✨ Astro UI Update received`);
        if (msg.highlights) {
            const houses = msg.highlights.houses || [];
            const planets = msg.highlights.planets || [];
            console.log(`[MSG] 🏠 Highlighting houses: ${houses}, planets: ${planets}`);
            displayPlanetsInHouses(houses, planets);
        }
        if (msg.remedy) {
            console.log(`[MSG] 💊 Suggested remedy: ${msg.remedy}`);
            addLog("Acharya", `💊 Remedy: ${msg.remedy}`);
        }
        if (msg.time_travel) {
            console.log(`[MSG] 🕐 Time travel date: ${msg.time_travel}`);
        }
    }
    else if (msg.status === "error") {
        console.error("[MSG] ⚠️ Error:", msg.message);
        updateStatus("ERROR: " + msg.message);
    }
    else {
        console.log("[MSG] 🔷 Unknown status:", msg.status);
    }
}

function updateStatus(txt) { 
    console.log(`[UI] 📍 Status: ${txt}`);
    document.getElementById('status').innerText = txt; 
}

function addLog(role, text) {
    console.log(`[UI] 💬 ${role}: ${text.substring(0, 60)}`);
    let div = document.createElement('div');
    div.className = `msg ${role.toLowerCase()}`;
    div.innerHTML = `<strong>${role}:</strong> ${text}`;
    document.getElementById('transcript').appendChild(div);
}

// --- Mic ---
function startMic() {
    console.log("[Mic] 🎤 Request to start microphone");
    navigator.mediaDevices.getUserMedia({audio:true}).then(stream => {
        // Try webm first, fall back to default
        let mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            console.log(`[Mic] ⚠️ ${mimeType} not supported, using default`);
            mimeType = 'audio/webm';
        }
        console.log(`[Mic] ✅ Using MIME type: ${mimeType}`);
        
        mediaRecorder = new MediaRecorder(stream, {mimeType: mimeType});
        console.log(`[Mic] ✅ MediaRecorder created`);
        
        mediaRecorder.ondataavailable = e => {
            if (socket && socket.readyState === 1) {
                console.log(`[Mic] 📤 Sending chunk (${e.data.type}): ${e.data.size} bytes`);
                socket.send(e.data);
            } else {
                console.warn(`[Mic] ⚠️ Socket not ready, dropping chunk: ${e.data.size} bytes`);
            }
        };
        mediaRecorder.onerror = (event) => {
            console.error("[Mic] ❌ MediaRecorder error:", event.error);
        };
        mediaRecorder.onstart = () => {
            console.log("[Mic] ▶️ Recording started");
        };
        mediaRecorder.onstop = () => {
            console.log("[Mic] ⏹️ Recording stopped");
        };
        
        mediaRecorder.start(500); // 500ms timeslice
        console.log("[Mic] ✅ Started recording with 500ms timeslice");
        
        socket.send(JSON.stringify({action: 'start_speaking'}));
        console.log("[Mic] 📤 Sent 'start_speaking' signal");
        
        updateStatus("RECORDING...");
    }).catch(err => {
        console.error("[Mic] ❌ Error accessing microphone:", err);
        updateStatus("MIC ERROR");
    });
}

function stopMic() {
    console.log("[Mic] ⏹️ Request to stop microphone");
    if (mediaRecorder) {
        mediaRecorder.stop();
        console.log("[Mic] ✅ MediaRecorder stopped");
        
        socket.send(JSON.stringify({action: 'stop_speaking'}));
        console.log("[Mic] 📤 Sent 'stop_speaking' signal");
        
        updateStatus("TRANSMITTING...");
    } else {
        console.warn("[Mic] ⚠️ No MediaRecorder to stop");
    }
}