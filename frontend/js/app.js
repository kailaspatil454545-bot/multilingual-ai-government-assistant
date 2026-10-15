const API_URL = (window.location.protocol === "http:" || window.location.protocol === "https:") && (window.location.port === "8000" || window.location.port === "")
    ? ""
    : "http://127.0.0.1:8000";

let messageCounter = 0;
let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;
let isRecording = false;
let recordingTimerInterval = null;
let recordingSeconds = 0;
let currentAudio = null; // currently playing HTML5 Audio element

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("question");
    if (input) {
        input.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendQuestion();
            }
        });
    }

    // Check microphone support on startup
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn("Microphone access API (getUserMedia) not supported in this browser environment.");
    }
});

/**
 * Update system status bar
 * Statuses: 'ready', 'listening', 'processing', 'response'
 */
function setStatus(statusType, message) {
    const statusBar = document.getElementById("status-bar");
    const statusText = document.getElementById("status-text");
    const statusIcon = document.getElementById("status-icon");
    const timerEl = document.getElementById("recording-timer");

    if (!statusBar || !statusText) return;

    // Reset classes
    statusBar.className = "status-bar";

    switch (statusType) {
        case "listening":
            statusBar.classList.add("status-listening");
            statusIcon.innerText = "🔴";
            statusText.innerText = message || "Listening... (Click ⏹️ to finish speaking)";
            if (timerEl) timerEl.style.display = "inline-block";
            break;

        case "processing":
            statusBar.classList.add("status-processing");
            statusIcon.innerText = "⏳";
            statusText.innerText = message || "Processing speech with Faster-Whisper AI...";
            if (timerEl) timerEl.style.display = "none";
            break;

        case "response":
            statusBar.classList.add("status-ready");
            statusIcon.innerText = "🔊";
            statusText.innerText = message || "Response ready";
            if (timerEl) timerEl.style.display = "none";
            break;

        case "error":
            statusBar.classList.add("status-error");
            statusIcon.innerText = "⚠️";
            statusText.innerText = message || "An error occurred";
            if (timerEl) timerEl.style.display = "none";
            break;

        case "ready":
        default:
            statusBar.classList.add("status-ready");
            statusIcon.innerText = "🎙️";
            statusText.innerText = message || "Ready • Click 🎤 to speak or type your question";
            if (timerEl) timerEl.style.display = "none";
            break;
    }
}

/**
 * Show / Close Error Banner
 */
function showErrorBanner(message) {
    const banner = document.getElementById("error-banner");
    const msgEl = document.getElementById("error-message");
    if (banner && msgEl) {
        msgEl.innerText = message;
        banner.style.display = "flex";
    }
}

function closeErrorBanner() {
    const banner = document.getElementById("error-banner");
    if (banner) {
        banner.style.display = "none";
    }
}

/**
 * Handle Language change
 */
function onLanguageChange() {
    const lang = document.getElementById("language").value;
    const input = document.getElementById("question");
    if (input) {
        if (lang === "mr") {
            input.placeholder = "तुमचा प्रश्न विचारा किंवा 🎤 वर क्लिक करा...";
        } else if (lang === "hi") {
            input.placeholder = "अपना प्रश्न पूछें या 🎤 पर क्लिक करें...";
        } else {
            input.placeholder = "Ask your question or click 🎤 to speak...";
        }
    }
}

/**
 * Toggle voice recording (Start / Stop)
 */
async function toggleVoiceRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

// Backwards compatibility alias for startVoice
function startVoice() {
    toggleVoiceRecording();
}

/**
 * Request microphone permission and start recording
 */
async function startRecording() {
    closeErrorBanner();

    // Check browser compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showErrorBanner("Microphone recording is not supported in this browser. Please use Chrome, Edge, or Firefox.");
        setStatus("error", "Microphone not supported");
        return;
    }

    try {
        // Request microphone permission
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            }
        });

        // Determine supported audio mime type
        let mimeType = "audio/webm;codecs=opus";
        if (typeof MediaRecorder.isTypeSupported === "function") {
            if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
                mimeType = "audio/webm;codecs=opus";
            } else if (MediaRecorder.isTypeSupported("audio/webm")) {
                mimeType = "audio/webm";
            } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
                mimeType = "audio/ogg";
            } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
                mimeType = "audio/mp4";
            } else {
                mimeType = "";
            }
        }

        const options = mimeType ? { mimeType: mimeType } : {};
        mediaRecorder = new MediaRecorder(audioStream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstart = () => {
            isRecording = true;
            updateMicButtonUI(true);
            recordingSeconds = 0;
            updateTimerDisplay();
            recordingTimerInterval = setInterval(() => {
                recordingSeconds++;
                updateTimerDisplay();
            }, 1000);

            setStatus("listening", "Listening... (Click ⏹️ to finish speaking)");
        };

        mediaRecorder.onstop = async () => {
            isRecording = false;
            clearInterval(recordingTimerInterval);
            updateMicButtonUI(false);

            // Release microphone tracks
            if (audioStream) {
                audioStream.getTracks().forEach((track) => track.stop());
                audioStream = null;
            }

            const recordedBlob = new Blob(audioChunks, {
                type: mimeType || "audio/webm"
            });

            if (recordedBlob.size < 1000) {
                setStatus("ready", "Recording was too short. Tap 🎤 to try again.");
                return;
            }

            // Upload and transcribe
            await handleRecordedAudio(recordedBlob);
        };

        mediaRecorder.start(250); // Collect data chunks every 250ms

    } catch (error) {
        console.error("Microphone access error:", error);
        handleMicrophoneError(error);
    }
}

/**
 * Stop active audio recording
 */
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        setStatus("processing", "Processing recorded voice...");
        mediaRecorder.stop();
    }
}

/**
 * Handle microphone errors gracefully
 */
function handleMicrophoneError(error) {
    let msg = "Could not access microphone.";
    if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
        msg = "Microphone access was denied. Please allow microphone permission in your browser URL bar or settings.";
    } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
        msg = "No microphone hardware found. Please connect a microphone or use the text input.";
    } else if (error.name === "NotReadableError") {
        msg = "Microphone is already in use by another application.";
    } else {
        msg = `Microphone error: ${error.message || error.name}`;
    }

    showErrorBanner(msg);
    setStatus("error", msg);
    updateMicButtonUI(false);
}

/**
 * Update Mic button appearance
 */
function updateMicButtonUI(recording) {
    const micBtn = document.getElementById("mic-btn");
    if (!micBtn) return;

    if (recording) {
        micBtn.classList.add("recording");
        micBtn.innerHTML = '<span class="mic-icon">⏹️</span><span class="mic-text">Stop</span>';
        micBtn.title = "Click to stop recording";
    } else {
        micBtn.classList.remove("recording");
        micBtn.innerHTML = '<span class="mic-icon">🎤</span><span class="mic-text">Speak</span>';
        micBtn.title = "Click to record voice with microphone";
    }
}

function updateTimerDisplay() {
    const timerEl = document.getElementById("recording-timer");
    if (!timerEl) return;
    const mins = String(Math.floor(recordingSeconds / 60)).padStart(2, "0");
    const secs = String(recordingSeconds % 60).padStart(2, "0");
    timerEl.innerText = `${mins}:${secs}`;
}

/**
 * Send recorded audio to backend /transcribe endpoint
 */
async function handleRecordedAudio(audioBlob) {
    setStatus("processing", "Processing speech with Faster-Whisper AI...");

    const languageSelect = document.getElementById("language");
    const selectedLanguage = languageSelect ? languageSelect.value : "en";

    const formData = new FormData();
    const ext = audioBlob.type.includes("webm") ? "webm" : (audioBlob.type.includes("ogg") ? "ogg" : "wav");
    formData.append("audio", audioBlob, `voice_query.${ext}`);
    formData.append("language", selectedLanguage);

    try {
        const response = await fetch(`${API_URL}/transcribe`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        const transcribedText = (data.text || "").trim();

        if (!transcribedText) {
            setStatus("ready", "No clear speech detected. Please speak closer to the microphone.");
            showErrorBanner("Could not transcribe any clear words. Please try again.");
            return;
        }

        // Display transcribed text in input field and screen
        const input = document.getElementById("question");
        if (input) {
            input.value = transcribedText;
        }

        // Send to query API
        await executeQuery(transcribedText, selectedLanguage);

    } catch (error) {
        console.error("Transcription error:", error);
        setStatus("error", "Transcription failed. You can also type your question.");
        showErrorBanner(`Transcription error: ${error.message}`);
    }
}

/**
 * Send written question from text input
 */
async function sendQuestion() {
    const input = document.getElementById("question");
    const question = input.value.trim();
    const language = document.getElementById("language").value;

    if (question === "") {
        showErrorBanner("Please enter a question or click the microphone to speak.");
        return;
    }

    closeErrorBanner();
    input.value = "";
    await executeQuery(question, language);
}

/**
 * Execute query to backend /query API, display answer, and trigger TTS
 */
async function executeQuery(question, language) {
    // Stop any ongoing TTS audio
    stopAudio();

    // Display user question in chat
    addMessage(question, "user");

    // Show temporary thinking state
    const thinkingId = addMessage("Thinking...", "bot typing");
    setStatus("processing", "Finding government service information...");

    try {
        const response = await fetch(`${API_URL}/query`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: question,
                language: language
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        removeMessage(thinkingId);

        const answerText = data.answer || "No response received.";
        const msgId = addMessage(answerText, "bot", {
            allowSpeak: true,
            text: answerText,
            language: language
        });

        setStatus("response", "Response ready");

        // Speak the answer aloud automatically
        speakText(answerText, language, msgId);

    } catch (error) {
        console.error("Query API error:", error);
        removeMessage(thinkingId);
        addMessage(
            "Sorry, I could not connect to the AI assistant. Please ensure the backend server is running on http://127.0.0.1:8000.",
            "bot"
        );
        setStatus("error", "Connection error");
    }
}

/**
 * Add a message bubble to the chat box
 */
function addMessage(message, type, options = {}) {
    const messages = document.getElementById("messages");
    if (!messages) return null;

    messageCounter++;
    const id = `msg-${messageCounter}`;

    const div = document.createElement("div");
    div.id = id;
    div.className = type.includes("user") ? "user-message" : "bot-message";

    if (type.includes("typing")) {
        div.style.fontStyle = "italic";
        div.style.opacity = "0.7";
        div.innerText = message;
    } else {
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        contentDiv.innerText = message;
        div.appendChild(contentDiv);

        // Add speaker replay button for bot messages
        if (options.allowSpeak) {
            const actionsDiv = document.createElement("div");
            actionsDiv.className = "message-actions";

            const speakerBtn = document.createElement("button");
            speakerBtn.className = "speaker-btn";
            speakerBtn.id = `speaker-${id}`;
            speakerBtn.title = "Replay answer aloud (TTS)";
            speakerBtn.innerHTML = "🔊";
            speakerBtn.onclick = () => {
                replayAnswer(options.text, options.language, id);
            };

            actionsDiv.appendChild(speakerBtn);
            div.appendChild(actionsDiv);
        }
    }

    messages.appendChild(div);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) {
        el.remove();
    }
}

function scrollToBottom() {
    const chatBox = document.getElementById("chat-box") || document.getElementById("messages");
    if (chatBox) {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

/**
 * Stop any ongoing TTS audio or speech synthesis
 */
function stopAudio() {
    if (currentAudio) {
        try {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        } catch (e) {
            // ignore
        }
        currentAudio = null;
    }

    if (window.speechSynthesis && window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
    }

    // Reset all speaker button animations
    document.querySelectorAll(".speaker-btn").forEach((btn) => {
        btn.classList.remove("playing");
        btn.innerHTML = "🔊";
    });
}

/**
 * Speak text aloud using backend /tts with browser Web Speech API fallback
 */
async function speakText(text, language, messageId) {
    stopAudio();

    const speakerBtn = messageId ? document.getElementById(`speaker-${messageId}`) : null;
    if (speakerBtn) {
        speakerBtn.classList.add("playing");
        speakerBtn.innerHTML = "🔊";
    }

    try {
        // First try the backend neural TTS endpoint
        const ttsUrl = `${API_URL}/tts?text=${encodeURIComponent(text)}&language=${encodeURIComponent(language)}`;
        const audio = new Audio(ttsUrl);
        currentAudio = audio;

        audio.onended = () => {
            if (speakerBtn) {
                speakerBtn.classList.remove("playing");
                speakerBtn.innerHTML = "🔊";
            }
            currentAudio = null;
        };

        audio.onerror = () => {
            console.warn("Backend TTS playback failed, falling back to Web Speech Synthesis API.");
            fallbackSpeechSynthesis(text, language, speakerBtn);
        };

        await audio.play();

    } catch (err) {
        console.warn("Audio play rejected or failed, falling back to Web Speech Synthesis API:", err);
        fallbackSpeechSynthesis(text, language, speakerBtn);
    }
}

/**
 * Fallback to browser's native Web Speech Synthesis API
 */
function fallbackSpeechSynthesis(text, language, speakerBtn) {
    if (!window.speechSynthesis) {
        if (speakerBtn) {
            speakerBtn.classList.remove("playing");
            speakerBtn.innerHTML = "🔊";
        }
        return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    if (language === "mr") {
        utterance.lang = "mr-IN";
    } else if (language === "hi") {
        utterance.lang = "hi-IN";
    } else {
        utterance.lang = "en-IN";
    }

    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => {
        if (speakerBtn) {
            speakerBtn.classList.remove("playing");
            speakerBtn.innerHTML = "🔊";
        }
    };

    utterance.onerror = () => {
        if (speakerBtn) {
            speakerBtn.classList.remove("playing");
            speakerBtn.innerHTML = "🔊";
        }
    };

    window.speechSynthesis.speak(utterance);
}

/**
 * Replay specific answer when 🔊 is clicked
 */
function replayAnswer(text, language, messageId) {
    const speakerBtn = document.getElementById(`speaker-${messageId}`);
    if (speakerBtn && speakerBtn.classList.contains("playing")) {
        // Toggle stop
        stopAudio();
    } else {
        speakText(text, language, messageId);
    }
}

/**
 * Replay initial welcome message
 */
function replayWelcome() {
    const lang = document.getElementById("language").value;
    const welcomeText = "Welcome to the Multilingual AI Government Assistant. Ask me about Aadhaar, PAN card, Ration card, Income certificate, Driving licence, and Government schemes.";
    speakText(welcomeText, lang, "welcome-msg");
}

/**
 * Ask from quick topic chip
 */
function askQuickTopic(topic) {
    const input = document.getElementById("question");
    if (input) {
        input.value = topic;
    }
    sendQuestion();
}