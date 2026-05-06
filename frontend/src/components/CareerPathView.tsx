"use client";

import { motion } from "framer-motion";
import { Mic, Check, Lock } from "lucide-react";
import type { CareerPathResponse, CareerPathLesson } from "@/lib/api";

interface Props {
  path: CareerPathResponse;
  onPracticeLesson: (params: {
    role: string;
    profession: string;
    skill_id: string;
    lesson_id: string;
  }) => void;
}

function LessonNode({
  lesson,
  onPractice,
}: {
  lesson: CareerPathLesson;
  onPractice: () => void;
}) {
  const canPractice = lesson.unlocked && lesson.type === "mini_interview";
  const isConceptQuiz = lesson.type === "concept_quiz";

  return (
    <div
      className="flex items-center gap-3 py-2 px-3 rounded-xl border-2 transition-colors"
      style={{
        borderColor: lesson.completed
          ? "var(--duo-green)"
          : lesson.unlocked
            ? "var(--duo-polar)"
            : "var(--duo-hare)",
        background: lesson.completed
          ? "var(--duo-green-light)"
          : lesson.unlocked
            ? "white"
            : "var(--duo-polar)",
      }}
    >
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
        style={{
          background: lesson.completed
            ? "var(--duo-green)"
            : lesson.unlocked
              ? "var(--duo-blue)"
              : "var(--duo-hare)",
          color: "white",
        }}
      >
        {lesson.completed ? (
          <Check width={16} height={16} strokeWidth={3} />
        ) : lesson.unlocked ? (
          isConceptQuiz ? (
            <span className="text-xs font-bold">?</span>
          ) : (
            <Mic width={14} height={14} />
          )
        ) : (
          <Lock width={14} height={14} />
        )}
      </div>
      <span
        className="flex-1 text-sm font-semibold"
        style={{
          color: lesson.unlocked ? "var(--duo-eel)" : "var(--duo-wolf)",
        }}
      >
        {lesson.name}
      </span>
      {canPractice && (
        <button
          type="button"
          onClick={onPractice}
          className="text-xs font-bold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-90"
          style={{
            background: "var(--duo-green)",
            color: "white",
          }}
        >
          Practice
        </button>
      )}
    </div>
  );
}

export default function CareerPathView({ path, onPracticeLesson }: Props) {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-lg font-extrabold" style={{ color: "var(--duo-eel)" }}>
          {path.info.name}
        </h2>
        {path.info.description && (
          <p className="text-sm mt-1" style={{ color: "var(--duo-wolf)" }}>
            {path.info.description}
          </p>
        )}
      </div>
      <div className="space-y-8">
        {path.skills.map((skill) => (
          <motion.section
            key={skill.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl p-4 border-2"
            style={{ borderColor: "var(--duo-polar)", background: "white" }}
          >
            <h3 className="text-base font-bold mb-4" style={{ color: "var(--duo-blue)" }}>
              {skill.name}
            </h3>
            <div className="space-y-2">
              {skill.lessons.map((lesson) => (
                <LessonNode
                  key={lesson.id}
                  lesson={lesson}
                  onPractice={() =>
                    onPracticeLesson({
                      role: path.info.role,
                      profession: path.profession,
                      skill_id: skill.id,
                      lesson_id: lesson.id,
                    })
                  }
                />
              ))}
            </div>
          </motion.section>
        ))}
      </div>
    </div>
  );
}
