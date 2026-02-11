"use client";

import { useState } from "react";
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
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top nav bar */}
      <nav className="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4 h-12 flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-900 dark:text-white tracking-tight">
            AI Interview Coach
          </span>
          {phase !== "setup" && (
            <button
              onClick={handleRestart}
              className="text-xs text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              New Interview
            </button>
          )}
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {error && (
          <div className="max-w-2xl mx-auto mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {phase === "setup" && (
          <div className="phase-fade-in">
            <InterviewSetup onStart={handleStart} isLoading={isLoading} />
          </div>
        )}

        {phase === "interview" && session && (
          <div className="phase-fade-in">
            <InterviewSession
              session={session}
              onComplete={handleComplete}
            />
          </div>
        )}

        {phase === "generating_report" && (
          <div className="phase-fade-in flex flex-col items-center justify-center py-32">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Generating Your Feedback Report
            </h2>
            <p className="text-gray-500 mt-2">
              Analyzing your responses, tone, and body language...
            </p>
          </div>
        )}

        {phase === "report" && report && (
          <div className="phase-fade-in">
            <FeedbackReportView report={report} onRestart={handleRestart} />
          </div>
        )}
      </div>
    </main>
  );
}
