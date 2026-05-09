document.addEventListener("DOMContentLoaded", () => {
    if (window.lucide) {
        window.lucide.createIcons();
    }

    initTheme();
    initChat();
    initMoodTracker();
    initMeditationTimer();
});

function initTheme() {
    const toggle = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("manasvi-theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
    }

    if (!toggle) return;
    toggle.addEventListener("click", () => {
        document.body.classList.toggle("dark");
        localStorage.setItem("manasvi-theme", document.body.classList.contains("dark") ? "dark" : "light");
    });
}

function initChat() {
    const chatWindow = document.getElementById("chatWindow");
    if (chatWindow) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    const voiceButton = document.getElementById("voiceButton");
    const textarea = document.querySelector(".composer textarea");
    const voiceStatus = document.getElementById("voiceStatus");
    if (!voiceButton || !textarea) return;

    voiceButton.addEventListener("click", () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            voiceStatus.textContent = "Speech recognition is not available in this browser.";
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "en-IN";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        voiceStatus.textContent = "Listening...";
        recognition.start();

        recognition.onresult = (event) => {
            textarea.value = event.results[0][0].transcript;
            voiceStatus.textContent = "Transcript added. Review it, then send.";
            textarea.focus();
        };

        recognition.onerror = () => {
            voiceStatus.textContent = "Could not capture speech. Please try again or type your message.";
        };
    });
}

function initMoodTracker() {
    const form = document.getElementById("moodForm");
    const chartCanvas = document.getElementById("moodChart");
    if (!form || !chartCanvas || !window.Chart) return;

    let selectedMood = "";
    const status = document.getElementById("moodSaveStatus");
    const moodButtons = Array.from(form.querySelectorAll("[data-mood]"));
    moodButtons.forEach((button) => {
        button.addEventListener("click", () => {
            selectedMood = button.dataset.mood;
            moodButtons.forEach((item) => item.classList.toggle("active", item === button));
        });
    });

    let chart;
    const moodScale = {
        Sad: 1,
        Anxious: 2,
        Okay: 3,
        Good: 4,
        Happy: 5,
    };

    async function loadMoods() {
        const response = await fetch("/api/moods");
        const moods = await response.json();
        const labels = moods.map((entry) => entry.date);
        const values = moods.map((entry) => moodScale[entry.mood] || null);

        if (chart) chart.destroy();
        chart = new Chart(chartCanvas, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Mood",
                    data: values,
                    borderColor: "#f57c2c",
                    backgroundColor: "rgba(245, 124, 44, 0.14)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 5,
                }],
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    y: {
                        min: 1,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            callback: (value) => Object.keys(moodScale).find((mood) => moodScale[mood] === value) || "",
                        },
                    },
                },
                plugins: {
                    legend: { display: false },
                },
            },
        });
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!selectedMood) {
            status.textContent = "Choose a mood before saving.";
            return;
        }

        const note = form.querySelector("[name='note']").value;
        const response = await fetch("/api/moods", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mood: selectedMood, note }),
        });

        if (!response.ok) {
            status.textContent = "Mood could not be saved.";
            return;
        }

        status.textContent = "Mood saved.";
        form.reset();
        selectedMood = "";
        moodButtons.forEach((button) => button.classList.remove("active"));
        await loadMoods();
    });

    loadMoods();
}

function initMeditationTimer() {
    const display = document.getElementById("countdownDisplay");
    const input = document.getElementById("timeInput");
    const startButton = document.getElementById("startTimer");
    const pauseButton = document.getElementById("pauseTimer");
    const resetButton = document.getElementById("resetTimer");
    const audioSelect = document.getElementById("audioSelect");
    if (!display || !input || !startButton || !pauseButton || !resetButton || !audioSelect) return;

    const audio = {
        flute: document.getElementById("fluteAudio"),
        sitar: document.getElementById("sitarAudio"),
        violin: document.getElementById("violinAudio"),
    };
    let intervalId = null;
    let remainingSeconds = Number(input.value) * 60;
    let isPaused = false;
    let currentAudio = null;

    function updateDisplay() {
        const minutes = Math.floor(remainingSeconds / 60).toString().padStart(2, "0");
        const seconds = (remainingSeconds % 60).toString().padStart(2, "0");
        display.textContent = `${minutes}:${seconds}`;
    }

    function stopAudio(reset = false) {
        if (!currentAudio) return;
        currentAudio.pause();
        if (reset) currentAudio.currentTime = 0;
    }

    function playSelectedAudio() {
        stopAudio(true);
        currentAudio = audio[audioSelect.value];
        if (currentAudio) {
            currentAudio.play().catch(() => {});
        }
    }

    function resetTimer() {
        clearInterval(intervalId);
        intervalId = null;
        isPaused = false;
        remainingSeconds = Math.max(1, Number(input.value) || 5) * 60;
        pauseButton.disabled = true;
        pauseButton.innerHTML = '<i data-lucide="pause"></i> Pause';
        stopAudio(true);
        updateDisplay();
        if (window.lucide) window.lucide.createIcons();
    }

    input.addEventListener("input", resetTimer);

    startButton.addEventListener("click", () => {
        resetTimer();
        pauseButton.disabled = false;
        playSelectedAudio();
        intervalId = setInterval(() => {
            if (isPaused) return;
            remainingSeconds -= 1;
            updateDisplay();
            if (remainingSeconds <= 0) {
                resetTimer();
            }
        }, 1000);
    });

    pauseButton.addEventListener("click", () => {
        isPaused = !isPaused;
        pauseButton.innerHTML = isPaused ? '<i data-lucide="play"></i> Resume' : '<i data-lucide="pause"></i> Pause';
        if (isPaused) {
            stopAudio(false);
        } else if (currentAudio) {
            currentAudio.play().catch(() => {});
        }
        if (window.lucide) window.lucide.createIcons();
    });

    resetButton.addEventListener("click", resetTimer);
    updateDisplay();
}
