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
import { getSkillPath, type InterviewSetupRequest, type SkillPathSection } from "@/lib/api";

interface Props {
  onStart: (setup: InterviewSetupRequest) => void;
  isLoading: boolean;
  presetQuickPractice?: { topic: string; interviewType: InterviewSetupRequest["interview_type"] } | null;
  onPresetApplied?: () => void;
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

const TOPICS_BY_TYPE: Record<InterviewSetupRequest["interview_type"], string[]> = {
  behavioral: ["Leadership", "Conflict Resolution", "Teamwork", "Problem Solving", "Adaptability", "Communication"],
  technical: ["System Design", "Algorithms", "Data Structures", "Machine Learning", "SQL & Databases", "Statistics"],
  case_study: ["Market Sizing", "Profitability", "Growth Strategy", "Product Strategy"],
};

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

export default function InterviewSetup({ onStart, isLoading, presetQuickPractice, onPresetApplied }: Props) {
  const [interviewType, setInterviewType] =
    useState<InterviewSetupRequest["interview_type"]>("behavioral");
  const [role, setRole] = useState("Software Engineer");
  const [company, setCompany] = useState("");
  const [difficulty, setDifficulty] =
    useState<InterviewSetupRequest["difficulty"]>("medium");
  const [numQuestions, setNumQuestions] = useState(5);
  const [practiceMode, setPracticeMode] = useState<"full" | "quick">("full");
  const [topic, setTopic] = useState("");

  const [companyOpen, setCompanyOpen] = useState(false);
  const [skillPath, setSkillPath] = useState<SkillPathSection[]>([]);
  const companyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getSkillPath().then((data) => setSkillPath(data.path || []));
  }, []);

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
    const num = practiceMode === "quick" ? 3 : numQuestions;
    onStart({
      interview_type: interviewType,
      role,
      company,
      difficulty,
      num_questions: num,
      practice_mode: practiceMode,
      topic: practiceMode === "quick" && topic ? topic : undefined,
    });
  };

  const topicsForType = TOPICS_BY_TYPE[interviewType];

  useEffect(() => {
    if (practiceMode === "quick") {
      const list = TOPICS_BY_TYPE[interviewType];
      if (list.length > 0 && (!topic || !list.includes(topic))) {
        setTopic(list[0]);
      }
    }
  }, [practiceMode, interviewType]);

  useEffect(() => {
    if (presetQuickPractice) {
      setInterviewType(presetQuickPractice.interviewType);
      setPracticeMode("quick");
      setTopic(presetQuickPractice.topic);
      onPresetApplied?.();
    }
  }, [presetQuickPractice]);

  const canSubmit = role.trim() && (practiceMode === "full" || (practiceMode === "quick" && topic));

  const handlePathTopicClick = (interviewType: InterviewSetupRequest["interview_type"], topicName: string) => {
    setInterviewType(interviewType);
    setPracticeMode("quick");
    setTopic(topicName);
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Skill path (Duo-style): click a topic to quick-practice */}
      {skillPath.length > 0 && (
        <div className="mb-8">
          <label className="block text-sm font-bold uppercase tracking-wide mb-3" style={{ color: "var(--duo-wolf)" }}>
            Practice Path
          </label>
          <div className="flex flex-wrap gap-2">
            {skillPath.map((section) => (
              <div key={section.interview_type} className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ background: "var(--duo-polar)", color: "var(--duo-eel)" }}>
                  {section.interview_type.replace("_", " ")}
                </span>
                {section.topics.map((t) => {
                  const isSelected = practiceMode === "quick" && topic === t && interviewType === section.interview_type;
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => handlePathTopicClick(section.interview_type, t)}
                      className="text-xs font-semibold px-2.5 py-1 rounded-xl transition-all"
                      style={
                        isSelected
                          ? { background: "var(--duo-green)", color: "white" }
                          : { background: "var(--duo-polar)", color: "var(--duo-eel)" }
                      }
                    >
                      {t}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}

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

        {/* Practice mode: Quick vs Full */}
        <div>
          <label className="block text-sm font-bold uppercase tracking-wide mb-3" style={{ color: "var(--duo-wolf)" }}>
            Practice Mode
          </label>
          <div className="grid grid-cols-2 gap-3">
            <motion.button
              type="button"
              onClick={() => setPracticeMode("full")}
              whileTap={{ scale: 0.97 }}
              className="duo-card text-left"
              style={
                practiceMode === "full"
                  ? {
                      borderColor: "var(--duo-blue)",
                      background: "var(--duo-blue-light)",
                      borderLeftWidth: "4px",
                    }
                  : {}
              }
            >
              <div className="font-bold text-sm" style={{ color: "var(--duo-eel)" }}>
                Full interview
              </div>
              <div className="text-xs font-medium mt-1" style={{ color: "var(--duo-wolf)" }}>
                5–15 questions, full run
              </div>
            </motion.button>
            <motion.button
              type="button"
              onClick={() => setPracticeMode("quick")}
              whileTap={{ scale: 0.97 }}
              className="duo-card text-left"
              style={
                practiceMode === "quick"
                  ? {
                      borderColor: "var(--duo-green)",
                      background: "var(--duo-green-light)",
                      borderLeftWidth: "4px",
                    }
                  : {}
              }
            >
              <div className="font-bold text-sm" style={{ color: "var(--duo-eel)" }}>
                Quick practice
              </div>
              <div className="text-xs font-medium mt-1" style={{ color: "var(--duo-wolf)" }}>
                2–3 questions, one topic
              </div>
            </motion.button>
          </div>
        </div>

        {/* Topic (quick mode only) */}
        {practiceMode === "quick" && (
          <div>
            <label
              htmlFor="topic"
              className="block text-sm font-bold uppercase tracking-wide mb-2"
              style={{ color: "var(--duo-wolf)" }}
            >
              Topic
            </label>
            <select
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full px-4 py-3 rounded-2xl text-base font-semibold focus:outline-none transition-all"
              style={{
                border: "2px solid var(--duo-polar)",
                color: "var(--duo-eel)",
                background: "white",
              }}
            >
              {topicsForType.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        )}

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

        {/* Number of questions (full mode only) */}
        {practiceMode === "full" && (
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
        )}

        {/* Start button / Loading overlay */}
        {isLoading ? (
          <LoadingOverlay />
        ) : (
          <motion.button
            type="submit"
            disabled={!canSubmit}
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
