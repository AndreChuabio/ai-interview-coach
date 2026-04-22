"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Plus,
  FolderOpen,
  Trash2,
  ArrowLeft,
  BookOpen,
  AlertTriangle,
  Loader2,
} from "lucide-react";
import { getLearnerId } from "@/lib/learner";
import { deleteClass, listClasses, type ClassSummary } from "@/lib/api";

const STATUS_LABELS: Record<string, { label: string; color: string; bg: string; border: string }> = {
  parsing:    { label: "Parsing",    color: "var(--duo-blue-push)",   bg: "var(--duo-blue-light)",   border: "var(--duo-blue)" },
  embedding:  { label: "Embedding",  color: "var(--duo-blue-push)",   bg: "var(--duo-blue-light)",   border: "var(--duo-blue)" },
  generating: { label: "Writing",    color: "var(--duo-purple-push)", bg: "var(--duo-purple-light)", border: "var(--duo-purple)" },
  ready:      { label: "Ready",      color: "var(--duo-green-push)",  bg: "var(--duo-green-light)",  border: "var(--duo-green)" },
  failed:     { label: "Failed",     color: "var(--duo-red-push)",    bg: "var(--duo-red-light)",    border: "var(--duo-red)" },
};

export default function ClassesPage() {
  const [learnerId, setLearnerId] = useState<string>("");
  const [classes, setClasses] = useState<ClassSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    setLearnerId(getLearnerId());
  }, []);

  const refresh = useCallback(async () => {
    if (!learnerId) return;
    try {
      const list = await listClasses(learnerId);
      setClasses(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load classes");
    }
  }, [learnerId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Re-poll while any class is still processing so the UI stays fresh.
  useEffect(() => {
    if (!classes) return;
    const anyPending = classes.some((c) =>
      ["parsing", "embedding", "generating"].includes(c.status)
    );
    if (!anyPending) return;
    const t = setInterval(refresh, 3000);
    return () => clearInterval(t);
  }, [classes, refresh]);

  const onDelete = async (classId: string) => {
    if (!learnerId) return;
    if (!window.confirm("Delete this class and its flashcards?")) return;
    setDeleting(classId);
    try {
      await deleteClass(classId, learnerId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <main className="min-h-screen" style={{ background: "var(--background)" }}>
      <nav className="sticky top-0 z-30 bg-white border-b-2" style={{ borderColor: "var(--duo-polar)" }}>
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <Link
            href="/trainer"
            className="text-sm font-bold flex items-center gap-1"
            style={{ color: "var(--duo-blue)" }}
          >
            <ArrowLeft className="w-4 h-4" /> Trainer
          </Link>
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "var(--duo-purple)" }}
            >
              <BookOpen className="w-[18px] h-[18px] text-white" />
            </div>
            <span className="text-base font-extrabold" style={{ color: "var(--duo-eel)" }}>
              My Classes
            </span>
          </div>
          <Link
            href="/trainer/classes/new"
            className="btn-3d btn-3d-green text-sm px-3 py-1.5 flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> New
          </Link>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        {error && (
          <div
            className="mb-6 p-4 rounded-2xl text-sm font-semibold flex items-center justify-between"
            style={{
              background: "var(--duo-red-light)",
              color: "var(--duo-red-push)",
              border: "2px solid var(--duo-red)",
            }}
          >
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-3 font-bold underline">
              Dismiss
            </button>
          </div>
        )}

        {classes === null ? (
          <div className="text-center py-20" style={{ color: "var(--duo-wolf)" }}>
            <Loader2 className="w-6 h-6 mx-auto animate-spin mb-2" />
            <span className="text-sm font-semibold">Loading your classes...</span>
          </div>
        ) : classes.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="space-y-3">
            {classes.map((cls, i) => {
              const status = STATUS_LABELS[cls.status] ?? STATUS_LABELS.parsing;
              const busy = ["parsing", "embedding", "generating"].includes(cls.status);
              return (
                <motion.li
                  key={cls.class_id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.25 }}
                  className="duo-card p-4 flex items-center justify-between"
                >
                  <Link
                    href={`/trainer/classes/${cls.class_id}`}
                    className="flex-1 flex items-center gap-3 min-w-0"
                  >
                    <div
                      className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ background: "var(--duo-purple-light)" }}
                    >
                      <FolderOpen className="w-5 h-5" style={{ color: "var(--duo-purple-push)" }} />
                    </div>
                    <div className="min-w-0">
                      <div className="font-extrabold truncate" style={{ color: "var(--duo-eel)" }}>
                        {cls.title}
                      </div>
                      <div className="text-xs font-medium flex gap-2" style={{ color: "var(--duo-wolf)" }}>
                        <span>{cls.file_count} file{cls.file_count !== 1 ? "s" : ""}</span>
                        <span>·</span>
                        <span>{cls.chunk_count} chunks</span>
                        <span>·</span>
                        <span>{cls.card_count} cards</span>
                      </div>
                    </div>
                  </Link>

                  <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                    <span
                      className="text-[10px] font-extrabold uppercase px-2.5 py-1 rounded-full flex items-center gap-1.5"
                      style={{ background: status.bg, color: status.color, border: `1px solid ${status.border}` }}
                    >
                      {busy && <Loader2 className="w-3 h-3 animate-spin" />}
                      {cls.status === "failed" && <AlertTriangle className="w-3 h-3" />}
                      {status.label}
                    </span>
                    <button
                      type="button"
                      disabled={deleting === cls.class_id}
                      onClick={() => onDelete(cls.class_id)}
                      className="p-1.5 rounded-lg transition-colors"
                      style={{ color: "var(--duo-hare)" }}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.li>
              );
            })}
          </ul>
        )}
      </div>
    </main>
  );
}

function EmptyState() {
  return (
    <div className="text-center py-20">
      <div
        className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
        style={{ background: "var(--duo-purple-light)" }}
      >
        <FolderOpen className="w-8 h-8" style={{ color: "var(--duo-purple-push)" }} />
      </div>
      <h2 className="text-2xl font-extrabold mb-2" style={{ color: "var(--duo-eel)" }}>
        No classes yet
      </h2>
      <p className="text-base font-medium mb-6" style={{ color: "var(--duo-wolf)" }}>
        Drop a folder of lecture notes, slides, or readings and we'll generate flashcards from it.
      </p>
      <Link
        href="/trainer/classes/new"
        className="btn-3d btn-3d-green inline-flex items-center gap-2 px-6 py-3 text-base"
      >
        <Plus className="w-5 h-5" />
        Upload your first class
      </Link>
    </div>
  );
}
