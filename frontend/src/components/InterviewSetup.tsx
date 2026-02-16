"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
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
    color: "var(--duo-blue)",
    lightBg: "var(--duo-blue-light)",
    pushColor: "var(--duo-blue-push)",
  },
  {
    id: "technical" as const,
    label: "Technical",
    description: "Data science, coding, system design",
    icon: GraduationCap,
    color: "var(--duo-purple)",
    lightBg: "var(--duo-purple-light)",
    pushColor: "var(--duo-purple-push)",
  },
  {
    id: "case_study" as const,
    label: "Case Study",
    description: "Market sizing, profitability, strategy",
    icon: TrendingUp,
    color: "var(--duo-orange)",
    lightBg: "var(--duo-orange-light)",
    pushColor: "var(--duo-orange-push)",
  },
];

const DIFFICULTIES = [
  {
    id: "easy" as const,
    label: "Easy",
    color: "var(--duo-green)",
    pushColor: "var(--duo-green-push)",
    hoverColor: "var(--duo-green-hover)",
  },
  {
    id: "medium" as const,
    label: "Medium",
    color: "var(--duo-orange)",
    pushColor: "var(--duo-orange-push)",
    hoverColor: "var(--duo-orange-hover)",
  },
  {
    id: "hard" as const,
    label: "Hard",
    color: "var(--duo-red)",
    pushColor: "var(--duo-red-push)",
    hoverColor: "var(--duo-red-hover)",
  },
];

const FEATURES = [
  { icon: Mic, label: "Voice AI", description: "Natural conversation", color: "var(--duo-green)", bg: "var(--duo-green-light)" },
  { icon: Eye, label: "Face Tracking", description: "Expression analysis", color: "var(--duo-blue)", bg: "var(--duo-blue-light)" },
  { icon: AudioLines, label: "Tone Analysis", description: "Pace and fillers", color: "var(--duo-orange)", bg: "var(--duo-orange-light)" },
  { icon: Database, label: "Knowledge Graph", description: "Company context", color: "var(--duo-purple)", bg: "var(--duo-purple-light)" },
];

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
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 260, damping: 20 }}
          className="inline-flex items-center justify-center w-20 h-20 rounded-2xl mb-5"
          style={{ background: "var(--duo-green)" }}
        >
          <Mic className="w-10 h-10 text-white" />
        </motion.div>
        <h1 className="text-4xl font-extrabold mb-2" style={{ color: "var(--duo-eel)" }}>
          Practice Makes Perfect
        </h1>
        <p className="text-lg font-medium max-w-md mx-auto" style={{ color: "var(--duo-wolf)" }}>
          Ace your next interview with real-time AI feedback on your responses, tone, and body language.
        </p>
      </div>

      {/* Feature badges */}
      <div className="grid grid-cols-4 gap-3 mb-10">
        {FEATURES.map((f, i) => {
          const Icon = f.icon;
          return (
            <motion.div
              key={f.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.3 }}
              className="flex flex-col items-center text-center p-3 rounded-2xl"
              style={{ background: f.bg }}
            >
              <div
                className="w-9 h-9 rounded-xl flex items-center justify-center mb-1.5"
                style={{ background: f.color }}
              >
                <Icon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xs font-bold" style={{ color: "var(--duo-eel)" }}>
                {f.label}
              </span>
              <span className="text-[10px] font-medium" style={{ color: "var(--duo-wolf)" }}>
                {f.description}
              </span>
            </motion.div>
          );
        })}
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Interview Type */}
        <div>
          <label className="block text-sm font-bold uppercase tracking-wide mb-3" style={{ color: "var(--duo-wolf)" }}>
            Interview Type
          </label>
          <div className="grid grid-cols-3 gap-3">
            {INTERVIEW_TYPES.map((type) => {
              const Icon = type.icon;
              const selected = interviewType === type.id;
              return (
                <motion.button
                  key={type.id}
                  type="button"
                  onClick={() => setInterviewType(type.id)}
                  whileTap={{ scale: 0.97 }}
                  className="duo-card text-left"
                  style={
                    selected
                      ? {
                          borderColor: type.color,
                          background: type.lightBg,
                          borderLeftWidth: "4px",
                          transform: "scale(1.02)",
                          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
                        }
                      : {}
                  }
                >
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center mb-2"
                    style={{
                      background: selected ? type.color : "var(--duo-polar)",
                    }}
                  >
                    <Icon
                      className="w-5 h-5"
                      style={{ color: selected ? "white" : "var(--duo-hare)" }}
                    />
                  </div>
                  <div className="font-bold text-sm" style={{ color: "var(--duo-eel)" }}>
                    {type.label}
                  </div>
                  <div className="text-xs font-medium mt-1" style={{ color: "var(--duo-wolf)" }}>
                    {type.description}
                  </div>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Role */}
        <div>
          <label
            htmlFor="role"
            className="block text-sm font-bold uppercase tracking-wide mb-2"
            style={{ color: "var(--duo-wolf)" }}
          >
            Target Role
          </label>
          <input
            id="role"
            type="text"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="e.g., Data Scientist, Product Manager"
            className="w-full px-4 py-3 rounded-2xl text-base font-semibold focus:outline-none transition-all"
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
        </div>

        {/* Company Autocomplete */}
        <div ref={companyRef} className="relative">
          <label
            htmlFor="company"
            className="block text-sm font-bold uppercase tracking-wide mb-2"
            style={{ color: "var(--duo-wolf)" }}
          >
            Target Company{" "}
            <span className="normal-case font-medium" style={{ color: "var(--duo-hare)" }}>(optional)</span>
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
              onFocus={(e) => {
                setCompanyOpen(true);
                e.currentTarget.style.borderColor = "var(--duo-blue)";
                e.currentTarget.style.boxShadow = "0 0 0 3px var(--duo-blue-light)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "var(--duo-polar)";
                e.currentTarget.style.boxShadow = "none";
              }}
              placeholder="e.g., Google, JP Morgan, McKinsey"
              className="w-full px-4 py-3 rounded-2xl text-base font-semibold pr-20 focus:outline-none transition-all"
              style={{
                border: "2px solid var(--duo-polar)",
                color: "var(--duo-eel)",
                background: "white",
              }}
              autoComplete="off"
            />
            {isSeededCompany && (
              <span
                className="absolute right-10 top-1/2 -translate-y-1/2 text-[10px] font-bold px-2 py-0.5 rounded-full"
                style={{
                  background: "var(--duo-green-light)",
                  color: "var(--duo-green-push)",
                  border: "1px solid var(--duo-green)",
                }}
              >
                RAG
              </span>
            )}
            <ChevronDown
              className={`absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 transition-transform ${
                companyOpen ? "rotate-180" : ""
              }`}
              style={{ color: "var(--duo-hare)" }}
            />
          </div>

          {companyOpen && filteredCompanies.length > 0 && (
            <div
              className="absolute z-20 w-full mt-2 max-h-48 overflow-y-auto rounded-2xl shadow-lg"
              style={{
                background: "white",
                border: "2px solid var(--duo-polar)",
              }}
            >
              {filteredCompanies.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setCompany(c);
                    setCompanyOpen(false);
                  }}
                  className="w-full text-left px-4 py-2.5 text-sm font-semibold flex items-center justify-between transition-colors"
                  style={{ color: "var(--duo-eel)" }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "var(--duo-green-light)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  <span>{c}</span>
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                    style={{
                      background: "var(--duo-green-light)",
                      color: "var(--duo-green-push)",
                      border: "1px solid var(--duo-green)",
                    }}
                  >
                    RAG
                  </span>
                </button>
              ))}
              {company.trim() && filteredCompanies.length === 0 && (
                <div className="px-4 py-2.5 text-sm font-medium" style={{ color: "var(--duo-hare)" }}>
                  No matching companies -- will use general questions
                </div>
              )}
            </div>
          )}
        </div>

        {/* Difficulty */}
        <div>
          <label className="block text-sm font-bold uppercase tracking-wide mb-3" style={{ color: "var(--duo-wolf)" }}>
            Difficulty
          </label>
          <div className="flex gap-3">
            {DIFFICULTIES.map((d) => {
              const selected = difficulty === d.id;
              return (
                <motion.button
                  key={d.id}
                  type="button"
                  onClick={() => setDifficulty(d.id)}
                  whileTap={{ scale: 0.96 }}
                  className="btn-3d flex-1 py-3 px-4 text-sm"
                  style={
                    selected
                      ? {
                          background: d.color,
                          borderBottomColor: d.pushColor,
                          color: "white",
                        }
                      : {
                          background: "white",
                          borderBottomColor: "var(--duo-polar)",
                          color: "var(--duo-eel)",
                          border: "2px solid var(--duo-polar)",
                          borderBottom: "4px solid var(--duo-polar)",
                        }
                  }
                >
                  {d.label}
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Number of questions */}
        <div>
          <label
            htmlFor="numQuestions"
            className="block text-sm font-bold uppercase tracking-wide mb-2"
            style={{ color: "var(--duo-wolf)" }}
          >
            Number of Questions:{" "}
            <span
              className="inline-block px-3 py-0.5 rounded-full text-sm font-extrabold"
              style={{ background: "var(--duo-green-light)", color: "var(--duo-green-push)" }}
            >
              {numQuestions}
            </span>
          </label>
          <input
            id="numQuestions"
            type="range"
            min={3}
            max={15}
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs font-semibold mt-1" style={{ color: "var(--duo-hare)" }}>
            <span>3 (quick)</span>
            <span>15 (thorough)</span>
          </div>
        </div>

        {/* Start button / Loading overlay */}
        {isLoading ? (
          <LoadingOverlay />
        ) : (
          <motion.button
            type="submit"
            disabled={!role.trim()}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            className="btn-3d btn-3d-green w-full py-4 text-lg"
          >
            Start Interview
          </motion.button>
        )}
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Loading overlay with cycling status messages                        */
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

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className="w-full py-8 px-6 rounded-2xl flex flex-col items-center gap-4"
      style={{
        background: "var(--duo-green-light)",
        border: "2px solid var(--duo-green)",
      }}
    >
      {/* Bouncing dots */}
      <div className="flex gap-2">
        <span className="bounce-dot" style={{ background: "var(--duo-green)" }} />
        <span className="bounce-dot" style={{ background: "var(--duo-blue)" }} />
        <span className="bounce-dot" style={{ background: "var(--duo-orange)" }} />
      </div>

      <p className="text-sm font-bold" style={{ color: "var(--duo-green-push)" }}>
        {LOADING_MESSAGES[messageIdx]}
      </p>

      <span className="text-xs font-semibold" style={{ color: "var(--duo-hare)" }}>
        {elapsed}s
      </span>
    </div>
  );
}
