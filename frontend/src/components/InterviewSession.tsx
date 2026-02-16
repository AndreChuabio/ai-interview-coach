"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  Square,
  Loader2,
  Video,
  VideoOff,
  MessageSquare,
  Activity,
  Gauge,
  RefreshCw,
} from "lucide-react";
import { AudioRecorder, playAudioUrl } from "@/lib/audio";
import FaceTracker from "@/components/FaceTracker";
import {
  getOpeningAudio,
  sendResponse,
  submitFaceData,
  type InterviewSession as SessionType,
  type RespondResponse,
  type ToneSnapshot,
  type FaceSnapshot,
} from "@/lib/api";
import type { FaceFrame } from "@/lib/mediapipe";

interface Props {
  session: SessionType;
  onComplete: (sessionId: string) => void;
}

type Phase = "loading" | "ai_speaking" | "listening" | "processing" | "done" | "error";

interface Turn {
  role: "interviewer" | "candidate";
  text: string;
  tone?: ToneSnapshot;
}

/* ------------------------------------------------------------------ */
/*  Progress Path (Duolingo-style connected dots)                       */
/* ------------------------------------------------------------------ */
function ProgressPath({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  return (
    <div className="flex items-center gap-0 w-full">
      {Array.from({ length: total }, (_, i) => {
        const idx = i + 1;
        const done = idx < current;
        const active = idx === current;
        return (
          <div key={i} className="flex items-center flex-1">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold transition-all duration-500 ${
                active ? "dot-pulse" : ""
              }`}
              style={{
                background: done
                  ? "var(--duo-green)"
                  : active
                    ? "var(--duo-blue)"
                    : "var(--duo-polar)",
                color: done || active ? "white" : "var(--duo-hare)",
                boxShadow: active ? "0 0 0 4px var(--duo-blue-light)" : "none",
              }}
            >
              {done ? (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : (
                idx
              )}
            </div>
            {i < total - 1 && (
              <div
                className="h-1 flex-1 rounded-full transition-all duration-500"
                style={{
                  background: done ? "var(--duo-green)" : "var(--duo-polar)",
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Audio Level Bars (green, Duolingo-style)                            */
/* ------------------------------------------------------------------ */
function AudioLevelBars() {
  return (
    <div className="flex items-end gap-1 h-6">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-1.5 rounded-full"
          style={{
            background: "var(--duo-green)",
            animation: `audioBar 0.8s ease-in-out ${i * 0.1}s infinite alternate`,
          }}
        />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Phase Indicator (colored badges)                                    */
/* ------------------------------------------------------------------ */
function PhaseIndicator({ phase }: { phase: Phase }) {
  const config: Record<Phase, { bg: string; color: string; label: string }> = {
    loading: { bg: "var(--duo-polar)", color: "var(--duo-wolf)", label: "Loading..." },
    ai_speaking: { bg: "var(--duo-orange-light)", color: "var(--duo-orange-push)", label: "AI speaking" },
    listening: { bg: "var(--duo-green-light)", color: "var(--duo-green-push)", label: "Your turn" },
    processing: { bg: "var(--duo-blue-light)", color: "var(--duo-blue-push)", label: "Processing..." },
    done: { bg: "var(--duo-green-light)", color: "var(--duo-green-push)", label: "Complete" },
    error: { bg: "var(--duo-red-light)", color: "var(--duo-red-push)", label: "Error" },
  };

  const c = config[phase];

  return (
    <span
      className="px-3 py-1 rounded-full text-xs font-bold"
      style={{ background: c.bg, color: c.color }}
    >
      {c.label}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Component                                                      */
/* ------------------------------------------------------------------ */
export default function InterviewSession({ session, onComplete }: Props) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [transcript, setTranscript] = useState<Turn[]>([]);
  const [questionNum, setQuestionNum] = useState(0);
  const [faceTrackingOn, setFaceTrackingOn] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [latestTone, setLatestTone] = useState<ToneSnapshot | null>(null);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const faceSnapshotsRef = useRef<FaceSnapshot[]>([]);
  const lastAudioBlobRef = useRef<Blob | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      const recorder = new AudioRecorder();
      await recorder.initialize();
      recorderRef.current = recorder;

      const opening = await getOpeningAudio(session.session_id);
      if (cancelled) return;

      setTranscript([{ role: "interviewer", text: opening.text }]);
      setQuestionNum(1);
      setPhase("ai_speaking");

      try {
        await playAudioUrl(opening.audio);
      } catch {
        // Audio playback may fail without user interaction
      }
      if (!cancelled) setPhase("listening");
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [session.session_id]);

  const handleFaceFrameBatch = useCallback((frames: FaceFrame[]) => {
    const snapshots: FaceSnapshot[] = frames.map((f) => ({
      timestamp: f.timestamp,
      dominant_emotion: f.dominant_emotion,
      emotion_scores: f.emotion_scores,
      eye_contact: f.eye_contact,
      head_pitch: f.head_pitch,
      head_yaw: f.head_yaw,
    }));
    faceSnapshotsRef.current.push(...snapshots);
  }, []);

  const startRecording = useCallback(() => {
    if (recorderRef.current && !recorderRef.current.isRecording) {
      recorderRef.current.start();
      setIsRecording(true);
      setRecordingDuration(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((d) => d + 1);
      }, 1000);
    }
  }, []);

  const processAudioBlob = useCallback(async (audioBlob: Blob) => {
    setPhase("processing");
    setErrorMessage(null);

    try {
      const result: RespondResponse = await sendResponse(
        session.session_id,
        audioBlob
      );

      if (result.tone_snapshot) {
        setLatestTone(result.tone_snapshot);
      }

      setTranscript((prev) => [
        ...prev,
        {
          role: "candidate",
          text: result.transcript_text,
          tone: result.tone_snapshot ?? undefined,
        },
      ]);

      setTranscript((prev) => [
        ...prev,
        { role: "interviewer", text: result.interviewer_text },
      ]);

      setQuestionNum(result.question_number);
      lastAudioBlobRef.current = null;

      if (result.is_final) {
        setPhase("done");
        if (faceSnapshotsRef.current.length > 0) {
          await submitFaceData(session.session_id, faceSnapshotsRef.current);
        }
        onComplete(session.session_id);
        return;
      }

      setPhase("ai_speaking");
      try {
        await playAudioUrl(result.interviewer_audio_url);
      } catch {
        // Fallback: just show text
      }
      setPhase("listening");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong";
      console.error("Response processing failed:", err);
      setErrorMessage(message);
      setPhase("error");
    }
  }, [session.session_id, onComplete]);

  const stopRecording = useCallback(async () => {
    if (!recorderRef.current?.isRecording) return;
    setIsRecording(false);

    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }

    const audioBlob = await recorderRef.current.stop();
    lastAudioBlobRef.current = audioBlob;
    await processAudioBlob(audioBlob);
  }, [processAudioBlob]);

  const retryLastResponse = useCallback(async () => {
    if (!lastAudioBlobRef.current) return;
    await processAudioBlob(lastAudioBlobRef.current);
  }, [processAudioBlob]);

  useEffect(() => {
    return () => {
      recorderRef.current?.destroy();
      if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    };
  }, []);

  const formatTime = (sec: number) =>
    `${Math.floor(sec / 60)}:${(sec % 60).toString().padStart(2, "0")}`;

  const showSidebar = faceTrackingOn || latestTone;

  return (
    <div className="max-w-5xl mx-auto flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="pb-4 space-y-3" style={{ borderBottom: "2px solid var(--duo-polar)" }}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-extrabold capitalize" style={{ color: "var(--duo-eel)" }}>
              {session.interview_type.replace("_", " ")} Interview
            </h2>
            <p className="text-sm font-semibold" style={{ color: "var(--duo-wolf)" }}>
              {session.role}
              {session.company ? ` at ${session.company}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <PhaseIndicator phase={phase} />
            <motion.button
              whileTap={{ scale: 0.92 }}
              onClick={() => setFaceTrackingOn(!faceTrackingOn)}
              className="p-2 rounded-xl transition-colors"
              style={{
                background: faceTrackingOn ? "var(--duo-green-light)" : "#f0f0f0",
                color: faceTrackingOn ? "var(--duo-green-push)" : "var(--duo-hare)",
              }}
              title={faceTrackingOn ? "Disable face tracking" : "Enable face tracking"}
            >
              {faceTrackingOn ? (
                <Video className="w-5 h-5" />
              ) : (
                <VideoOff className="w-5 h-5" />
              )}
            </motion.button>
          </div>
        </div>

        {/* Progress path */}
        <div className="flex items-center gap-3">
          <ProgressPath current={questionNum} total={session.num_questions} />
          <span
            className="text-xs font-extrabold whitespace-nowrap px-2 py-1 rounded-lg"
            style={{ background: "var(--duo-blue-light)", color: "var(--duo-blue-push)" }}
          >
            Q{questionNum}/{session.num_questions}
          </span>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex gap-4 min-h-0 mt-4">
        {/* Transcript column */}
        <div
          className={`overflow-y-auto pr-2 space-y-3 transition-all duration-300 ${
            showSidebar ? "flex-1" : "w-full"
          }`}
        >
          <AnimatePresence>
            {transcript.map((turn, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex ${
                  turn.role === "candidate" ? "justify-end" : "justify-start"
                }`}
              >
                <div className="flex items-start gap-2 max-w-[80%]">
                  {turn.role === "interviewer" && (
                    <div
                      className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center mt-1"
                      style={{ background: "var(--duo-blue-light)" }}
                    >
                      <MessageSquare className="w-4 h-4" style={{ color: "var(--duo-blue)" }} />
                    </div>
                  )}
                  <div
                    className="rounded-2xl px-4 py-3"
                    style={
                      turn.role === "candidate"
                        ? {
                            background: "var(--duo-green)",
                            color: "white",
                            borderBottomRightRadius: "6px",
                          }
                        : {
                            background: "white",
                            color: "var(--duo-eel)",
                            border: "2px solid var(--duo-polar)",
                            borderBottomLeftRadius: "6px",
                          }
                    }
                  >
                    <div
                      className="text-xs font-bold mb-1"
                      style={{
                        opacity: 0.7,
                        color: turn.role === "candidate" ? "rgba(255,255,255,0.8)" : "var(--duo-wolf)",
                      }}
                    >
                      {turn.role === "interviewer" ? "Interviewer" : "You"}
                    </div>
                    <p className="text-sm leading-relaxed font-medium">{turn.text}</p>
                    {turn.tone && (
                      <div
                        className="mt-2 pt-2 text-xs font-semibold flex gap-3"
                        style={{
                          borderTop: "1px solid rgba(255,255,255,0.25)",
                          opacity: 0.8,
                        }}
                      >
                        <span>{turn.tone.speaking_pace_wpm.toFixed(0)} WPM</span>
                        {turn.tone.filler_word_count > 0 && (
                          <span>{turn.tone.filler_word_count} fillers</span>
                        )}
                        <span>Energy: {(turn.tone.energy_level * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                  {turn.role === "candidate" && (
                    <div
                      className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center mt-1"
                      style={{ background: "var(--duo-green-light)" }}
                    >
                      <Mic className="w-4 h-4" style={{ color: "var(--duo-green-push)" }} />
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {phase === "processing" && (
            <div className="flex justify-center py-4">
              <div className="flex gap-2">
                <span className="bounce-dot" style={{ background: "var(--duo-blue)", width: "8px", height: "8px" }} />
                <span className="bounce-dot" style={{ background: "var(--duo-blue)", width: "8px", height: "8px" }} />
                <span className="bounce-dot" style={{ background: "var(--duo-blue)", width: "8px", height: "8px" }} />
              </div>
            </div>
          )}

          {/* Tip banner */}
          {!showSidebar && transcript.length > 0 && (
            <div
              className="flex items-center gap-3 px-4 py-3 rounded-2xl text-xs font-semibold"
              style={{
                background: "var(--duo-blue-light)",
                color: "var(--duo-blue-push)",
                border: "2px solid var(--duo-blue)",
              }}
            >
              <span className="font-extrabold">Tip:</span>
              Speak at 130-160 WPM. Use pauses instead of fillers. Structure answers with STAR method.
            </div>
          )}

          <div ref={transcriptEndRef} />
        </div>

        {/* Right sidebar: face tracker + tone metrics */}
        {showSidebar && (
          <div className="w-72 flex-shrink-0 space-y-3 transition-all duration-300">
            <FaceTracker
              active={faceTrackingOn}
              onFrameBatch={handleFaceFrameBatch}
              showPreview={true}
            />

            {latestTone && (
              <div
                className="rounded-2xl p-4 space-y-3"
                style={{
                  background: "white",
                  border: "2px solid var(--duo-polar)",
                }}
              >
                <h3
                  className="text-xs font-bold uppercase tracking-wide flex items-center gap-1.5"
                  style={{ color: "var(--duo-wolf)" }}
                >
                  <Activity className="w-3.5 h-3.5" />
                  Last Response Metrics
                </h3>

                {/* Speaking Pace */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="flex items-center gap-1 font-semibold" style={{ color: "var(--duo-wolf)" }}>
                      <Gauge className="w-3 h-3" /> Pace
                    </span>
                    <span
                      className="font-bold"
                      style={{
                        color:
                          latestTone.speaking_pace_wpm >= 130 && latestTone.speaking_pace_wpm <= 160
                            ? "var(--duo-green)"
                            : latestTone.speaking_pace_wpm > 0
                              ? "var(--duo-orange)"
                              : "var(--duo-hare)",
                      }}
                    >
                      {latestTone.speaking_pace_wpm.toFixed(0)} WPM
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "var(--duo-polar)" }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        background:
                          latestTone.speaking_pace_wpm >= 130 && latestTone.speaking_pace_wpm <= 160
                            ? "var(--duo-green)"
                            : "var(--duo-orange)",
                        width: `${Math.min(100, (latestTone.speaking_pace_wpm / 200) * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] font-medium mt-0.5" style={{ color: "var(--duo-hare)" }}>
                    <span>Slow</span>
                    <span>130-160 ideal</span>
                    <span>Fast</span>
                  </div>
                </div>

                {/* Energy Level */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="font-semibold" style={{ color: "var(--duo-wolf)" }}>Energy</span>
                    <span className="font-bold" style={{ color: "var(--duo-eel)" }}>
                      {(latestTone.energy_level * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: "var(--duo-polar)" }}>
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        background: "var(--duo-blue)",
                        width: `${latestTone.energy_level * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Fillers */}
                <div className="flex justify-between text-xs">
                  <span className="font-semibold" style={{ color: "var(--duo-wolf)" }}>Filler Words</span>
                  <span
                    className="font-bold"
                    style={{
                      color:
                        latestTone.filler_word_count === 0
                          ? "var(--duo-green)"
                          : latestTone.filler_word_count <= 3
                            ? "var(--duo-orange)"
                            : "var(--duo-red)",
                    }}
                  >
                    {latestTone.filler_word_count}
                    {latestTone.filler_word_count === 0 && " (clean)"}
                  </span>
                </div>

                {/* Silence Ratio */}
                <div className="flex justify-between text-xs">
                  <span className="font-semibold" style={{ color: "var(--duo-wolf)" }}>Silence</span>
                  <span className="font-bold" style={{ color: "var(--duo-eel)" }}>
                    {(latestTone.silence_ratio * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="pt-4 mt-4" style={{ borderTop: "2px solid var(--duo-polar)" }}>
        <div className="flex flex-col items-center gap-3">
          {phase === "listening" && (
            <>
              {isRecording ? (
                <div className="flex flex-col items-center gap-3">
                  <span
                    className="text-3xl font-mono font-extrabold tabular-nums"
                    style={{ color: "var(--duo-red)" }}
                  >
                    {formatTime(recordingDuration)}
                  </span>
                  <AudioLevelBars />
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={stopRecording}
                    className="btn-3d btn-3d-red relative flex items-center gap-2 px-8 py-3 rounded-full text-base"
                  >
                    <span
                      className="absolute inset-0 rounded-full opacity-40"
                      style={{
                        border: "2px solid var(--duo-red)",
                        animation: "pulseGlow 2s infinite",
                      }}
                    />
                    <Square className="w-5 h-5 relative" />
                    <span className="relative">Stop Recording</span>
                  </motion.button>
                </div>
              ) : (
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  whileHover={{ scale: 1.03 }}
                  onClick={startRecording}
                  className="btn-3d btn-3d-green relative flex items-center gap-2 px-8 py-3 rounded-full text-base pulse-glow-green"
                >
                  <Mic className="w-5 h-5 relative" />
                  <span className="relative">Start Speaking</span>
                </motion.button>
              )}
            </>
          )}

          {phase === "ai_speaking" && (
            <div
              className="flex items-center gap-2 px-6 py-3 rounded-full font-bold text-sm"
              style={{ background: "var(--duo-orange-light)", color: "var(--duo-orange-push)" }}
            >
              <MessageSquare className="w-5 h-5" />
              Interviewer is speaking...
            </div>
          )}

          {phase === "processing" && (
            <div
              className="flex items-center gap-2 px-6 py-3 rounded-full font-bold text-sm"
              style={{ background: "var(--duo-blue-light)", color: "var(--duo-blue-push)" }}
            >
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing your response...
            </div>
          )}

          {phase === "loading" && (
            <div
              className="flex items-center gap-2 px-6 py-3 rounded-full font-bold text-sm"
              style={{ background: "#f0f0f0", color: "var(--duo-wolf)" }}
            >
              <Loader2 className="w-5 h-5 animate-spin" />
              Preparing interview...
            </div>
          )}

          {phase === "error" && (
            <div className="flex flex-col items-center gap-3">
              <div
                className="px-6 py-3 rounded-2xl text-sm font-semibold max-w-md text-center"
                style={{
                  background: "var(--duo-red-light)",
                  color: "var(--duo-red-push)",
                  border: "2px solid var(--duo-red)",
                }}
              >
                {errorMessage || "Something went wrong processing your response."}
              </div>
              <div className="flex items-center gap-3">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={retryLastResponse}
                  className="btn-3d btn-3d-red flex items-center gap-2 px-6 py-2.5 rounded-full text-sm"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setErrorMessage(null);
                    lastAudioBlobRef.current = null;
                    setPhase("listening");
                  }}
                  className="btn-3d btn-3d-ghost px-6 py-2.5 rounded-full text-sm font-bold"
                >
                  Re-record
                </motion.button>
              </div>
            </div>
          )}

          {phase === "done" && (
            <div
              className="flex items-center gap-2 px-6 py-3 rounded-full font-bold text-sm"
              style={{ background: "var(--duo-green-light)", color: "var(--duo-green-push)" }}
            >
              Interview complete -- generating your feedback report...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
