"use client";

import { useState } from "react";
import { Mic, Briefcase, GraduationCap, TrendingUp } from "lucide-react";
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

export default function InterviewSetup({ onStart, isLoading }: Props) {
  const [interviewType, setInterviewType] =
    useState<InterviewSetupRequest["interview_type"]>("behavioral");
  const [role, setRole] = useState("Software Engineer");
  const [company, setCompany] = useState("");
  const [difficulty, setDifficulty] =
    useState<InterviewSetupRequest["difficulty"]>("medium");
  const [numQuestions, setNumQuestions] = useState(5);

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
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900 mb-4">
          <Mic className="w-8 h-8 text-blue-600 dark:text-blue-300" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          AI Interview Coach
        </h1>
        <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Practice interviews with an AI that analyzes your responses, tone, and
          facial expressions in real time.
        </p>
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
                  className={`p-4 rounded-lg border-2 text-left transition-all ${
                    selected
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 mb-2 ${
                      selected
                        ? "text-blue-600"
                        : "text-gray-400"
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

        {/* Company */}
        <div>
          <label
            htmlFor="company"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Target Company{" "}
            <span className="text-gray-400">(optional)</span>
          </label>
          <input
            id="company"
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="e.g., Google, JP Morgan, McKinsey"
            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
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
                  className={`flex-1 py-2.5 px-4 rounded-lg border-2 font-medium text-sm transition-all ${
                    selected
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300"
                      : "border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:border-gray-300"
                  }`}
                >
                  <span
                    className={`inline-block w-2 h-2 rounded-full ${d.color} mr-2`}
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

        {/* Start button */}
        <button
          type="submit"
          disabled={isLoading || !role.trim()}
          className="w-full py-3 px-6 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold text-lg transition-colors"
        >
          {isLoading ? "Starting Interview..." : "Start Interview"}
        </button>
      </form>
    </div>
  );
}
