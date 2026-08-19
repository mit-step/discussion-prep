const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input-box");
const sendBtn = document.getElementById("send-btn");
const newSessionBtn = document.getElementById("new-session-btn");
const roundBadge = document.getElementById("round-badge");
const micBtn = document.getElementById("mic-btn");
const avatarEl = document.querySelector(".avatar-circle");

let sessionId = null;
let phase = "none"; // none | awaiting_topic | awaiting_argument | in_round | completed
let roundsTotal = null;
let currentRound = 0;

const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
let isRecording = false;
let voiceBaseText = "";
let voiceFinalTranscript = "";

function updateMicButton() {
  micBtn.classList.toggle("recording", isRecording);
  micBtn.textContent = isRecording ? "⏹" : "🎤";
  micBtn.title = isRecording ? "Stop recording" : "Start voice input";
}

function stopRecording() {
  if (recognition) recognition.stop();
}

function startRecording() {
  if (!SpeechRecognitionCtor || isRecording) return;

  voiceBaseText = inputEl.value.trim() ? inputEl.value.trim() + " " : "";
  voiceFinalTranscript = "";

  recognition = new SpeechRecognitionCtor();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = "en-US";

  recognition.onresult = (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        voiceFinalTranscript += transcript + " ";
      } else {
        interim += transcript;
      }
    }
    inputEl.value = voiceBaseText + voiceFinalTranscript + interim;
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
  };

  recognition.onend = () => {
    isRecording = false;
    updateMicButton();
  };

  recognition.start();
  isRecording = true;
  updateMicButton();
}

if (!SpeechRecognitionCtor) {
  micBtn.disabled = true;
  micBtn.title = "Voice input isn't supported in this browser (try Chrome or Edge)";
} else {
  micBtn.addEventListener("click", () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  });
}

function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
  return el;
}

function addLoadingBubble(label) {
  avatarEl.classList.add("thinking");

  const el = document.createElement("div");
  el.className = "bubble ai loading";
  el.textContent = label;
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;

  let dots = 0;
  const timer = setInterval(() => {
    dots = (dots + 1) % 4;
    el.textContent = label + ".".repeat(dots);
  }, 450);

  return {
    stop() {
      clearInterval(timer);
      el.remove();
      avatarEl.classList.remove("thinking");
    },
  };
}

function addTranscriptLink(id) {
  const el = document.createElement("a");
  el.href = `/transcript/${id}`;
  el.target = "_blank";
  el.className = "bubble system transcript-link";
  el.textContent = "View full transcript →";
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setRoundBadge(text) {
  if (!text) {
    roundBadge.classList.add("hidden");
    return;
  }
  roundBadge.textContent = text;
  roundBadge.classList.remove("hidden");
}

function setBusy(busy) {
  sendBtn.disabled = busy;
  inputEl.disabled = busy;
  if (SpeechRecognitionCtor) {
    if (busy && isRecording) stopRecording();
    micBtn.disabled = busy;
  }
}

async function api(path, options) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

async function startNewSession() {
  chatEl.innerHTML = "";
  setRoundBadge(null);
  inputEl.value = "";
  setBusy(true);
  try {
    const data = await api("/api/session");
    sessionId = data.session_id;
    phase = "awaiting_topic";
    roundsTotal = data.rounds_total;
    currentRound = 0;
    addBubble("ai", "Welcome! I'm here to help you prepare your legal argument before class. We'll work through it together — I'll ask a few questions to help you develop your thinking, and at the end I'll suggest a score to give you a sense of where you stand. What case or reading will your argument be based on?");
    inputEl.placeholder = "Name the case or reading…";
  } catch (err) {
    addBubble("system", `Error: ${err.message}`);
  } finally {
    setBusy(false);
    inputEl.focus();
  }
}

function renderEvaluation(evaluation) {
  const card = document.createElement("div");
  card.className = "report-card";

  const pillarsHeading = document.createElement("h2");
  pillarsHeading.textContent = "Overall Reasoning";
  card.appendChild(pillarsHeading);

  const pillarLabels = {
    logical_reasoning: "Logical Reasoning",
    organization: "Organization",
    persuasiveness: "Persuasiveness",
    clarity: "Clarity",
  };

  for (const [key, label] of Object.entries(pillarLabels)) {
    const pillar = evaluation.overall_reasoning[key];
    const row = document.createElement("div");
    row.className = "pillar-row";

    const name = document.createElement("div");
    name.className = "pillar-name";
    name.textContent = label;

    const meter = document.createElement("div");
    meter.className = "meter";
    const fill = document.createElement("div");
    fill.className = "meter-fill";
    fill.style.width = `${(pillar.score / 5) * 100}%`;
    meter.appendChild(fill);

    const score = document.createElement("div");
    score.textContent = `${pillar.score}/5`;

    row.appendChild(name);
    row.appendChild(meter);
    row.appendChild(score);
    card.appendChild(row);

    if (pillar.feedback) {
      const fb = document.createElement("div");
      fb.className = "pillar-feedback";
      fb.textContent = pillar.feedback;
      card.appendChild(fb);
    }
  }

  if (evaluation.rubric_alignment && evaluation.rubric_alignment.length > 0) {
    const rubricHeading = document.createElement("h2");
    rubricHeading.textContent = "Rubric Alignment";
    card.appendChild(rubricHeading);

    for (const item of evaluation.rubric_alignment) {
      const row = document.createElement("div");
      row.className = "rubric-item";

      const head = document.createElement("div");
      head.className = "rubric-item-head";
      head.innerHTML = `<span>${item.criterion}</span><span>${item.points_awarded}/${item.max_points}</span>`;
      row.appendChild(head);

      const meter = document.createElement("div");
      meter.className = "meter";
      meter.style.marginTop = "0.35rem";
      const fill = document.createElement("div");
      fill.className = "meter-fill";
      fill.style.width = `${(item.points_awarded / item.max_points) * 100}%`;
      meter.appendChild(fill);
      row.appendChild(meter);

      if (item.feedback) {
        const fb = document.createElement("div");
        fb.className = "rubric-item-feedback";
        fb.textContent = item.feedback;
        row.appendChild(fb);
      }
      card.appendChild(row);
    }
  }

  if (evaluation.groundedness_notes) {
    const notes = document.createElement("div");
    notes.className = "groundedness";
    notes.textContent = `Groundedness: ${evaluation.groundedness_notes}`;
    card.appendChild(notes);
  }

  chatEl.appendChild(card);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function send() {
  const text = inputEl.value.trim();
  if (!text || !sessionId) return;

  addBubble("student", text);
  inputEl.value = "";
  setBusy(true);

  const isFinalRound = phase === "in_round" && currentRound === roundsTotal;
  const loading = phase !== "completed" ? addLoadingBubble(isFinalRound ? "Evaluating" : "Thinking") : null;

  try {
    if (phase === "awaiting_topic") {
      const data = await api(`/api/session/${sessionId}/topic`, {
        body: JSON.stringify({ topic_text: text }),
      });
      loading.stop();
      phase = "awaiting_argument";
      const docLabel = data.source_docs.length > 0
        ? data.source_docs.join(", ")
        : "the available course materials";
      addBubble("ai", `Got it — I'll ground our discussion in ${docLabel}. Now go ahead and state your argument.`);
      inputEl.placeholder = "State your argument…";
    } else if (phase === "awaiting_argument") {
      const data = await api(`/api/session/${sessionId}/argument`, {
        body: JSON.stringify({ argument_text: text }),
      });
      loading.stop();
      phase = "in_round";
      currentRound = data.round;
      roundsTotal = data.rounds_total;
      setRoundBadge(`Round ${data.round}/${data.rounds_total}`);
      addBubble("ai", data.question);
    } else if (phase === "in_round") {
      const data = await api(`/api/session/${sessionId}/respond`, {
        body: JSON.stringify({ response_text: text }),
      });
      loading.stop();
      if (data.completed) {
        phase = "completed";
        setRoundBadge("Evaluation");
        addBubble("system", "Here's your suggested score.");
        renderEvaluation(data.evaluation);
        addTranscriptLink(sessionId);
      } else {
        currentRound = data.round;
        setRoundBadge(`Round ${data.round}/${data.rounds_total}`);
        addBubble("ai", data.question);
      }
    } else {
      addBubble("system", "Session complete — start a new session to practice again.");
    }
  } catch (err) {
    if (loading) loading.stop();
    addBubble("system", `Error: ${err.message}`);
  } finally {
    setBusy(phase === "completed");
    inputEl.focus();
  }
}

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});
newSessionBtn.addEventListener("click", startNewSession);

startNewSession();
