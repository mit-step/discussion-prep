import { useEffect, useRef, useState } from "react";

// The Web Speech API has no official TS lib types; `any` casts here are the
// pragmatic choice rather than hand-rolling ambient declarations for it.
/* eslint-disable @typescript-eslint/no-explicit-any */

export function MicButton({
  currentValue,
  onChange,
  disabled,
}: {
  currentValue: string;
  onChange: (value: string) => void;
  disabled: boolean;
}) {
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef<any>(null);
  const baseTextRef = useRef("");
  const finalTranscriptRef = useRef("");
  const currentValueRef = useRef(currentValue);
  currentValueRef.current = currentValue;

  const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

  useEffect(() => {
    if (disabled && isRecording) {
      recognitionRef.current?.stop();
    }
  }, [disabled, isRecording]);

  function start() {
    if (!Ctor || isRecording) return;
    baseTextRef.current = currentValueRef.current.trim() ? `${currentValueRef.current.trim()} ` : "";
    finalTranscriptRef.current = "";

    const recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscriptRef.current += transcript + " ";
        } else {
          interim += transcript;
        }
      }
      onChange(baseTextRef.current + finalTranscriptRef.current + interim);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => setIsRecording(false);

    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
  }

  function stop() {
    recognitionRef.current?.stop();
  }

  if (!Ctor) {
    return (
      <button
        type="button"
        className="mic-btn"
        disabled
        title="Voice input isn't supported in this browser (try Chrome or Edge)"
      >
        🎤
      </button>
    );
  }

  return (
    <button
      type="button"
      className={`mic-btn${isRecording ? " recording" : ""}`}
      disabled={disabled}
      onClick={() => (isRecording ? stop() : start())}
      title={isRecording ? "Stop recording" : "Start voice input"}
    >
      {isRecording ? "⏹" : "🎤"}
    </button>
  );
}
