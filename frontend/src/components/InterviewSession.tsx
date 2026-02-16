"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
/*  Progress Bar                                                       */
/* ------------------------------------------------------------------ */
function ProgressBar({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  return (
    <div className="flex items-center gap-1.5 w-full">
      {Array.from({ length: total }, (_, i) => {
        const idx = i + 1;
        const done = idx < current;
        const active = idx === current;
        return (
          <div
            key={i}
            className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
              done
                ? "bg-blue-500"
                : active
                  ? "bg-blue-400 animate-pulse"
                  : "bg-gray-200 dark:bg-gray-700"
            }`}
          />
        );
      })}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Audio Level Bars (CSS animation during recording)                   */
/* ------------------------------------------------------------------ */
function AudioLevelBars() {
  return (
    <div className="flex items-end gap-0.5 h-5">
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          className="w-1 bg-red-400 rounded-full"
          style={{
            animation: `audioBar 0.8s ease-in-out ${i * 0.1}s infinite alternate`,
          }}
        />
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Phase Indicator                                                     */
/* ------------------------------------------------------------------ */
function PhaseIndicator({ phase }: { phase: Phase }) {
  const colors: Record<Phase, string> = {
    loading: "bg-gray-400",
    ai_speaking: "bg-yellow-400",
    listening: "bg-green-400 animate-pulse",
    processing: "bg-blue-400 animate-pulse",
    done: "bg-green-500",
    error: "bg-red-500",
  };

  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      <span className={`w-2 h-2 rounded-full ${colors[phase]}`} />
      {phase === "listening" ? "Your turn" : phase.replace("_", " ")}
    </div>
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

  // Accumulated face data to send on interview completion
  const faceSnapshotsRef = useRef<FaceSnapshot[]>([]);
  const lastAudioBlobRef = useRef<Blob | null>(null);
  const recorderRef = useRef<AudioRecorder | null>(null);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  // Initialize and play opening question
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

  // Handle face frame batches from FaceTracker
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

  // Start recording
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

  // Process an audio blob (shared by stopRecording and retryLastResponse)
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

      // Add candidate turn
      setTranscript((prev) => [
        ...prev,
        {
          role: "candidate",
          text: result.transcript_text,
          tone: result.tone_snapshot ?? undefined,
        },
      ]);

      // Add interviewer turn
      setTranscript((prev) => [
        ...prev,
        { role: "interviewer", text: result.interviewer_text },
      ]);

      setQuestionNum(result.question_number);
      lastAudioBlobRef.current = null;

      if (result.is_final) {
        setPhase("done");
        // Submit accumulated face data
        if (faceSnapshotsRef.current.length > 0) {
          await submitFaceData(session.session_id, faceSnapshotsRef.current);
        }
        onComplete(session.session_id);
        return;
      }

      // Play interviewer audio
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

  // Stop recording and send to backend
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

  // Retry the last failed response without re-recording
  const retryLastResponse = useCallback(async () => {
    if (!lastAudioBlobRef.current) return;
    await processAudioBlob(lastAudioBlobRef.current);
  }, [processAudioBlob]);

  // Cleanup
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
      <div className="pb-4 border-b border-gray-200 dark:border-gray-700 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
              {session.interview_type.replace("_", " ")} Interview
            </h2>
            <p className="text-sm text-gray-500">
              {session.role}
              {session.company ? ` at ${session.company}` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <PhaseIndicator phase={phase} />
            <button
              onClick={() => setFaceTrackingOn(!faceTrackingOn)}
              className={`p-2 rounded-lg transition-colors ${
                faceTrackingOn
                  ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                  : "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400"
              }`}
              title={faceTrackingOn ? "Disable face tracking" : "Enable face tracking"}
            >
              {faceTrackingOn ? (
                <Video className="w-5 h-5" />
              ) : (
                <VideoOff className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="flex items-center gap-3">
          <ProgressBar current={questionNum} total={session.num_questions} />
          <span className="text-xs text-gray-400 whitespace-nowrap">
            {questionNum}/{session.num_questions}
          </span>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex gap-4 min-h-0 mt-4">
        {/* Transcript column -- expands to full width when sidebar hidden */}
        <div
          className={`overflow-y-auto pr-2 space-y-4 transition-all duration-300 ${
            showSidebar ? "flex-1" : "w-full"
          }`}
        >
          {transcript.map((turn, i) => (
            <div
              key={i}
              className={`flex ${
                turn.role === "candidate" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  turn.role === "candidate"
                    ? "bg-blue-600 text-white rounded-br-md"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-md"
                }`}
              >
                <div className="text-xs font-medium mb-1 opacity-70">
                  {turn.role === "interviewer" ? "Interviewer" : "You"}
                </div>
                <p className="text-sm leading-relaxed">{turn.text}</p>
                {turn.tone && (
                  <div className="mt-2 pt-2 border-t border-white/20 text-xs opacity-70 flex gap-3">
                    <span>{turn.tone.speaking_pace_wpm.toFixed(0)} WPM</span>
                    {turn.tone.filler_word_count > 0 && (
                      <span>{turn.tone.filler_word_count} fillers</span>
                    )}
                    <span>Energy: {(turn.tone.energy_level * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {phase === "processing" && (
            <div className="flex justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          )}

          {/* Inline tip banner when sidebar is hidden and no tone data yet */}
          {!showSidebar && transcript.length > 0 && (
            <div className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 text-xs text-blue-600 dark:text-blue-400">
              <span className="font-medium">Tip:</span>
              Speak at 130-160 WPM. Use pauses instead of fillers. Structure answers with STAR method.
            </div>
          )}

          <div ref={transcriptEndRef} />
        </div>

        {/* Right sidebar: face tracker + tone metrics -- only when needed */}
        {showSidebar && (
          <div className="w-72 flex-shrink-0 space-y-3 transition-all duration-300">
            {/* Face Tracker */}
            <FaceTracker
              active={faceTrackingOn}
              onFrameBatch={handleFaceFrameBatch}
              showPreview={true}
            />

            {/* Real-time Tone Metrics */}
            {latestTone && (
              <div className="bg-white dark:bg-gray-800 rounded-xl p-3 border border-gray-200 dark:border-gray-700 space-y-3">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5" />
                  Last Response Metrics
                </h3>

                {/* Speaking Pace */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500 flex items-center gap-1">
                      <Gauge className="w-3 h-3" /> Pace
                    </span>
                    <span className={`font-medium ${
                      latestTone.speaking_pace_wpm >= 130 && latestTone.speaking_pace_wpm <= 160
                        ? "text-green-600"
                        : latestTone.speaking_pace_wpm > 0
                          ? "text-amber-600"
                          : "text-gray-400"
                    }`}>
                      {latestTone.speaking_pace_wpm.toFixed(0)} WPM
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        latestTone.speaking_pace_wpm >= 130 && latestTone.speaking_pace_wpm <= 160
                          ? "bg-green-500"
                          : "bg-amber-500"
                      }`}
                      style={{
                        width: `${Math.min(100, (latestTone.speaking_pace_wpm / 200) * 100)}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-400 mt-0.5">
                    <span>Slow</span>
                    <span>130-160 ideal</span>
                    <span>Fast</span>
                  </div>
                </div>

                {/* Energy Level */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">Energy</span>
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {(latestTone.energy_level * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${latestTone.energy_level * 100}%` }}
                    />
                  </div>
                </div>

                {/* Fillers */}
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Filler Words</span>
                  <span
                    className={`font-medium ${
                      latestTone.filler_word_count === 0
                        ? "text-green-600"
                        : latestTone.filler_word_count <= 3
                          ? "text-amber-600"
                          : "text-red-600"
                    }`}
                  >
                    {latestTone.filler_word_count}
                    {latestTone.filler_word_count === 0 && " (clean)"}
                  </span>
                </div>

                {/* Silence Ratio */}
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">Silence</span>
                  <span className="font-medium text-gray-700 dark:text-gray-300">
                    {(latestTone.silence_ratio * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 mt-4">
        <div className="flex flex-col items-center gap-2">
          {phase === "listening" && (
            <>
              {isRecording ? (
                <div className="flex flex-col items-center gap-2">
                  {/* Timer -- prominent */}
                  <span className="text-2xl font-mono font-semibold text-red-500 tabular-nums">
                    {formatTime(recordingDuration)}
                  </span>
                  <AudioLevelBars />
                  <button
                    onClick={stopRecording}
                    className="relative flex items-center gap-2 px-8 py-3 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium transition-colors"
                  >
                    {/* Pulsing ring */}
                    <span className="absolute inset-0 rounded-full border-2 border-red-400 animate-ping opacity-40" />
                    <Square className="w-5 h-5 relative" />
                    <span className="relative">Stop Recording</span>
                  </button>
                </div>
              ) : (
                <button
                  onClick={startRecording}
                  className="relative flex items-center gap-2 px-8 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-medium transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
                >
                  {/* Gentle pulse ring */}
                  <span className="absolute inset-0 rounded-full border-2 border-blue-400 animate-pulse opacity-30" />
                  <Mic className="w-5 h-5 relative" />
                  <span className="relative">Start Speaking</span>
                </button>
              )}
            </>
          )}

          {phase === "ai_speaking" && (
            <div className="flex items-center gap-2 px-6 py-3 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
              <MessageSquare className="w-5 h-5" />
              Interviewer is speaking...
            </div>
          )}

          {phase === "processing" && (
            <div className="flex items-center gap-2 px-6 py-3 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing your response...
            </div>
          )}

          {phase === "loading" && (
            <div className="flex items-center gap-2 px-6 py-3 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">
              <Loader2 className="w-5 h-5 animate-spin" />
              Preparing interview...
            </div>
          )}

          {phase === "error" && (
            <div className="flex flex-col items-center gap-3">
              <div className="px-6 py-3 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300 max-w-md text-center">
                {errorMessage || "Something went wrong processing your response."}
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={retryLastResponse}
                  className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-medium transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
                <button
                  onClick={() => {
                    setErrorMessage(null);
                    lastAudioBlobRef.current = null;
                    setPhase("listening");
                  }}
                  className="px-6 py-2.5 rounded-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium transition-colors"
                >
                  Re-record
                </button>
              </div>
            </div>
          )}

          {phase === "done" && (
            <div className="flex items-center gap-2 px-6 py-3 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 font-medium">
              Interview complete -- generating your feedback report...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
