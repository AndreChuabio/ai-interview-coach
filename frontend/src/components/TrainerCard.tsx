"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, ChevronRight, Lightbulb, FileText } from "lucide-react";
import { submitCardAnswer, type AnswerResponse, type TrainerCard as Card } from "@/lib/api";

interface Props {
  card: Card;
  learnerId: string;
  onNext: () => void;
}

const GRADE_BANDS: { min: number; label: string; color: string; bg: string; border: string }[] = [
  { min: 5, label: "Perfect", color: "var(--duo-green-push)", bg: "var(--duo-green-light)", border: "var(--duo-green)" },
  { min: 4, label: "Strong", color: "var(--duo-green-push)", bg: "var(--duo-green-light)", border: "var(--duo-green)" },
  { min: 3, label: "OK", color: "var(--duo-orange-push)", bg: "var(--duo-orange-light)", border: "var(--duo-orange)" },
  { min: 2, label: "Weak", color: "var(--duo-orange-push)", bg: "var(--duo-orange-light)", border: "var(--duo-orange)" },
  { min: 0, label: "Needs work", color: "var(--duo-red-push)", bg: "var(--duo-red-light)", border: "var(--duo-red)" },
];

function gradeBand(score: number) {
  return GRADE_BANDS.find((b) => score >= b.min) ?? GRADE_BANDS[GRADE_BANDS.length - 1];
}

export default function TrainerCard({ card, learnerId, onNext }: Props) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState<AnswerResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const startTime = useRef<number>(Date.now());

  useEffect(() => {
    // New card -- reset everything
    setAnswer("");
    setResult(null);
    setError(null);
    startTime.current = Date.now();
  }, [card.id]);

  const handleSubmit = async () => {
    if (!answer.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const elapsed = Date.now() - startTime.current;
      const resp = await submitCardAnswer(card.id, learnerId, answer, elapsed);
      setResult(resp);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to grade answer");
    } finally {
      setSubmitting(false);
    }
  };

  const band = result ? gradeBand(result.score) : null;

  return (
    <div className="max-w-2xl mx-auto">
      {/* Topic + difficulty pill */}
      <div className="flex items-center justify-between mb-4">
        <span
          className="text-xs font-extrabold uppercase tracking-wide px-3 py-1 rounded-full"
          style={{ background: "var(--duo-purple-light)", color: "var(--duo-purple-push)" }}
        >
          {card.topic}
        </span>
        <span
          className="text-xs font-bold uppercase tracking-wide px-3 py-1 rounded-full"
          style={{ background: "var(--duo-polar)", color: "var(--duo-wolf)" }}
        >
          {card.difficulty}
        </span>
      </div>

      {/* Question card */}
      <motion.div
        key={card.id}
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="duo-card p-6 mb-6"
        style={{ background: "white", borderLeft: "4px solid var(--duo-purple)" }}
      >
        <div className="text-xs font-bold uppercase mb-2" style={{ color: "var(--duo-wolf)" }}>
          Question
        </div>
        <p className="text-lg font-semibold leading-relaxed" style={{ color: "var(--duo-eel)" }}>
          {card.question}
        </p>
      </motion.div>

      {/* Answer textarea (hidden once graded) */}
      {!result && (
        <div className="mb-4">
          <label className="block text-xs font-bold uppercase mb-2" style={{ color: "var(--duo-wolf)" }}>
            Your answer
          </label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
            }}
            placeholder="Type what you remember -- key ideas, not word-perfect"
            rows={6}
            className="w-full px-4 py-3 rounded-2xl text-base font-medium focus:outline-none transition-all resize-none"
            style={{
              border: "2px solid var(--duo-polar)",
              color: "var(--duo-eel)",
              background: "white",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--duo-blue)";
              e.currentTarget.style.boxShadow = "0 0 0 3px var(--duo-blue-light)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--duo-polar)";
              e.currentTarget.style.boxShadow = "none";
            }}
          />
          <div className="flex justify-between items-center mt-1">
            <span className="text-xs font-medium" style={{ color: "var(--duo-hare)" }}>
              Ctrl/Cmd + Enter to submit
            </span>
            <span className="text-xs font-medium" style={{ color: "var(--duo-hare)" }}>
              {answer.length} chars
            </span>
          </div>
        </div>
      )}

      {error && (
        <div
          className="mb-4 p-3 rounded-2xl text-sm font-semibold"
          style={{ background: "var(--duo-red-light)", color: "var(--duo-red-push)", border: "2px solid var(--duo-red)" }}
        >
          {error}
        </div>
      )}

      {/* Result panel */}
      <AnimatePresence>
        {result && band && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-4 mb-6"
          >
            {/* Score banner */}
            <div
              className="rounded-2xl p-5 flex items-center gap-4"
              style={{ background: band.bg, border: `2px solid ${band.border}` }}
            >
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ background: band.border }}
              >
                {result.score >= 3 ? (
                  <Check className="w-7 h-7 text-white" strokeWidth={3} />
                ) : (
                  <X className="w-7 h-7 text-white" strokeWidth={3} />
                )}
              </div>
              <div className="flex-1">
                <div className="text-sm font-bold uppercase" style={{ color: band.color }}>
                  {band.label}
                </div>
                <div className="text-2xl font-extrabold" style={{ color: band.color }}>
                  {result.score} / 5
                </div>
              </div>
            </div>

            {/* Feedback */}
            {result.feedback && (
              <div
                className="rounded-2xl p-4"
                style={{ background: "var(--duo-blue-light)", border: "2px solid var(--duo-blue)" }}
              >
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: "var(--duo-blue-push)" }} />
                  <p className="text-sm font-semibold leading-relaxed" style={{ color: "var(--duo-eel)" }}>
                    {result.feedback}
                  </p>
                </div>
              </div>
            )}

            {/* Missing concepts */}
            {result.missing_concepts.length > 0 && (
              <div>
                <div className="text-xs font-bold uppercase mb-2" style={{ color: "var(--duo-wolf)" }}>
                  Missed
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.missing_concepts.map((c, i) => (
                    <span
                      key={i}
                      className="text-xs font-bold px-3 py-1 rounded-full"
                      style={{
                        background: "var(--duo-red-light)",
                        color: "var(--duo-red-push)",
                        border: "1px solid var(--duo-red)",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Reference answer */}
            <div>
              <div className="text-xs font-bold uppercase mb-2" style={{ color: "var(--duo-wolf)" }}>
                Reference answer
              </div>
              <div
                className="duo-card p-4 text-sm leading-relaxed font-medium"
                style={{ background: "white", color: "var(--duo-eel)" }}
              >
                {card.reference_answer}
              </div>
              {card.source_citation && (
                <div
                  className="mt-2 flex items-center gap-1.5 text-[11px] font-semibold"
                  style={{ color: "var(--duo-hare)" }}
                >
                  <FileText className="w-3 h-3" />
                  <span className="truncate">
                    From {card.source_citation.filename}
                    {card.source_citation.page > 0 ? ` · p.${card.source_citation.page}` : ""}
                    {card.source_citation.heading ? ` · ${card.source_citation.heading}` : ""}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Action button */}
      {!result ? (
        <motion.button
          onClick={handleSubmit}
          disabled={!answer.trim() || submitting}
          whileTap={{ scale: 0.98 }}
          className="btn-3d btn-3d-green w-full py-4 text-base"
        >
          {submitting ? "Grading..." : "Check answer"}
        </motion.button>
      ) : (
        <motion.button
          onClick={onNext}
          whileTap={{ scale: 0.98 }}
          className="btn-3d btn-3d-blue w-full py-4 text-base flex items-center justify-center gap-2"
        >
          Next card <ChevronRight className="w-5 h-5" />
        </motion.button>
      )}
    </div>
  );
}
