"use client";

import { use, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  BookOpen,
  Sparkles,
  Trash2,
  Plus,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { getLearnerId } from "@/lib/learner";
import {
  deleteClass,
  generateMoreCards,
  getClassStatus,
  getProgress,
  type ClassStatus,
  type ProgressSummary,
} from "@/lib/api";

interface Props {
  params: Promise<{ classId: string }>;
}

export default function ClassDetailPage({ params }: Props) {
  const { classId } = use(params);
  const router = useRouter();
  const [learnerId, setLearnerId] = useState<string>("");
  const [status, setStatus] = useState<ClassStatus | null>(null);
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [generating, setGenerating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLearnerId(getLearnerId());
  }, []);

  const refresh = useCallback(async () => {
    if (!learnerId) return;
    try {
      const [s, p] = await Promise.all([
        getClassStatus(classId, learnerId),
        getProgress(learnerId, `class:${classId}`),
      ]);
      setStatus(s);
      setProgress(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load class");
    }
  }, [classId, learnerId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (!status) return;
    if (!["parsing", "embedding", "generating"].includes(status.status)) return;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [status, refresh]);

  const onGenerateMore = async () => {
    if (!learnerId) return;
    setGenerating(true);
    setError(null);
    try {
      const s = await generateMoreCards(classId, learnerId, 20);
      setStatus(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const onDelete = async () => {
    if (!learnerId) return;
    if (!window.confirm("Delete this class and all its flashcards?")) return;
    setDeleting(true);
    try {
      await deleteClass(classId, learnerId);
      router.push("/trainer/classes");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
      setDeleting(false);
    }
  };

  const mastered = progress?.mastered ?? 0;
  const total = progress?.total_cards ?? status?.card_count ?? 0;
  const masteredPct = total > 0 ? Math.round((mastered / total) * 100) : 0;
  const isBusy = !!status && ["parsing", "embedding", "generating"].includes(status.status);
  const isReady = status?.status === "ready";

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
          <button
            onClick={onDelete}
            disabled={deleting}
            className="text-xs font-bold flex items-center gap-1 px-2 py-1 rounded-lg"
            style={{ color: "var(--duo-red-push)" }}
          >
            <Trash2 className="w-3.5 h-3.5" /> Delete
          </button>
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

        {!status ? (
          <div className="text-center py-20" style={{ color: "var(--duo-wolf)" }}>
            <Loader2 className="w-6 h-6 mx-auto animate-spin mb-2" />
            <span className="text-sm font-semibold">Loading...</span>
          </div>
        ) : (
          <>
            <div className="text-center mb-8">
              <motion.div
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
                className="inline-flex items-center justify-center w-20 h-20 rounded-2xl mb-5"
                style={{ background: "var(--duo-purple)" }}
              >
                <BookOpen className="w-10 h-10 text-white" />
              </motion.div>
              <h1 className="text-3xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
                {status.title}
              </h1>
              <p className="text-sm font-medium" style={{ color: "var(--duo-wolf)" }}>
                {status.file_count} file{status.file_count !== 1 ? "s" : ""} · {status.chunk_count} chunks · {status.card_count} flashcards
              </p>
            </div>

            {isBusy && (
              <div
                className="mb-6 p-4 rounded-2xl flex items-center gap-3"
                style={{ background: "var(--duo-blue-light)", border: "2px solid var(--duo-blue)" }}
              >
                <Loader2 className="w-5 h-5 animate-spin flex-shrink-0" style={{ color: "var(--duo-blue-push)" }} />
                <div className="flex-1">
                  <div className="text-sm font-bold" style={{ color: "var(--duo-blue-push)" }}>
                    Still working...
                  </div>
                  <div className="text-xs font-medium" style={{ color: "var(--duo-eel)" }}>
                    {status.status === "embedding"
                      ? `Embedded ${status.embedded_chunks} of ${status.chunk_count} chunks`
                      : status.status === "generating"
                      ? "Writing flashcards"
                      : "Parsing files"}
                  </div>
                </div>
              </div>
            )}

            {status.status === "failed" && (
              <div
                className="mb-6 p-4 rounded-2xl"
                style={{ background: "var(--duo-red-light)", border: "2px solid var(--duo-red)" }}
              >
                <div className="text-sm font-bold mb-1" style={{ color: "var(--duo-red-push)" }}>
                  Ingestion failed
                </div>
                <div className="text-xs font-medium" style={{ color: "var(--duo-eel)" }}>
                  {status.error_message || "Unknown error"}
                </div>
              </div>
            )}

            {isReady && total > 0 && (
              <div className="mb-8">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--duo-wolf)" }}>
                    Class mastery
                  </span>
                  <span className="text-xs font-bold" style={{ color: "var(--duo-green-push)" }}>
                    {masteredPct}% mastered
                  </span>
                </div>
                <div className="h-4 rounded-full overflow-hidden flex" style={{ background: "var(--duo-polar)" }}>
                  <Seg count={mastered} total={total} color="var(--duo-green)" />
                  <Seg count={progress?.learning ?? 0} total={total} color="var(--duo-blue)" />
                  <Seg count={progress?.struggling ?? 0} total={total} color="var(--duo-red)" />
                  <Seg count={progress?.new ?? 0} total={total} color="var(--duo-polar)" />
                </div>
                <div className="flex flex-wrap gap-3 mt-2 text-xs font-semibold" style={{ color: "var(--duo-wolf)" }}>
                  <Dot color="var(--duo-green)" label={`${mastered} mastered`} />
                  <Dot color="var(--duo-blue)" label={`${progress?.learning ?? 0} learning`} />
                  <Dot color="var(--duo-red)" label={`${progress?.struggling ?? 0} struggling`} />
                  <Dot color="var(--duo-hare)" label={`${progress?.new ?? 0} new`} />
                </div>
              </div>
            )}

            <div className="space-y-3">
              <motion.button
                onClick={() => router.push(`/trainer?deck=${encodeURIComponent(status.deck)}`)}
                disabled={!isReady || total === 0}
                whileTap={{ scale: 0.98 }}
                whileHover={{ scale: 1.01 }}
                className="btn-3d btn-3d-green w-full py-4 text-lg flex items-center justify-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                Study this class
              </motion.button>

              <button
                onClick={onGenerateMore}
                disabled={!isReady || generating || status.card_count >= 200}
                className="btn-3d btn-3d-blue w-full py-3 text-sm flex items-center justify-center gap-2"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                {status.card_count >= 200 ? "Card cap reached (200)" : "Generate 20 more cards"}
              </button>
            </div>
          </>
        )}
      </div>
    </main>
  );
}

function Seg({ count, total, color }: { count: number; total: number; color: string }) {
  if (count <= 0) return null;
  const pct = (count / total) * 100;
  return <div style={{ width: `${pct}%`, background: color }} />;
}

function Dot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
