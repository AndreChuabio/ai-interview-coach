"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Sparkles, Loader2, Check, AlertTriangle } from "lucide-react";
import ClassFolderDrop from "@/components/ClassFolderDrop";
import { getLearnerId } from "@/lib/learner";
import {
  getClassStatus,
  uploadClass,
  type ClassStatus,
} from "@/lib/api";

type Phase = "pick" | "uploading" | "processing" | "ready" | "failed";

const PHASE_ORDER = ["parsing", "embedding", "generating", "ready"] as const;

function phaseProgress(status: ClassStatus): number {
  const stageIdx = PHASE_ORDER.indexOf(status.status as (typeof PHASE_ORDER)[number]);
  if (status.status === "failed") return 0;
  if (status.status === "ready") return 1;
  if (stageIdx < 0) return 0;
  const stageFrac = stageIdx / (PHASE_ORDER.length - 1);
  // Inside 'embedding', blend the embedded_chunks/chunk_count as a sub-progress.
  if (status.status === "embedding" && status.chunk_count > 0) {
    const sub = status.embedded_chunks / status.chunk_count;
    const nextFrac = (stageIdx + 1) / (PHASE_ORDER.length - 1);
    return stageFrac + (nextFrac - stageFrac) * sub;
  }
  return stageFrac;
}

export default function NewClassPage() {
  const router = useRouter();
  const [learnerId, setLearnerId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [phase, setPhase] = useState<Phase>("pick");
  const [uploadPct, setUploadPct] = useState(0);
  const [status, setStatus] = useState<ClassStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [skipped, setSkipped] = useState<string[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    setLearnerId(getLearnerId());
  }, []);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const startPolling = useCallback(
    (classId: string) => {
      stopPolling();
      let intervalMs = 2000;
      let lastStatus = "";
      let stableTicks = 0;
      const tick = async () => {
        try {
          const s = await getClassStatus(classId, learnerId);
          setStatus(s);
          if (s.status === "ready") {
            setPhase("ready");
            stopPolling();
            return;
          }
          if (s.status === "failed") {
            setPhase("failed");
            setError(s.error_message || "Ingestion failed");
            stopPolling();
            return;
          }
          if (s.status === lastStatus) {
            stableTicks += 1;
          } else {
            stableTicks = 0;
            lastStatus = s.status;
          }
          // If nothing has changed for 60s, back off to every 8s.
          if (stableTicks >= 30 && intervalMs < 8000) {
            stopPolling();
            intervalMs = 8000;
            pollRef.current = setInterval(tick, intervalMs);
          }
        } catch (err) {
          setError(err instanceof Error ? err.message : "Polling failed");
        }
      };
      pollRef.current = setInterval(tick, intervalMs);
      void tick();
    },
    [learnerId, stopPolling]
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!learnerId || !title.trim() || files.length === 0) return;
    setError(null);
    setPhase("uploading");
    setUploadPct(0);
    try {
      const res = await uploadClass(learnerId, title.trim(), files, (p) =>
        setUploadPct(p)
      );
      setSkipped(res.skipped_files || []);
      if (res.status === "failed") {
        setPhase("failed");
        setError(
          "No text could be extracted from any file. Make sure your PDFs contain selectable text (not scans)."
        );
        return;
      }
      setPhase("processing");
      setStatus({
        class_id: res.class_id,
        title: res.title,
        deck: res.deck,
        status: res.status,
        file_count: res.file_count,
        chunk_count: res.chunk_count,
        embedded_chunks: 0,
        progress: 0,
        card_count: 0,
        error_message: "",
      });
      startPolling(res.class_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setPhase("pick");
    }
  };

  const canSubmit =
    phase === "pick" && learnerId && title.trim().length > 0 && files.length > 0;

  return (
    <main className="min-h-screen" style={{ background: "var(--background)" }}>
      <nav className="sticky top-0 z-30 bg-white border-b-2" style={{ borderColor: "var(--duo-polar)" }}>
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href="/trainer/classes"
            className="text-sm font-bold flex items-center gap-1"
            style={{ color: "var(--duo-blue)" }}
          >
            <ArrowLeft className="w-4 h-4" /> My classes
          </Link>
          <span className="text-base font-extrabold" style={{ color: "var(--duo-eel)" }}>
            New class
          </span>
          <span className="w-12" />
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {error && (
          <div
            className="mb-6 p-4 rounded-2xl text-sm font-semibold flex items-center gap-2"
            style={{
              background: "var(--duo-red-light)",
              color: "var(--duo-red-push)",
              border: "2px solid var(--duo-red)",
            }}
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {(phase === "pick" || phase === "uploading") && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                className="block text-xs font-bold uppercase tracking-wide mb-2"
                style={{ color: "var(--duo-wolf)" }}
              >
                Class title
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., CS 584 -- Machine Learning"
                maxLength={200}
                className="w-full px-4 py-3 rounded-2xl text-base font-semibold focus:outline-none transition-all"
                style={{
                  border: "2px solid var(--duo-polar)",
                  color: "var(--duo-eel)",
                  background: "white",
                }}
                disabled={phase !== "pick"}
              />
            </div>

            <div>
              <label
                className="block text-xs font-bold uppercase tracking-wide mb-2"
                style={{ color: "var(--duo-wolf)" }}
              >
                Class folder
              </label>
              <ClassFolderDrop
                onFilesChanged={setFiles}
                disabled={phase !== "pick"}
              />
            </div>

            {phase === "uploading" && (
              <div
                className="rounded-2xl p-4"
                style={{
                  background: "var(--duo-blue-light)",
                  border: "2px solid var(--duo-blue)",
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <Loader2 className="w-4 h-4 animate-spin" style={{ color: "var(--duo-blue-push)" }} />
                  <span className="text-sm font-bold" style={{ color: "var(--duo-blue-push)" }}>
                    Uploading... {Math.round(uploadPct * 100)}%
                  </span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: "white" }}>
                  <div
                    className="h-full transition-all"
                    style={{
                      width: `${Math.round(uploadPct * 100)}%`,
                      background: "var(--duo-blue)",
                    }}
                  />
                </div>
              </div>
            )}

            <motion.button
              type="submit"
              disabled={!canSubmit}
              whileTap={{ scale: 0.98 }}
              className="btn-3d btn-3d-green w-full py-4 text-base flex items-center justify-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              Upload and generate cards
            </motion.button>
          </form>
        )}

        {phase === "processing" && status && (
          <ProcessingView status={status} />
        )}

        {phase === "ready" && status && (
          <ReadyView status={status} skipped={skipped} onStudy={() => router.push(`/trainer/classes/${status.class_id}`)} />
        )}

        {phase === "failed" && status && (
          <FailedView
            status={status}
            onRetry={() => {
              setPhase("pick");
              setStatus(null);
              setError(null);
            }}
          />
        )}
      </div>
    </main>
  );
}

function ProcessingView({ status }: { status: ClassStatus }) {
  const pct = Math.round(phaseProgress(status) * 100);
  const stageLabel = {
    parsing: "Parsing files...",
    embedding: `Embedding chunks (${status.embedded_chunks}/${status.chunk_count})`,
    generating: "Writing flashcards...",
    ready: "Done",
    failed: "Failed",
  }[status.status] ?? status.status;

  return (
    <div className="text-center py-10">
      <Loader2 className="w-10 h-10 mx-auto animate-spin mb-5" style={{ color: "var(--duo-purple-push)" }} />
      <h2 className="text-xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
        {stageLabel}
      </h2>
      <p className="text-sm font-medium mb-6" style={{ color: "var(--duo-wolf)" }}>
        This can take a minute or two for larger classes. You can leave this page open.
      </p>
      <div className="max-w-md mx-auto">
        <div className="h-3 rounded-full overflow-hidden" style={{ background: "var(--duo-polar)" }}>
          <div
            className="h-full transition-all"
            style={{
              width: `${pct}%`,
              background: "var(--duo-purple)",
            }}
          />
        </div>
        <div className="flex justify-between mt-2 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--duo-hare)" }}>
          <span>Parse</span>
          <span>Embed</span>
          <span>Write</span>
          <span>Ready</span>
        </div>
      </div>
    </div>
  );
}

function ReadyView({
  status,
  skipped,
  onStudy,
}: {
  status: ClassStatus;
  skipped: string[];
  onStudy: () => void;
}) {
  return (
    <div className="text-center py-10">
      <div
        className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
        style={{ background: "var(--duo-green)" }}
      >
        <Check className="w-9 h-9 text-white" strokeWidth={3} />
      </div>
      <h2 className="text-2xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
        Your class is ready
      </h2>
      <p className="text-base font-medium mb-4" style={{ color: "var(--duo-wolf)" }}>
        {status.card_count} flashcard{status.card_count !== 1 ? "s" : ""} generated from {status.file_count} file{status.file_count !== 1 ? "s" : ""} ({status.chunk_count} chunks).
      </p>
      {skipped.length > 0 && (
        <div
          className="max-w-md mx-auto mb-4 p-3 rounded-2xl text-xs font-semibold text-left"
          style={{
            background: "var(--duo-orange-light)",
            color: "var(--duo-orange-push)",
            border: "2px solid var(--duo-orange)",
          }}
        >
          <div className="font-bold mb-1">Skipped files:</div>
          <ul className="list-disc list-inside space-y-0.5">
            {skipped.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}
      <button
        onClick={onStudy}
        className="btn-3d btn-3d-green inline-flex items-center gap-2 px-8 py-3"
      >
        <Sparkles className="w-5 h-5" />
        Open class
      </button>
    </div>
  );
}

function FailedView({ status, onRetry }: { status: ClassStatus; onRetry: () => void }) {
  return (
    <div className="text-center py-10">
      <div
        className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
        style={{ background: "var(--duo-red)" }}
      >
        <AlertTriangle className="w-8 h-8 text-white" />
      </div>
      <h2 className="text-2xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
        Something went wrong
      </h2>
      <p className="text-sm font-medium mb-6 max-w-md mx-auto" style={{ color: "var(--duo-wolf)" }}>
        {status.error_message || "The class could not be prepared. Try a smaller folder, or make sure PDFs contain selectable text."}
      </p>
      <button onClick={onRetry} className="btn-3d btn-3d-blue px-6 py-3">
        Try again
      </button>
    </div>
  );
}
