"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts";
import {
  Target,
  MessageSquare,
  Eye,
  CheckCircle2,
  ArrowUp,
  ArrowRight,
  Trophy,
  Star,
  Zap,
} from "lucide-react";
import type { FeedbackReport as ReportType } from "@/lib/api";

interface Props {
  report: ReportType;
  onRestart: () => void;
  onPracticeTopic?: (topic: string, interviewType: string) => void;
}

const COLORS = [
  "#1CB0F6",
  "#58CC02",
  "#FF9600",
  "#FF4B4B",
  "#CE82FF",
  "#ec4899",
  "#06b6d4",
];

/* ------------------------------------------------------------------ */
/*  Confetti burst on mount                                             */
/* ------------------------------------------------------------------ */
function Confetti() {
  const [pieces, setPieces] = useState<
    Array<{ id: number; left: string; color: string; delay: string; size: number }>
  >([]);

  useEffect(() => {
    const colors = ["#58CC02", "#1CB0F6", "#FF9600", "#FF4B4B", "#CE82FF", "#FFC800"];
    const generated = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      color: colors[Math.floor(Math.random() * colors.length)],
      delay: `${Math.random() * 1.5}s`,
      size: 6 + Math.random() * 8,
    }));
    setPieces(generated);
  }, []);

  return (
    <>
      {pieces.map((p) => (
        <div
          key={p.id}
          className="confetti-piece"
          style={{
            left: p.left,
            background: p.color,
            animationDelay: p.delay,
            width: `${p.size}px`,
            height: `${p.size}px`,
            borderRadius: Math.random() > 0.5 ? "50%" : "2px",
          }}
        />
      ))}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Animated score counter                                              */
/* ------------------------------------------------------------------ */
function AnimatedScore({
  target,
  size = "text-4xl",
  color,
}: {
  target: number;
  size?: string;
  color: string;
}) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    let frame: number;
    const duration = 1200;
    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(eased * target);
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    }

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target]);

  return (
    <span className={`${size} font-extrabold tabular-nums`} style={{ color }}>
      {current.toFixed(1)}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Score Ring (Duolingo-themed)                                        */
/* ------------------------------------------------------------------ */
function ScoreRing({
  score,
  label,
  size = 80,
}: {
  score: number;
  label: string;
  size?: number;
}) {
  const pct = (score / 10) * 100;
  const circumference = 2 * Math.PI * 35;
  const offset = circumference - (pct / 100) * circumference;
  const color =
    score >= 7 ? "var(--duo-green)" : score >= 5 ? "var(--duo-orange)" : "var(--duo-red)";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r="35"
          stroke="var(--duo-polar)"
          strokeWidth="6"
          fill="none"
        />
        <circle
          cx="40"
          cy="40"
          r="35"
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 40 40)"
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
        <text
          x="40"
          y="44"
          textAnchor="middle"
          className="font-extrabold"
          style={{ fill: "var(--duo-eel)" }}
          fontSize="18"
        >
          {score.toFixed(1)}
        </text>
      </svg>
      <span className="text-xs font-bold mt-1" style={{ color: "var(--duo-wolf)" }}>
        {label}
      </span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Feedback Report                                                */
/* ------------------------------------------------------------------ */
export default function FeedbackReport({ report, onRestart, onPracticeTopic }: Props) {
  const radarData = [
    { metric: "Content", value: report.content.overall_score },
    { metric: "Relevance", value: report.content.relevance },
    { metric: "Structure", value: report.content.structure },
    { metric: "Pace", value: report.communication.pace_score },
    { metric: "Clarity", value: report.communication.clarity_score },
    { metric: "Eye Contact", value: report.body_language.eye_contact_pct / 10 },
  ];

  const commData = [
    { name: "Pace", score: report.communication.pace_score },
    { name: "Clarity", score: report.communication.clarity_score },
    { name: "Fillers", score: report.communication.filler_score },
    { name: "Confidence", score: report.communication.confidence_score },
  ];

  const emotionData = Object.entries(
    report.body_language.emotion_distribution
  ).map(([name, value]) => ({ name, value }));

  // Use raw hex values (not CSS variables) so alpha suffixes can be
  // appended directly in inline style template literals.
  const overallColor =
    report.overall_score >= 7
      ? "#58CC02"
      : report.overall_score >= 5
        ? "#FF9600"
        : "#FF4B4B";

  const headline =
    report.overall_score >= 8
      ? "Outstanding Performance"
      : report.overall_score >= 6
        ? "Great Job"
        : report.overall_score >= 4
          ? "Good Effort"
          : "Keep Practicing";

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      <Confetti />

      {/* Header with celebration */}
      <motion.div
        className="text-center celebrate-pop"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 15 }}
      >
        <div
          className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-3"
          style={{ background: overallColor }}
        >
          <Trophy className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
          {headline}
        </h1>
        <p className="text-base font-semibold" style={{ color: "var(--duo-wolf)" }}>
          {report.interview_type.replace("_", " ")} interview for{" "}
          {report.role}
          {report.company ? ` at ${report.company}` : ""}
        </p>
        {report.xp_earned != null && report.level != null && (
          <p className="text-sm font-bold mt-2" style={{ color: "var(--duo-green-push)" }}>
            +{report.xp_earned} XP. Level {report.level}.
            {report.streak_days != null && report.streak_days > 0 && (
              <span className="ml-2" style={{ color: "var(--duo-orange)" }}>
                {report.streak_days}-day streak
              </span>
            )}
          </p>
        )}
      </motion.div>

      {/* Overall Score Trophy Card */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="rounded-3xl p-8"
        style={{
          background: "white",
          border: "2px solid var(--duo-polar)",
        }}
      >
        <div className="flex items-center justify-center gap-12">
          {/* Big overall score */}
          <div className="flex flex-col items-center">
            <div
              className="w-32 h-32 rounded-full flex flex-col items-center justify-center"
              style={{
                background: `linear-gradient(135deg, ${overallColor}, ${overallColor}dd)`,
                boxShadow: `0 8px 24px ${overallColor}40`,
              }}
            >
              <AnimatedScore target={report.overall_score} size="text-4xl" color="white" />
              <span className="text-xs font-bold text-white/80 mt-0.5">/ 10</span>
            </div>
            <div className="flex items-center gap-1 mt-3">
              <Star className="w-4 h-4" style={{ color: overallColor }} />
              <span className="text-sm font-extrabold" style={{ color: "var(--duo-eel)" }}>
                Overall Score
              </span>
            </div>
          </div>

          {/* Sub-scores */}
          <div className="flex gap-8">
            <ScoreRing
              score={report.content.overall_score}
              label="Content"
            />
            <ScoreRing
              score={report.communication.overall_score}
              label="Communication"
            />
            <ScoreRing
              score={report.body_language.overall_score}
              label="Body Language"
            />
          </div>
        </div>
      </motion.div>

      {/* Radar Overview */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.35, duration: 0.5 }}
        className="rounded-3xl p-6"
        style={{ background: "white", border: "2px solid var(--duo-polar)" }}
      >
        <h2 className="text-lg font-extrabold mb-4" style={{ color: "var(--duo-eel)" }}>
          Performance Overview
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="var(--duo-polar)" />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fontSize: 12, fill: "var(--duo-wolf)", fontWeight: 600 }}
            />
            <PolarRadiusAxis domain={[0, 10]} tick={{ fontSize: 10 }} />
            <Radar
              dataKey="value"
              stroke="#58CC02"
              fill="#58CC02"
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Content Analysis */}
      <Section
        icon={<Target className="w-5 h-5" style={{ color: "var(--duo-blue)" }} />}
        title="Content Analysis"
        delay={0.45}
      >
        <div className="grid grid-cols-3 gap-4 mb-6">
          <MiniScore label="Relevance" score={report.content.relevance} />
          <MiniScore label="Specificity" score={report.content.specificity} />
          <MiniScore label="Structure" score={report.content.structure} />
        </div>
        <FeedbackList
          strengths={report.content.strengths}
          improvements={report.content.improvements}
        />
        {report.content.example_responses.length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-bold mb-2" style={{ color: "var(--duo-eel)" }}>
              Example Better Responses
            </h4>
            {report.content.example_responses.map((ex, i) => (
              <div
                key={i}
                className="rounded-2xl p-3 mb-2 text-sm font-medium"
                style={{
                  background: "var(--duo-blue-light)",
                  color: "var(--duo-blue-push)",
                  border: "1px solid var(--duo-blue)",
                }}
              >
                {ex}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Communication Analysis */}
      <Section
        icon={<MessageSquare className="w-5 h-5" style={{ color: "var(--duo-green)" }} />}
        title="Communication Analysis"
        delay={0.55}
      >
        <div className="flex gap-4 mb-6">
          <span
            className="text-sm font-bold px-3 py-1 rounded-full"
            style={{ background: "var(--duo-blue-light)", color: "var(--duo-blue-push)" }}
          >
            Avg pace: {report.communication.avg_wpm.toFixed(0)} WPM
          </span>
          <span
            className="text-sm font-bold px-3 py-1 rounded-full"
            style={{ background: "var(--duo-orange-light)", color: "var(--duo-orange-push)" }}
          >
            Total fillers: {report.communication.total_fillers}
          </span>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={commData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--duo-polar)" />
            <XAxis dataKey="name" tick={{ fontSize: 12, fontWeight: 600 }} />
            <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="score" fill="#58CC02" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <FeedbackList
          strengths={report.communication.strengths}
          improvements={report.communication.improvements}
        />
      </Section>

      {/* Body Language Analysis */}
      <Section
        icon={<Eye className="w-5 h-5" style={{ color: "var(--duo-purple)" }} />}
        title="Body Language Analysis"
        delay={0.65}
      >
        <div className="flex gap-8 mb-6">
          <div className="text-center">
            <div className="text-3xl font-extrabold" style={{ color: "var(--duo-eel)" }}>
              {report.body_language.eye_contact_pct.toFixed(0)}%
            </div>
            <div className="text-xs font-bold" style={{ color: "var(--duo-wolf)" }}>Eye Contact</div>
          </div>
          <div className="flex-1">
            {emotionData.length > 0 && (
              <ResponsiveContainer width="100%" height={150}>
                <PieChart>
                  <Pie
                    data={emotionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={60}
                    dataKey="value"
                    label={({ name, value }) =>
                      `${name} ${value.toFixed(0)}%`
                    }
                  >
                    {emotionData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={COLORS[i % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
        <FeedbackList
          strengths={report.body_language.strengths}
          improvements={report.body_language.improvements}
        />
      </Section>

      {/* Action Items -- Quest List */}
      <motion.div
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.75, duration: 0.5 }}
        className="rounded-3xl p-6"
        style={{ background: "white", border: "2px solid var(--duo-polar)" }}
      >
        <h2 className="text-lg font-extrabold mb-4 flex items-center gap-2" style={{ color: "var(--duo-eel)" }}>
          <Zap className="w-5 h-5" style={{ color: "var(--duo-orange)" }} />
          Your Quest List
        </h2>
        <ol className="space-y-3">
          {report.action_items.map((item, i) => (
            <motion.li
              key={i}
              initial={{ x: -12, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.8 + i * 0.1 }}
              className="flex gap-3 text-sm"
            >
              <span
                className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-extrabold"
                style={{
                  background: "var(--duo-orange)",
                  color: "white",
                }}
              >
                {i + 1}
              </span>
              <span
                className="font-medium pt-0.5 flex-1 rounded-xl px-3 py-2"
                style={{
                  background: "var(--duo-orange-light)",
                  color: "var(--duo-eel)",
                  borderLeft: "3px solid var(--duo-orange)",
                }}
              >
                {item}
              </span>
            </motion.li>
          ))}
        </ol>
      </motion.div>

      {/* Practice weak skill (recommended) + Practice Again */}
      <div className="text-center flex flex-col sm:flex-row items-center justify-center gap-4">
        {report.recommended_topic && report.recommended_interview_type && onPracticeTopic && (
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => onPracticeTopic(report.recommended_topic!, report.recommended_interview_type!)}
            className="px-8 py-3 text-base font-bold rounded-2xl transition-colors"
            style={{
              background: "var(--duo-orange-light)",
              color: "var(--duo-orange-push)",
              border: "2px solid var(--duo-orange)",
            }}
          >
            Practice {report.recommended_topic} (quick)
          </motion.button>
        )}
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={onRestart}
          className="btn-3d btn-3d-green px-10 py-4 text-lg rounded-2xl"
        >
          <ArrowRight className="w-5 h-5" />
          Practice Again
        </motion.button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Section wrapper                                                     */
/* ------------------------------------------------------------------ */
function Section({
  icon,
  title,
  delay = 0,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  delay?: number;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay, duration: 0.5 }}
      className="rounded-3xl p-6"
      style={{ background: "white", border: "2px solid var(--duo-polar)" }}
    >
      <h2 className="text-lg font-extrabold mb-4 flex items-center gap-2" style={{ color: "var(--duo-eel)" }}>
        {icon}
        {title}
      </h2>
      {children}
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Mini Score Badge                                                    */
/* ------------------------------------------------------------------ */
function MiniScore({ label, score }: { label: string; score: number }) {
  const color =
    score >= 7
      ? "var(--duo-green)"
      : score >= 5
        ? "var(--duo-orange)"
        : "var(--duo-red)";
  const bg =
    score >= 7
      ? "var(--duo-green-light)"
      : score >= 5
        ? "var(--duo-orange-light)"
        : "var(--duo-red-light)";

  return (
    <div
      className="text-center p-4 rounded-2xl"
      style={{ background: bg }}
    >
      <div className="text-2xl font-extrabold" style={{ color }}>{score.toFixed(1)}</div>
      <div className="text-xs font-bold" style={{ color: "var(--duo-wolf)" }}>{label}</div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Feedback List (achievements + skills to level up)                   */
/* ------------------------------------------------------------------ */
function FeedbackList({
  strengths,
  improvements,
}: {
  strengths: string[];
  improvements: string[];
}) {
  return (
    <div className="grid grid-cols-2 gap-4 mt-4">
      <div>
        <h4 className="text-sm font-bold mb-2 flex items-center gap-1.5" style={{ color: "var(--duo-green-push)" }}>
          <CheckCircle2 className="w-4 h-4" style={{ color: "var(--duo-green)" }} />
          Achievements Unlocked
        </h4>
        <ul className="space-y-2">
          {strengths.map((s, i) => (
            <li
              key={i}
              className="text-sm font-medium p-2 rounded-xl"
              style={{
                background: "var(--duo-green-light)",
                color: "var(--duo-eel)",
                borderLeft: "3px solid var(--duo-green)",
              }}
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="text-sm font-bold mb-2 flex items-center gap-1.5" style={{ color: "var(--duo-orange-push)" }}>
          <ArrowUp className="w-4 h-4" style={{ color: "var(--duo-orange)" }} />
          Skills to Level Up
        </h4>
        <ul className="space-y-2">
          {improvements.map((s, i) => (
            <li
              key={i}
              className="text-sm font-medium p-2 rounded-xl"
              style={{
                background: "var(--duo-orange-light)",
                color: "var(--duo-eel)",
                borderLeft: "3px solid var(--duo-orange)",
              }}
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
