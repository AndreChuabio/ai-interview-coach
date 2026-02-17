"use client";

import { useState } from "react";
import { motion } from "framer-motion";

const PROFESSIONS = [
  { id: "data_scientist", name: "Data Scientist", description: "Learn data, statistics, and storytelling." },
  { id: "trader", name: "Trader", description: "Learn markets, risk, and trading basics." },
];

interface Props {
  onDone: () => void;
  onSubmit: (age: number, profession: string) => Promise<void>;
}

export default function OnboardingModal({ onDone, onSubmit }: Props) {
  const [age, setAge] = useState("");
  const [profession, setProfession] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const ageNum = parseInt(age, 10);
    if (Number.isNaN(ageNum) || ageNum < 5 || ageNum > 120) {
      setError("Please enter an age between 5 and 120.");
      return;
    }
    if (!profession || !PROFESSIONS.some((p) => p.id === profession)) {
      setError("Please choose a profession.");
      return;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(ageNum, profession);
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-40 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.4)" }}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 25 }}
        className="rounded-2xl p-6 sm:p-8 w-full max-w-md"
        style={{
          background: "white",
          border: "2px solid var(--duo-blue)",
          boxShadow: "0 20px 40px rgba(0,0,0,0.15)",
        }}
      >
        <h2 className="text-xl font-extrabold mb-1" style={{ color: "var(--duo-eel)" }}>
          Set up your path
        </h2>
        <p className="text-sm mb-6" style={{ color: "var(--duo-wolf)" }}>
          Choose your age and the profession you want to learn. We will adapt the practice to you.
        </p>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="onboarding-age" className="block text-sm font-bold mb-2" style={{ color: "var(--duo-wolf)" }}>
              Your age
            </label>
            <input
              id="onboarding-age"
              type="number"
              min={5}
              max={120}
              value={age}
              onChange={(e) => setAge(e.target.value)}
              placeholder="e.g. 14"
              className="w-full px-4 py-2.5 rounded-xl border-2 text-base"
              style={{ borderColor: "var(--duo-polar)" }}
            />
          </div>
          <div>
            <label className="block text-sm font-bold mb-2" style={{ color: "var(--duo-wolf)" }}>
              Profession you want to learn
            </label>
            <div className="space-y-2">
              {PROFESSIONS.map((p) => (
                <label
                  key={p.id}
                  className="flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-colors"
                  style={{
                    borderColor: profession === p.id ? "var(--duo-blue)" : "var(--duo-polar)",
                    background: profession === p.id ? "var(--duo-blue-light)" : "transparent",
                  }}
                >
                  <input
                    type="radio"
                    name="profession"
                    value={p.id}
                    checked={profession === p.id}
                    onChange={() => setProfession(p.id)}
                    className="mt-1"
                  />
                  <div>
                    <span className="font-bold" style={{ color: "var(--duo-eel)" }}>{p.name}</span>
                    <p className="text-xs mt-0.5" style={{ color: "var(--duo-wolf)" }}>{p.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>
          {error && (
            <p className="text-sm font-semibold" style={{ color: "var(--duo-red)" }}>{error}</p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 rounded-xl font-bold text-white transition-opacity disabled:opacity-60"
            style={{ background: "var(--duo-green)" }}
          >
            {isSubmitting ? "Saving..." : "Continue"}
          </button>
        </form>
      </motion.div>
    </motion.div>
  );
}
