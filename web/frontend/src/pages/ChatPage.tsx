import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ChatBubble, type BubbleRole } from "../components/ChatBubble";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { HistoryPanel } from "../components/HistoryPanel";
import { LoadingBubble } from "../components/LoadingBubble";
import { MicButton } from "../components/MicButton";
import { ReportCard } from "../components/ReportCard";
import type { Evaluation } from "../types";

type Phase = "starting" | "awaiting_argument" | "in_round" | "completed";

type ChatMessage =
  | { kind: "bubble"; role: BubbleRole; text: string }
  | { kind: "evaluation"; evaluation: Evaluation }
  | { kind: "transcript-link"; sessionId: string };

export function ChatPage() {
  const { docUuid } = useParams<{ docUuid: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const initialTitle = (location.state as { title?: string } | null)?.title;

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("starting");
  const [round, setRound] = useState(0);
  const [roundsTotal, setRoundsTotal] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(true);
  const [loadingLabel, setLoadingLabel] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  const isUnfinished = phase === "awaiting_argument" || phase === "in_round";

  function goToLibrary() {
    if (isUnfinished) {
      setShowLeaveConfirm(true);
    } else {
      navigate("/library");
    }
  }

  useEffect(() => {
    if (!docUuid) return;
    let cancelled = false;
    api
      .createSession(docUuid)
      .then((data) => {
        if (cancelled) return;
        setSessionId(data.session_id);
        setRoundsTotal(data.rounds_total);
        setPhase("awaiting_argument");
        setBusy(false);
        setMessages([
          {
            kind: "bubble",
            role: "ai",
            text: `Welcome! We'll discuss **${data.reading_title}**. State your argument to begin — I'll ask a few probing questions, then suggest a score.`,
          },
        ]);
      })
      .catch((err) => {
        if (cancelled) return;
        setMessages([
          { kind: "bubble", role: "system", text: `Error: ${err instanceof Error ? err.message : "Failed to start session"}` },
        ]);
      });
    return () => {
      cancelled = true;
    };
  }, [docUuid]);

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight });
  }, [messages, loadingLabel]);

  async function send() {
    const text = input.trim();
    if (!text || !sessionId || busy) return;

    setMessages((prev) => [...prev, { kind: "bubble", role: "student", text }]);
    setInput("");
    setBusy(true);

    const isFinalRound = phase === "in_round" && round === roundsTotal;
    setLoadingLabel(isFinalRound ? "Evaluating" : "Thinking");

    // React state updates are deferred, so `phase` itself can't be trusted
    // by the time `finally` runs below — track the outcome locally instead.
    let nextPhase: Phase = phase;

    try {
      if (phase === "awaiting_argument") {
        const data = await api.submitArgument(sessionId, text);
        nextPhase = "in_round";
        setPhase(nextPhase);
        setRound(data.round ?? 1);
        setRoundsTotal(data.rounds_total ?? roundsTotal);
        setMessages((prev) => [...prev, { kind: "bubble", role: "ai", text: data.question ?? "" }]);
      } else if (phase === "in_round") {
        const data = await api.submitResponse(sessionId, text);
        if (data.completed && data.evaluation) {
          nextPhase = "completed";
          setPhase(nextPhase);
          setMessages((prev) => [
            ...prev,
            { kind: "bubble", role: "system", text: "Here's your suggested score." },
            { kind: "evaluation", evaluation: data.evaluation as Evaluation },
            { kind: "transcript-link", sessionId },
          ]);
        } else {
          setRound(data.round ?? round + 1);
          setMessages((prev) => [...prev, { kind: "bubble", role: "ai", text: data.question ?? "" }]);
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { kind: "bubble", role: "system", text: `Error: ${err instanceof Error ? err.message : "Something went wrong"}` },
      ]);
    } finally {
      setLoadingLabel(null);
      setBusy(nextPhase === "completed");
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <header className="app-header">
        <button type="button" className="secondary" onClick={goToLibrary}>
          ← Library
        </button>
        <h1>{initialTitle ?? "Discussion Prep"}</h1>
        <div className="app-header-actions">
          <Link to="/about" className="knowledge-graph-link">
            About
          </Link>
          {roundsTotal !== null && phase !== "starting" && (
            <span className="round-badge">
              {phase === "completed" ? "Evaluation" : `Round ${round}/${roundsTotal}`}
            </span>
          )}
          {docUuid && (
            <button
              type="button"
              className="history-btn"
              title="View past sessions"
              onClick={() => setShowHistory(true)}
            >
              🕐
            </button>
          )}
        </div>
      </header>

      <main className="chat" ref={chatRef}>
        {messages.map((msg, i) => {
          if (msg.kind === "bubble") return <ChatBubble key={i} role={msg.role} text={msg.text} />;
          if (msg.kind === "evaluation") return <ReportCard key={i} evaluation={msg.evaluation} />;
          return (
            <a
              key={i}
              className="bubble system transcript-link"
              href={`/discussion-prep/transcript/${msg.sessionId}`}
              target="_blank"
              rel="noreferrer"
            >
              View full transcript →
            </a>
          );
        })}
        {loadingLabel && <LoadingBubble label={loadingLabel} />}
      </main>

      <footer className="composer">
        <textarea
          id="input-box"
          rows={3}
          placeholder={phase === "awaiting_argument" ? "State your argument…" : "Your response…"}
          value={input}
          disabled={busy || phase === "starting" || phase === "completed"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <div className="composer-actions">
          <div className="composer-actions-right">
            <MicButton currentValue={input} onChange={setInput} disabled={busy || phase === "completed"} />
            <button type="button" onClick={send} disabled={busy || phase === "completed" || !input.trim()}>
              Send
            </button>
          </div>
        </div>
      </footer>

      {showHistory && docUuid && <HistoryPanel docUuid={docUuid} onClose={() => setShowHistory(false)} />}

      {showLeaveConfirm && (
        <ConfirmDialog
          title="Leave this discussion?"
          message="You haven't finished this session yet — going back to the library now will abandon this conversation and it won't be saved."
          confirmLabel="Abandon & leave"
          onCancel={() => setShowLeaveConfirm(false)}
          onConfirm={() => {
            setShowLeaveConfirm(false);
            navigate("/library");
          }}
        />
      )}
    </div>
  );
}
