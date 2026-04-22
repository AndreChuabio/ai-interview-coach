/**
 * Backend API client for the AI Interview Coach.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface InterviewSetupRequest {
  interview_type: "behavioral" | "technical" | "case_study";
  role: string;
  company: string;
  difficulty: "easy" | "medium" | "hard";
  num_questions: number;
}

export interface InterviewSession {
  session_id: string;
  interview_type: string;
  role: string;
  company: string;
  difficulty: string;
  num_questions: number;
  status: string;
  transcript: TranscriptEntry[];
}

export interface TranscriptEntry {
  role: "interviewer" | "candidate";
  text: string;
  timestamp: string;
  audio_duration_sec?: number;
}

export interface RespondResponse {
  session_id: string;
  transcript_text: string;
  interviewer_text: string;
  interviewer_audio_url: string;
  question_number: number;
  is_final: boolean;
  tone_snapshot?: ToneSnapshot;
}

export interface ToneSnapshot {
  speaking_pace_wpm: number;
  filler_word_count: number;
  filler_words: string[];
  avg_pitch_hz: number;
  pitch_variation: number;
  pitch_range_hz: number;
  rising_intonation_ratio: number;
  monotone_flag: boolean;
  jitter: number;
  shimmer: number;
  energy_level: number;
  silence_ratio: number;
  duration_sec: number;
}

export interface FaceSnapshot {
  timestamp: string;
  dominant_emotion: string;
  emotion_scores: Record<string, number>;
  eye_contact: boolean;
  head_pitch: number;
  head_yaw: number;
}

export interface FeedbackReport {
  session_id: string;
  interview_type: string;
  role: string;
  company: string;
  overall_score: number;
  content: {
    overall_score: number;
    relevance: number;
    specificity: number;
    structure: number;
    strengths: string[];
    improvements: string[];
    example_responses: string[];
  };
  communication: {
    overall_score: number;
    pace_score: number;
    clarity_score: number;
    filler_score: number;
    confidence_score: number;
    avg_wpm: number;
    total_fillers: number;
    strengths: string[];
    improvements: string[];
  };
  body_language: {
    overall_score: number;
    eye_contact_pct: number;
    emotion_distribution: Record<string, number>;
    fidgeting_score: number;
    strengths: string[];
    improvements: string[];
  };
  top_strengths: string[];
  top_improvements: string[];
  action_items: string[];
}

/** Start a new interview session. */
export async function startInterview(
  setup: InterviewSetupRequest
): Promise<InterviewSession> {
  const res = await fetch(`${API_BASE}/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(setup),
  });
  if (!res.ok) throw new Error(`Start interview failed: ${res.status}`);
  return res.json();
}

/** Get the opening audio for a session. */
export async function getOpeningAudio(
  sessionId: string
): Promise<{ text: string; audio: string }> {
  const res = await fetch(`${API_BASE}/interview/opening-audio/${sessionId}`);
  if (!res.ok) throw new Error(`Get opening audio failed: ${res.status}`);
  return res.json();
}

/** Send a candidate audio response and get the interviewer follow-up. */
export async function sendResponse(
  sessionId: string,
  audioBlob: Blob
): Promise<RespondResponse> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "response.webm");

  // Allow up to 2 minutes for STT + LLM + TTS pipeline
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000);

  try {
    const res = await fetch(`${API_BASE}/interview/respond/${sessionId}`, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => "");
      throw new Error(`Send response failed (${res.status}): ${detail}`);
    }
    return res.json();
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Response timed out. The backend may still be processing. Try again.");
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

/** Submit batched face data snapshots. */
export async function submitFaceData(
  sessionId: string,
  snapshots: FaceSnapshot[]
): Promise<void> {
  await fetch(`${API_BASE}/interview/face-data/${sessionId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, snapshots }),
  });
}

/** Generate feedback report for a completed session. */
export async function generateFeedback(
  sessionId: string
): Promise<FeedbackReport> {
  const res = await fetch(`${API_BASE}/feedback/generate/${sessionId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`Generate feedback failed: ${res.status}`);
  return res.json();
}

/* ------------------------------------------------------------------ */
/* Trainer (flashcards) API                                           */
/* ------------------------------------------------------------------ */

export interface TrainerCard {
  id: number;
  deck: string;
  topic: string;
  question: string;
  reference_answer: string;
  difficulty: string;
}

export interface NextCardResponse {
  card: TrainerCard | null;
  remaining_new: number;
  remaining_review: number;
}

export interface AnswerResponse {
  card_id: number;
  score: number;
  grade: number;
  feedback: string;
  missing_concepts: string[];
  reference_answer: string;
}

export interface ProgressSummary {
  total_reviews: number;
  accuracy: number;
  streak_days: number;
  mastered: number;
  learning: number;
  struggling: number;
  new: number;
  total_cards: number;
  recent_reviews: Array<{
    card_id: number;
    grade: number;
    llm_score: number;
    reviewed_at: string | null;
  }>;
}

export async function registerLearner(
  learnerId: string,
  displayName = ""
): Promise<void> {
  await fetch(`${API_BASE}/trainer/learner`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ learner_id: learnerId, display_name: displayName }),
  });
}

export async function getNextCard(
  learnerId: string,
  deck = "ml_fundamentals"
): Promise<NextCardResponse> {
  const res = await fetch(
    `${API_BASE}/trainer/decks/${deck}/next?learner_id=${encodeURIComponent(
      learnerId
    )}`
  );
  if (!res.ok) throw new Error(`Next card failed: ${res.status}`);
  return res.json();
}

export async function submitCardAnswer(
  cardId: number,
  learnerId: string,
  userAnswer: string,
  timeSpentMs: number
): Promise<AnswerResponse> {
  const res = await fetch(`${API_BASE}/trainer/cards/${cardId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      learner_id: learnerId,
      user_answer: userAnswer,
      time_spent_ms: timeSpentMs,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Submit answer failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export async function getProgress(
  learnerId: string,
  deck?: string
): Promise<ProgressSummary> {
  const qs = new URLSearchParams({ learner_id: learnerId });
  if (deck) qs.set("deck", deck);
  const res = await fetch(`${API_BASE}/trainer/progress?${qs.toString()}`);
  if (!res.ok) throw new Error(`Progress failed: ${res.status}`);
  return res.json();
}

/* ------------------------------------------------------------------ */
/* Class materials API                                                */
/* ------------------------------------------------------------------ */

export interface ClassSummary {
  class_id: string;
  title: string;
  deck: string;
  status: string;
  file_count: number;
  chunk_count: number;
  card_count: number;
  error_message: string;
}

export interface UploadClassResponse {
  class_id: string;
  title: string;
  deck: string;
  status: string;
  file_count: number;
  chunk_count: number;
  skipped_files: string[];
}

export interface ClassStatus {
  class_id: string;
  title: string;
  deck: string;
  status: string;
  file_count: number;
  chunk_count: number;
  embedded_chunks: number;
  progress: number;
  card_count: number;
  error_message: string;
}

/** Upload a class: multipart with learner_id, title, and multiple files. */
export async function uploadClass(
  learnerId: string,
  title: string,
  files: File[],
  onProgress?: (pct: number) => void
): Promise<UploadClassResponse> {
  const fd = new FormData();
  fd.append("learner_id", learnerId);
  fd.append("title", title);
  for (const f of files) {
    // Preserve folder path if the browser supplied it.
    const rel = (f as File & { webkitRelativePath?: string })
      .webkitRelativePath;
    fd.append("files", f, rel && rel.length > 0 ? rel : f.name);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/classes/upload`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(e.loaded / e.total);
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          reject(new Error("Upload response was not JSON"));
        }
      } else {
        reject(new Error(`Upload failed (${xhr.status}): ${xhr.responseText}`));
      }
    };
    xhr.onerror = () => reject(new Error("Upload network error"));
    xhr.send(fd);
  });
}

export async function listClasses(learnerId: string): Promise<ClassSummary[]> {
  const res = await fetch(
    `${API_BASE}/classes/?learner_id=${encodeURIComponent(learnerId)}`
  );
  if (!res.ok) throw new Error(`List classes failed: ${res.status}`);
  return res.json();
}

export async function getClassStatus(
  classId: string,
  learnerId: string
): Promise<ClassStatus> {
  const res = await fetch(
    `${API_BASE}/classes/${classId}/status?learner_id=${encodeURIComponent(
      learnerId
    )}`
  );
  if (!res.ok) throw new Error(`Class status failed: ${res.status}`);
  return res.json();
}

export async function deleteClass(
  classId: string,
  learnerId: string
): Promise<void> {
  const res = await fetch(
    `${API_BASE}/classes/${classId}?learner_id=${encodeURIComponent(learnerId)}`,
    { method: "DELETE" }
  );
  if (!res.ok) throw new Error(`Delete class failed: ${res.status}`);
}

export async function generateMoreCards(
  classId: string,
  learnerId: string,
  count = 20
): Promise<ClassStatus> {
  const res = await fetch(
    `${API_BASE}/classes/${classId}/generate-cards?learner_id=${encodeURIComponent(
      learnerId
    )}&count=${count}`,
    { method: "POST" }
  );
  if (!res.ok) throw new Error(`Generate cards failed: ${res.status}`);
  return res.json();
}

/** Check backend health and active providers. */
export async function healthCheck(): Promise<{
  status: string;
  providers: { llm: string; stt: string; tts: string };
}> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
