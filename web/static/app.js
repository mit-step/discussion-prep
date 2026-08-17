const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input-box");
const sendBtn = document.getElementById("send-btn");
const newSessionBtn = document.getElementById("new-session-btn");
const roundBadge = document.getElementById("round-badge");

let sessionId = null;
let phase = "none"; // none | awaiting_argument | in_round | completed

function addBubble(role, text) {
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = text;
  chatEl.appendChild(el);
  chatEl.scrollTop = chatEl.scrollHeight;
  return el;
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
    phase = "awaiting_argument";
    addBubble("system", `New session started. Rounds: ${data.rounds_total}`);
    addBubble("ai", "State your argument.");
    inputEl.placeholder = "State your argument…";
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

  try {
    if (phase === "awaiting_argument") {
      const data = await api(`/api/session/${sessionId}/argument`, {
        body: JSON.stringify({ argument_text: text }),
      });
      phase = "in_round";
      setRoundBadge(`Round ${data.round}/${data.rounds_total}`);
      addBubble("ai", data.question);
    } else if (phase === "in_round") {
      const data = await api(`/api/session/${sessionId}/respond`, {
        body: JSON.stringify({ response_text: text }),
      });
      if (data.completed) {
        phase = "completed";
        setRoundBadge("Evaluation");
        addBubble("system", "Grading complete.");
        renderEvaluation(data.evaluation);
      } else {
        setRoundBadge(`Round ${data.round}/${data.rounds_total}`);
        addBubble("ai", data.question);
      }
    } else {
      addBubble("system", "Session complete — start a new session to practice again.");
    }
  } catch (err) {
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
