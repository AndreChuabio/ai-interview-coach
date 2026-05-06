"use client";

import { motion } from "framer-motion";
import { Flame, Target, CheckCircle2, TrendingUp, Sparkles, BookOpen } from "lucide-react";
import type { ProgressSummary } from "@/lib/api";

interface Props {
  progress: ProgressSummary | null;
  onStart: () => void;
  starting: boolean;
  /** When set (e.g. "this class"), the hero copy narrows to that deck. */
  scopeLabel?: string;
}

export default function TrainerDashboard({ progress, onStart, starting, scopeLabel }: Props) {
  const accuracyPct = progress ? Math.round(progress.accuracy * 100) : 0;
  const masteredPct = progress && progress.total_cards > 0
    ? Math.round((progress.mastered / progress.total_cards) * 100)
    : 0;
  const title = scopeLabel ? "Class Trainer" : "ML Trainer";
  const subtitle = scopeLabel
    ? `Short-answer flashcards generated from ${scopeLabel}. Your answers are graded and tracked.`
    : "Short-answer flashcards on ML fundamentals. Your answers are graded and tracked so weak topics come back.";

  return (
    <div className="max-w-2xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 20 }}
          className="inline-flex items-center justify-center w-20 h-20 rounded-2xl mb-5"
          style={{ background: "var(--duo-purple)" }}
        >
          <BookOpen className="w-10 h-10 text-white" />
        </motion.div>
        <h1 className="text-4xl font-extrabold mb-2" style={{ color: "var(--duo-eel)" }}>
          {title}
        </h1>
        <p className="text-lg font-medium max-w-md mx-auto" style={{ color: "var(--duo-wolf)" }}>
          {subtitle}
        </p>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
        <StatTile
          icon={Flame}
          label="Day Streak"
          value={progress?.streak_days ?? 0}
          color="var(--duo-orange)"
          bg="var(--duo-orange-light)"
          pushColor="var(--duo-orange-push)"
        />
        <StatTile
          icon={Target}
          label="Accuracy"
          value={`${accuracyPct}%`}
          color="var(--duo-blue)"
          bg="var(--duo-blue-light)"
          pushColor="var(--duo-blue-push)"
        />
        <StatTile
          icon={CheckCircle2}
          label="Mastered"
          value={`${progress?.mastered ?? 0}/${progress?.total_cards ?? 0}`}
          color="var(--duo-green)"
          bg="var(--duo-green-light)"
          pushColor="var(--duo-green-push)"
        />
        <StatTile
          icon={TrendingUp}
          label="Reviews"
          value={progress?.total_reviews ?? 0}
          color="var(--duo-purple)"
          bg="var(--duo-purple-light)"
          pushColor="var(--duo-purple-push)"
        />
      </div>

      {/* Card mix bar */}
      {progress && progress.total_cards > 0 && (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--duo-wolf)" }}>
              Your deck ({progress.total_cards} cards)
            </span>
            <span className="text-xs font-bold" style={{ color: "var(--duo-green-push)" }}>
              {masteredPct}% mastered
            </span>
          </div>
          <div
            className="h-4 rounded-full overflow-hidden flex"
            style={{ background: "var(--duo-polar)" }}
          >
            <Segment count={progress.mastered} total={progress.total_cards} color="var(--duo-green)" />
            <Segment count={progress.learning} total={progress.total_cards} color="var(--duo-blue)" />
            <Segment count={progress.struggling} total={progress.total_cards} color="var(--duo-red)" />
            <Segment count={progress.new} total={progress.total_cards} color="var(--duo-polar)" />
          </div>
          <div className="flex flex-wrap gap-3 mt-2 text-xs font-semibold" style={{ color: "var(--duo-wolf)" }}>
            <LegendDot color="var(--duo-green)" label={`${progress.mastered} mastered`} />
            <LegendDot color="var(--duo-blue)" label={`${progress.learning} learning`} />
            <LegendDot color="var(--duo-red)" label={`${progress.struggling} struggling`} />
            <LegendDot color="var(--duo-hare)" label={`${progress.new} new`} />
          </div>
        </div>
      )}

      {/* Start button */}
      <motion.button
        onClick={onStart}
        disabled={starting}
        whileTap={{ scale: 0.98 }}
        whileHover={{ scale: 1.01 }}
        className="btn-3d btn-3d-green w-full py-4 text-lg flex items-center justify-center gap-2"
      >
        <Sparkles className="w-5 h-5" />
        {starting ? "Loading..." : progress && progress.total_reviews > 0 ? "Continue studying" : "Start studying"}
      </motion.button>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  color,
  bg,
  pushColor,
}: {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  value: string | number;
  color: string;
  bg: string;
  pushColor: string;
}) {
  return (
    <div className="flex flex-col items-center text-center p-4 rounded-2xl" style={{ background: bg }}>
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center mb-2"
        style={{ background: color }}
      >
        <Icon className="w-5 h-5" style={{ color: "white" }} />
      </div>
      <div className="text-2xl font-extrabold" style={{ color: pushColor }}>
        {value}
      </div>
      <div className="text-[10px] font-bold uppercase tracking-wide mt-0.5" style={{ color: "var(--duo-wolf)" }}>
        {label}
      </div>
    </div>
  );
}

function Segment({ count, total, color }: { count: number; total: number; color: string }) {
  if (count <= 0) return null;
  const pct = (count / total) * 100;
  return <div style={{ width: `${pct}%`, background: color }} />;
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}
