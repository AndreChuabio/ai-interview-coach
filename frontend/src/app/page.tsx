"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import InterviewSetup from "@/components/InterviewSetup";
import InterviewSession from "@/components/InterviewSession";
import FeedbackReportView from "@/components/FeedbackReport";
import OnboardingModal from "@/components/OnboardingModal";
import CareerPathView from "@/components/CareerPathView";
import {
  startInterview,
  generateFeedback,
  getProgress,
  getProfile,
  setProfile,
  getCareerPath,
  recordLessonComplete,
  getOrCreateUserId,
  type InterviewSetupRequest,
  type InterviewSession as SessionType,
  type FeedbackReport as ReportType,
  type UserProgress,
  type UserProfile,
  type CareerPathResponse,
} from "@/lib/api";

const HAS_PROFILE_KEY = "interview_coach_has_profile";

type AppPhase = "setup" | "interview" | "generating_report" | "report";
type ViewMode = "path" | "setup";

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
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [presetQuickPractice, setPresetQuickPractice] = useState<{
    topic: string;
    interviewType: "behavioral" | "technical" | "case_study";
  } | null>(null);
  const [celebration, setCelebration] = useState<{ type: "level"; value: number } | { type: "streak"; value: number } | null>(null);

  const [showOnboarding, setShowOnboarding] = useState(false);
  const [profile, setProfileState] = useState<UserProfile | null>(null);
  const [careerPath, setCareerPath] = useState<CareerPathResponse | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("path");
  const [pathLessonContext, setPathLessonContext] = useState<{
    profession: string;
    skill_id: string;
    lesson_id: string;
  } | null>(null);

  const userId = getOrCreateUserId();

  useEffect(() => {
    if (typeof window === "undefined" || !userId) return;
    const hasProfile = localStorage.getItem(HAS_PROFILE_KEY);
    setShowOnboarding(!hasProfile);
    if (hasProfile) {
      getProfile(userId)
        .then((p) => {
          setProfileState(p);
          return getCareerPath(p.profession, userId);
        })
        .then(setCareerPath)
        .catch(() => setCareerPath(null));
    }
  }, [userId]);

  useEffect(() => {
    if (userId) {
      getProgress(userId).then(setProgress);
    }
  }, [userId]);

  const handleStart = async (setup: InterviewSetupRequest) => {
    setIsLoading(true);
    setError(null);
    setPathLessonContext(null);
    try {
      const newSession = await startInterview(setup, userId);
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

  const handleStartPracticeFromPath = async (params: {
    role: string;
    profession: string;
    skill_id: string;
    lesson_id: string;
  }) => {
    setIsLoading(true);
    setError(null);
    setPathLessonContext({
      profession: params.profession,
      skill_id: params.skill_id,
      lesson_id: params.lesson_id,
    });
    try {
      const newSession = await startInterview(
        {
          interview_type: "behavioral",
          role: params.role,
          company: "",
          difficulty: "medium",
          num_questions: 2,
          practice_mode: "quick",
        },
        userId
      );
      setSession(newSession);
      setPhase("interview");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to start practice"
      );
      setPathLessonContext(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshPath = useCallback(() => {
    if (profile?.profession && userId) {
      getCareerPath(profile.profession, userId).then(setCareerPath);
    }
  }, [profile?.profession, userId]);

  const handleComplete = async (sessionId: string) => {
    setPhase("generating_report");
    try {
      const feedbackReport = await generateFeedback(sessionId, userId);
      if (pathLessonContext) {
        await recordLessonComplete(userId, pathLessonContext);
        setPathLessonContext(null);
        refreshPath();
      }
      setReport(feedbackReport);
      if (feedbackReport.total_xp != null && feedbackReport.level != null) {
        const prevLevel = progress?.level ?? 0;
        const prevStreak = progress?.streak_days ?? 0;
        setProgress({
          total_xp: feedbackReport.total_xp,
          level: feedbackReport.level,
          streak_days: feedbackReport.streak_days ?? 0,
          xp_today: feedbackReport.xp_today ?? 0,
          sessions_today: feedbackReport.sessions_today ?? progress?.sessions_today ?? 0,
        });
        if (feedbackReport.level > prevLevel) {
          setCelebration({ type: "level", value: feedbackReport.level });
        } else if (
          feedbackReport.streak_days != null &&
          feedbackReport.streak_days >= 7 &&
          feedbackReport.streak_days > prevStreak &&
          [7, 30].includes(feedbackReport.streak_days)
        ) {
          setCelebration({ type: "streak", value: feedbackReport.streak_days });
        }
      }
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
    setCelebration(null);
    setPathLessonContext(null);
    setPhase("setup");
  };

  const handleOnboardingDone = async (age: number, profession: string) => {
    await setProfile(userId, { age, profession });
    localStorage.setItem(HAS_PROFILE_KEY, "1");
    const p = await getProfile(userId);
    setProfileState(p);
    const path = await getCareerPath(p.profession, userId);
    setCareerPath(path);
    setShowOnboarding(false);
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
            {progress && (
              <div className="flex items-center gap-3 ml-4 text-sm font-bold" style={{ color: "var(--duo-wolf)" }}>
                <span style={{ color: "var(--duo-blue)" }}>Lv.{progress.level}</span>
                <span>{progress.total_xp} XP</span>
                {progress.streak_days > 0 && (
                  <span style={{ color: "var(--duo-orange)" }} title="Don't break your streak">
                    {progress.streak_days}d streak
                  </span>
                )}
                <span className="text-xs" style={{ color: "var(--duo-hare)" }} title="Daily goal: 50 XP">
                  {progress.xp_today}/50 XP today
                </span>
                <span className="text-xs" style={{ color: "var(--duo-hare)" }} title="5 free practices per day">
                  {Math.max(0, 5 - (progress.sessions_today ?? 0))}/5
                </span>
              </div>
            )}
          </div>
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
      </nav>

      {showOnboarding && (
        <OnboardingModal
          onDone={() => setShowOnboarding(false)}
          onSubmit={handleOnboardingDone}
        />
      )}

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
              {viewMode === "path" ? (
                careerPath ? (
                  <div>
                    <div className="flex items-center justify-between gap-4 mb-6">
                      <h1 className="text-xl font-extrabold" style={{ color: "var(--duo-eel)" }}>
                        Continue learning
                      </h1>
                      <button
                        type="button"
                        onClick={() => setViewMode("setup")}
                        className="text-sm font-bold px-4 py-2 rounded-xl transition-opacity hover:opacity-90"
                        style={{ background: "var(--duo-blue)", color: "white" }}
                      >
                        Practice full interview
                      </button>
                    </div>
                    <CareerPathView
                      path={careerPath}
                      onPracticeLesson={handleStartPracticeFromPath}
                    />
                  </div>
                ) : (
                  <p className="text-center py-12 font-semibold" style={{ color: "var(--duo-wolf)" }}>
                    Loading your path...
                  </p>
                )
              ) : (
                <div>
                  <div className="mb-4">
                    <button
                      type="button"
                      onClick={() => setViewMode("path")}
                      className="text-sm font-bold px-3 py-1.5 rounded-lg transition-colors"
                      style={{ color: "var(--duo-blue)" }}
                    >
                      Back to path
                    </button>
                  </div>
                  <InterviewSetup
                    onStart={handleStart}
                    isLoading={isLoading}
                    presetQuickPractice={presetQuickPractice}
                    onPresetApplied={() => setPresetQuickPractice(null)}
                  />
                </div>
              )}
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
              <FeedbackReportView
                report={report}
                onRestart={handleRestart}
                onPracticeTopic={(topic, interviewType) => {
                  setPresetQuickPractice({
                    topic,
                    interviewType: interviewType as "behavioral" | "technical" | "case_study",
                  });
                  setPhase("setup");
                }}
              />
              {celebration && (
                <CelebrationModal
                  celebration={celebration}
                  onClose={() => setCelebration(null)}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </main>
  );
}

/* ------------------------------------------------------------------ */
/* Celebration modal (level-up, streak milestone)                     */
/* ------------------------------------------------------------------ */
function CelebrationModal({
  celebration,
  onClose,
}: {
  celebration: { type: "level"; value: number } | { type: "streak"; value: number };
  onClose: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.5)" }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        onClick={(e) => e.stopPropagation()}
        className="rounded-3xl p-8 text-center max-w-sm w-full"
        style={{
          background: "white",
          border: "3px solid var(--duo-green)",
          boxShadow: "0 20px 40px rgba(0,0,0,0.2)",
        }}
      >
        {celebration.type === "level" ? (
          <>
            <h3 className="text-2xl font-extrabold mb-2" style={{ color: "var(--duo-green-push)" }}>
              Level Up
            </h3>
            <p className="text-4xl font-extrabold mb-4" style={{ color: "var(--duo-green)" }}>
              Level {celebration.value}
            </p>
          </>
        ) : (
          <>
            <h3 className="text-2xl font-extrabold mb-2" style={{ color: "var(--duo-orange)" }}>
              {celebration.value}-Day Streak
            </h3>
            <p className="text-base font-semibold mb-4" style={{ color: "var(--duo-wolf)" }}>
              Don't break your streak
            </p>
          </>
        )}
        <button
          type="button"
          onClick={onClose}
          className="btn-3d btn-3d-green px-6 py-2.5 rounded-xl font-bold"
        >
          Continue
        </button>
      </motion.div>
    </motion.div>
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
