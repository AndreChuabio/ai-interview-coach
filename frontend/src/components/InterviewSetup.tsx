"use client";

import { useState, useRef, useEffect } from "react";
import {
  Mic,
  Briefcase,
  GraduationCap,
  TrendingUp,
  Eye,
  AudioLines,
  Database,
  ChevronDown,
} from "lucide-react";
import type { InterviewSetupRequest } from "@/lib/api";

interface Props {
  onStart: (setup: InterviewSetupRequest) => void;
  isLoading: boolean;
}

const INTERVIEW_TYPES = [
  {
    id: "behavioral" as const,
    label: "Behavioral",
    description: "Leadership, teamwork, conflict resolution",
    icon: Briefcase,
  },
  {
    id: "technical" as const,
    label: "Technical",
    description: "Data science, coding, system design",
    icon: GraduationCap,
  },
  {
    id: "case_study" as const,
    label: "Case Study",
    description: "Market sizing, profitability, strategy",
    icon: TrendingUp,
  },
];

const DIFFICULTIES = [
  { id: "easy" as const, label: "Easy", color: "bg-green-500" },
  { id: "medium" as const, label: "Medium", color: "bg-yellow-500" },
  { id: "hard" as const, label: "Hard", color: "bg-red-500" },
];

const FEATURES = [
  { icon: Mic, label: "Voice AI", description: "Natural conversation" },
  { icon: Eye, label: "Face Tracking", description: "Expression analysis" },
  { icon: AudioLines, label: "Tone Analysis", description: "Pace and fillers" },
  { icon: Database, label: "Knowledge Graph", description: "Company context" },
];

/** Companies seeded in the Neo4j knowledge graph. */
const SEEDED_COMPANIES = [
  "Google",
  "Amazon",
  "Meta",
  "Apple",
  "Microsoft",
  "Netflix",
  "Goldman Sachs",
  "JPMorgan Chase",
  "McKinsey",
  "Deloitte",
  "Tesla",
  "Stripe",
  "OpenAI",
  "Palantir",
  "Two Sigma",
];

export default function InterviewSetup({ onStart, isLoading }: Props) {
  const [interviewType, setInterviewType] =
    useState<InterviewSetupRequest["interview_type"]>("behavioral");
  const [role, setRole] = useState("Software Engineer");
  const [company, setCompany] = useState("");
  const [difficulty, setDifficulty] =
    useState<InterviewSetupRequest["difficulty"]>("medium");
  const [numQuestions, setNumQuestions] = useState(5);

  const [companyOpen, setCompanyOpen] = useState(false);
  const companyRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (companyRef.current && !companyRef.current.contains(e.target as Node)) {
        setCompanyOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filteredCompanies = company.trim()
    ? SEEDED_COMPANIES.filter((c) =>
        c.toLowerCase().includes(company.toLowerCase())
      )
    : SEEDED_COMPANIES;

  const isSeededCompany = SEEDED_COMPANIES.some(
    (c) => c.toLowerCase() === company.toLowerCase()
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onStart({
      interview_type: interviewType,
      role,
      company,
      difficulty,
      num_questions: numQuestions,
    });
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Hero */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 mb-4 shadow-lg shadow-blue-500/25">
          <Mic className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          AI Interview Coach
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Practice interviews with an AI that analyzes your responses, tone, and
          facial expressions in real time.
        </p>
      </div>

      {/* Feature highlights */}
      <div className="grid grid-cols-4 gap-3 mb-10">
        {FEATURES.map((f) => {
          const Icon = f.icon;
          return (
            <div
              key={f.label}
              className="flex flex-col items-center text-center p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"
            >
              <Icon className="w-5 h-5 text-blue-500 mb-1.5" />
              <span className="text-xs font-semibold text-gray-800 dark:text-gray-200">
                {f.label}
              </span>
              <span className="text-[10px] text-gray-400">{f.description}</span>
            </div>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Interview Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Interview Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {INTERVIEW_TYPES.map((type) => {
              const Icon = type.icon;
              const selected = interviewType === type.id;
              return (
                <button
                  key={type.id}
                  type="button"
                  onClick={() => setInterviewType(type.id)}
                  className={`p-4 rounded-xl border-2 text-left transition-all duration-200 ${
                    selected
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950 shadow-md shadow-blue-500/10 scale-[1.02]"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300 hover:shadow-sm hover:scale-[1.01]"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 mb-2 ${
                      selected ? "text-blue-600" : "text-gray-400"
                    }`}
                  />
                  <div className="font-medium text-sm text-gray-900 dark:text-white">
                    {type.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {type.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Role */}
        <div>
          <label
            htmlFor="role"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Target Role
          </label>
          <input
            id="role"
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g., Data Scientist, Product Manager"
            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Company -- Autocomplete */}
        <div ref={companyRef} className="relative">
          <label
            htmlFor="company"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Target Company{" "}
            <span className="text-gray-400">(optional)</span>
          </label>
          <div className="relative">
            <input
              id="company"
              type="text"
              value={company}
              onChange={(e) => {
                setCompany(e.target.value);
                setCompanyOpen(true);
              }}
              onFocus={() => setCompanyOpen(true)}
              placeholder="e.g., Google, JP Morgan, McKinsey"
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-20"
              autoComplete="off"
            />
            {isSeededCompany && (
              <span className="absolute right-10 top-1/2 -translate-y-1/2 text-[10px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-1.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                RAG
              </span>
            )}
            <ChevronDown
              className={`absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 transition-transform ${
                companyOpen ? "rotate-180" : ""
              }`}
            />
          </div>

          {/* Dropdown */}
          {companyOpen && filteredCompanies.length > 0 && (
            <div className="absolute z-20 w-full mt-1 max-h-48 overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
              {filteredCompanies.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setCompany(c);
                    setCompanyOpen(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-blue-50 dark:hover:bg-blue-950 flex items-center justify-between"
                >
                  <span className="text-gray-800 dark:text-gray-200">{c}</span>
                  <span className="text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-1.5 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                    RAG
                  </span>
                </button>
              ))}
              {company.trim() && filteredCompanies.length === 0 && (
                <div className="px-4 py-2 text-sm text-gray-400">
                  No matching companies -- will use general questions
                </div>
              )}
            </div>
          )}
        </div>

        {/* Difficulty */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Difficulty
          </label>
          <div className="flex gap-3">
            {DIFFICULTIES.map((d) => {
              const selected = difficulty === d.id;
              return (
                <button
                  key={d.id}
                  type="button"
                  onClick={() => setDifficulty(d.id)}
                  className={`flex-1 py-3 px-4 rounded-xl border-2 font-medium text-sm transition-all duration-200 ${
                    selected
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 shadow-md shadow-blue-500/10"
                      : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block w-2.5 h-2.5 rounded-full ${d.color} mr-2`}
                  />
                  {d.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Number of questions */}
        <div>
          <label
            htmlFor="numQuestions"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Number of Questions: {numQuestions}
          </label>
          <input
            id="numQuestions"
            type="range"
            min={3}
            max={15}
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            className="w-full accent-blue-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>3 (quick)</span>
            <span>15 (thorough)</span>
          </div>
        </div>

        {/* Start button / Loading overlay */}
        {isLoading ? (
          <LoadingOverlay />
        ) : (
          <button
            type="submit"
            disabled={!role.trim()}
            className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold text-lg transition-all duration-200 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
          >
            Start Interview
          </button>
        )}
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Loading overlay with cycling status messages                       */
/* ------------------------------------------------------------------ */

const LOADING_MESSAGES = [
  "Preparing your interview...",
  "Generating your first question...",
  "Synthesizing audio...",
  "Almost ready...",
];

function LoadingOverlay() {
  const [messageIdx, setMessageIdx] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  // Cycle status message every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Elapsed timer -- tick every second
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full py-6 px-6 rounded-xl bg-gradient-to-r from-blue-600/10 to-indigo-600/10 border-2 border-blue-500/30 flex flex-col items-center gap-4">
      {/* Spinner */}
      <svg
        className="animate-spin h-8 w-8 text-blue-500"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>

      {/* Cycling status text */}
      <p className="text-sm font-medium text-blue-600 dark:text-blue-400 transition-opacity duration-300">
        {LOADING_MESSAGES[messageIdx]}
      </p>

      {/* Subtle elapsed timer */}
      <span className="text-xs text-gray-400">
        {elapsed}s
      </span>
    </div>
  );
}
