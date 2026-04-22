"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { BookOpen } from "lucide-react";
import InterviewSetup from "@/components/InterviewSetup";
import InterviewSession from "@/components/InterviewSession";
import FeedbackReportView from "@/components/FeedbackReport";
import {
  startInterview,
  generateFeedback,
  type InterviewSetupRequest,
  type InterviewSession as SessionType,
  type FeedbackReport as ReportType,
} from "@/lib/api";

type AppPhase = "setup" | "interview" | "generating_report" | "report";

const GENERATING_MESSAGES = [
  "Crunching your performance data...",
  "Analyzing tone and body language...",
  "Building your personalized report...",
  "Almost there...",
];

export default function Home() {
  const [phase, setPhase] = useState<AppPhase>("setup");
  const [session, setSession] = useState<SessionType | null>(null);
  const [report, setReport] = useState<ReportType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async (setup: InterviewSetupRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const newSession = await startInterview(setup);
      setSession(newSession);
      setPhase("interview");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start interview"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async (sessionId: string) => {
    setPhase("generating_report");
    try {
      const feedbackReport = await generateFeedback(sessionId);
      setReport(feedbackReport);
      setPhase("report");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate feedback report"
      );
      setPhase("setup");
    }
  };

  const handleRestart = () => {
    setSession(null);
    setReport(null);
    setError(null);
    setPhase("setup");
  };

  return (
    <main className="min-h-screen" style={{ background: "var(--background)" }}>
      {/* Navbar */}
      <nav className="sticky top-0 z-30 bg-white border-b-2" style={{ borderColor: "var(--duo-polar)" }}>
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "var(--duo-green)" }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" x2="12" y1="19" y2="22" />
              </svg>
            </div>
            <span className="text-base font-extrabold" style={{ color: "var(--duo-eel)" }}>
              AI Interview Coach
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/trainer"
              className="text-sm font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-colors"
              style={{ color: "var(--duo-purple-push)", background: "var(--duo-purple-light)" }}
            >
              <BookOpen className="w-4 h-4" />
              Trainer
            </Link>
            {phase !== "setup" && (
              <button
                onClick={handleRestart}
                className="text-sm font-bold px-4 py-1.5 rounded-xl transition-colors"
                style={{ color: "var(--duo-blue)" }}
              >
                New Interview
              </button>
            )}
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {error && (
          <div
            className="max-w-2xl mx-auto mb-6 p-4 rounded-2xl text-sm font-semibold flex items-center justify-between"
            style={{ background: "var(--duo-red-light)", color: "var(--duo-red)", border: "2px solid var(--duo-red)" }}
          >
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-3 font-bold underline"
            >
              Dismiss
            </button>
          </div>
        )}

        <AnimatePresence mode="wait">
          {phase === "setup" && (
            <motion.div
              key="setup"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <InterviewSetup onStart={handleStart} isLoading={isLoading} />
            </motion.div>
          )}

          {phase === "interview" && session && (
            <motion.div
              key="interview"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <InterviewSession
                session={session}
                onComplete={handleComplete}
              />
            </motion.div>
          )}

          {phase === "generating_report" && (
            <motion.div
              key="generating"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <GeneratingReportView />
            </motion.div>
          )}

          {phase === "report" && report && (
            <motion.div
              key="report"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
            >
              <FeedbackReportView report={report} onRestart={handleRestart} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

/* ------------------------------------------------------------------ */
/* Generating Report -- bouncy dots + cycling messages                  */
/* ------------------------------------------------------------------ */
function GeneratingReportView() {
  const [msgIdx, setMsgIdx] = useState(0);

  useState(() => {
    const interval = setInterval(() => {
      setMsgIdx((prev) => (prev + 1) % GENERATING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  });

  return (
    <div className="flex flex-col items-center justify-center py-32 gap-6">
      {/* Bouncing dots */}
      <div className="flex gap-2">
        <span className="bounce-dot" style={{ background: "var(--duo-green)" }} />
        <span className="bounce-dot" style={{ background: "var(--duo-blue)" }} />
        <span className="bounce-dot" style={{ background: "var(--duo-orange)" }} />
      </div>

      <h2 className="text-2xl font-extrabold" style={{ color: "var(--duo-eel)" }}>
        Generating Your Report
      </h2>
      <p className="text-base font-semibold" style={{ color: "var(--duo-wolf)" }}>
        {GENERATING_MESSAGES[msgIdx]}
      </p>
    </div>
  );
}
