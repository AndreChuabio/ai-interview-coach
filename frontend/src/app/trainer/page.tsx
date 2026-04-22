"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, BookOpen } from "lucide-react";
import TrainerDashboard from "@/components/TrainerDashboard";
import TrainerCard from "@/components/TrainerCard";
import { getLearnerId } from "@/lib/learner";
import {
  getNextCard,
  getProgress,
  registerLearner,
  type NextCardResponse,
  type ProgressSummary,
  type TrainerCard as Card,
} from "@/lib/api";

type Phase = "dashboard" | "studying" | "empty";

const DEFAULT_DECK = "ml_fundamentals";

export default function TrainerPage() {
  return (
    <Suspense fallback={<main className="min-h-screen" style={{ background: "var(--background)" }} />}>
      <TrainerInner />
    </Suspense>
  );
}

function TrainerInner() {
  const searchParams = useSearchParams();
  const deck = searchParams.get("deck") || DEFAULT_DECK;
  const isClassDeck = deck.startsWith("class:");
  const headerTitle = isClassDeck ? "Class Study" : "ML Trainer";

  const [learnerId, setLearnerId] = useState<string>("");
  const [phase, setPhase] = useState<Phase>("dashboard");
  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [card, setCard] = useState<Card | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const id = getLearnerId();
    setLearnerId(id);
    if (id) {
      registerLearner(id).catch(() => {
        /* non-fatal */
      });
    }
  }, []);

  const refreshProgress = useCallback(async () => {
    if (!learnerId) return;
    try {
      const p = await getProgress(learnerId, isClassDeck ? deck : undefined);
      setProgress(p);
    } catch (err) {
      console.warn("Progress fetch failed", err);
    }
  }, [learnerId, deck, isClassDeck]);

  useEffect(() => {
    refreshProgress();
  }, [refreshProgress]);

  const loadNext = useCallback(async (): Promise<NextCardResponse | null> => {
    if (!learnerId) return null;
    try {
      return await getNextCard(learnerId, deck);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load next card");
      return null;
    }
  }, [learnerId, deck]);

  const handleStart = async () => {
    if (!learnerId) return;
    setLoading(true);
    setError(null);
    const next = await loadNext();
    setLoading(false);
    if (!next) return;
    if (!next.card) {
      setPhase("empty");
      return;
    }
    setCard(next.card);
    setPhase("studying");
  };

  const handleNext = async () => {
    await refreshProgress();
    const next = await loadNext();
    if (!next || !next.card) {
      setCard(null);
      setPhase("empty");
      return;
    }
    setCard(next.card);
  };

  const handleBackToDashboard = async () => {
    await refreshProgress();
    setPhase("dashboard");
    setCard(null);
  };

  return (
    <main className="min-h-screen" style={{ background: "var(--background)" }}>
      <nav className="sticky top-0 z-30 bg-white border-b-2" style={{ borderColor: "var(--duo-polar)" }}>
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "var(--duo-purple)" }}
            >
              <BookOpen className="w-[18px] h-[18px] text-white" />
            </div>
            <span className="text-base font-extrabold" style={{ color: "var(--duo-eel)" }}>
              {headerTitle}
            </span>
          </div>
          <div className="flex items-center gap-4">
            {phase === "studying" && (
              <button
                onClick={handleBackToDashboard}
                className="text-sm font-bold flex items-center gap-1"
                style={{ color: "var(--duo-blue)" }}
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
            )}
            <Link
              href="/trainer/classes"
              className="text-sm font-bold"
              style={{ color: "var(--duo-purple-push)" }}
            >
              My classes
            </Link>
            <Link
              href="/"
              className="text-sm font-bold"
              style={{ color: "var(--duo-wolf)" }}
            >
              Interview
            </Link>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {error && (
          <div
            className="max-w-2xl mx-auto mb-6 p-4 rounded-2xl text-sm font-semibold flex items-center justify-between"
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

        <AnimatePresence mode="wait">
          {phase === "dashboard" && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.3 }}
            >
              <TrainerDashboard
                progress={progress}
                onStart={handleStart}
                starting={loading}
                scopeLabel={isClassDeck ? "this class" : undefined}
              />
            </motion.div>
          )}

          {phase === "studying" && card && learnerId && (
            <motion.div
              key={`card-${card.id}`}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.3 }}
            >
              <TrainerCard card={card} learnerId={learnerId} onNext={handleNext} />
            </motion.div>
          )}

          {phase === "empty" && (
            <motion.div
              key="empty"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.3 }}
              className="max-w-xl mx-auto text-center py-20"
            >
              <div
                className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-5"
                style={{ background: "var(--duo-green)" }}
              >
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 6 9 17l-5-5" />
                </svg>
              </div>
              <h2 className="text-2xl font-extrabold mb-2" style={{ color: "var(--duo-eel)" }}>
                Deck complete for now
              </h2>
              <p className="text-base font-medium mb-6" style={{ color: "var(--duo-wolf)" }}>
                No cards available. Come back later or check the dashboard.
              </p>
              <button
                onClick={handleBackToDashboard}
                className="btn-3d btn-3d-blue px-8 py-3"
              >
                Back to dashboard
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}
