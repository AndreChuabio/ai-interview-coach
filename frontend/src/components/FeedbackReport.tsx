"use client";

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
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import type { FeedbackReport as ReportType } from "@/lib/api";

interface Props {
  report: ReportType;
  onRestart: () => void;
}

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
];

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
    score >= 7 ? "#10b981" : score >= 5 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r="35"
          stroke="#e5e7eb"
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
        />
        <text
          x="40"
          y="44"
          textAnchor="middle"
          className="fill-gray-900 dark:fill-white font-bold"
          fontSize="18"
        >
          {score.toFixed(1)}
        </text>
      </svg>
      <span className="text-xs text-gray-500 mt-1">{label}</span>
    </div>
  );
}

export default function FeedbackReport({ report, onRestart }: Props) {
  // Radar chart data
  const radarData = [
    { metric: "Content", value: report.content.overall_score },
    { metric: "Relevance", value: report.content.relevance },
    { metric: "Structure", value: report.content.structure },
    { metric: "Pace", value: report.communication.pace_score },
    { metric: "Clarity", value: report.communication.clarity_score },
    { metric: "Eye Contact", value: report.body_language.eye_contact_pct / 10 },
  ];

  // Communication bar chart
  const commData = [
    { name: "Pace", score: report.communication.pace_score },
    { name: "Clarity", score: report.communication.clarity_score },
    { name: "Fillers", score: report.communication.filler_score },
    { name: "Confidence", score: report.communication.confidence_score },
  ];

  // Emotion pie chart
  const emotionData = Object.entries(
    report.body_language.emotion_distribution
  ).map(([name, value]) => ({ name, value }));

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Interview Feedback Report
        </h1>
        <p className="text-gray-500">
          {report.interview_type.replace("_", " ")} interview for{" "}
          {report.role}
          {report.company ? ` at ${report.company}` : ""}
        </p>
      </div>

      {/* Overall Score */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-center gap-12">
          <ScoreRing score={report.overall_score} label="Overall" size={120} />
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
      </div>

      {/* Radar Overview */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Performance Overview
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis
              dataKey="metric"
              tick={{ fontSize: 12, fill: "#9ca3af" }}
            />
            <PolarRadiusAxis domain={[0, 10]} tick={{ fontSize: 10 }} />
            <Radar
              dataKey="value"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Content Analysis */}
      <Section
        icon={<Target className="w-5 h-5 text-blue-500" />}
        title="Content Analysis"
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
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Example Better Responses
            </h4>
            {report.content.example_responses.map((ex, i) => (
              <div
                key={i}
                className="bg-blue-50 dark:bg-blue-950 rounded-lg p-3 mb-2 text-sm text-gray-700 dark:text-gray-300"
              >
                {ex}
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Communication Analysis */}
      <Section
        icon={<MessageSquare className="w-5 h-5 text-green-500" />}
        title="Communication Analysis"
      >
        <div className="flex gap-4 mb-6 text-sm text-gray-600 dark:text-gray-400">
          <span>Avg pace: {report.communication.avg_wpm.toFixed(0)} WPM</span>
          <span>Total fillers: {report.communication.total_fillers}</span>
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={commData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="score" fill="#10b981" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <FeedbackList
          strengths={report.communication.strengths}
          improvements={report.communication.improvements}
        />
      </Section>

      {/* Body Language Analysis */}
      <Section
        icon={<Eye className="w-5 h-5 text-purple-500" />}
        title="Body Language Analysis"
      >
        <div className="flex gap-8 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {report.body_language.eye_contact_pct.toFixed(0)}%
            </div>
            <div className="text-xs text-gray-500">Eye Contact</div>
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

      {/* Action Items */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
          <ArrowRight className="w-5 h-5 text-orange-500" />
          Action Items
        </h2>
        <ol className="space-y-3">
          {report.action_items.map((item, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="flex-shrink-0 w-6 h-6 rounded-full bg-orange-100 dark:bg-orange-900 text-orange-600 dark:text-orange-300 flex items-center justify-center text-xs font-bold">
                {i + 1}
              </span>
              <span className="text-gray-700 dark:text-gray-300">{item}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* Restart */}
      <div className="text-center">
        <button
          onClick={onRestart}
          className="px-8 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition-colors"
        >
          Start New Interview
        </button>
      </div>
    </div>
  );
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white flex items-center gap-2">
        {icon}
        {title}
      </h2>
      {children}
    </div>
  );
}

function MiniScore({ label, score }: { label: string; score: number }) {
  const color =
    score >= 7
      ? "text-green-600"
      : score >= 5
        ? "text-yellow-600"
        : "text-red-600";
  return (
    <div className="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-750">
      <div className={`text-xl font-bold ${color}`}>{score.toFixed(1)}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

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
        <h4 className="text-sm font-medium text-green-700 dark:text-green-400 mb-2 flex items-center gap-1">
          <CheckCircle2 className="w-4 h-4" /> Strengths
        </h4>
        <ul className="space-y-1">
          {strengths.map((s, i) => (
            <li
              key={i}
              className="text-sm text-gray-600 dark:text-gray-400 pl-3 border-l-2 border-green-300"
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h4 className="text-sm font-medium text-amber-700 dark:text-amber-400 mb-2 flex items-center gap-1">
          <AlertTriangle className="w-4 h-4" /> Improvements
        </h4>
        <ul className="space-y-1">
          {improvements.map((s, i) => (
            <li
              key={i}
              className="text-sm text-gray-600 dark:text-gray-400 pl-3 border-l-2 border-amber-300"
            >
              {s}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
