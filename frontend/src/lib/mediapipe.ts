/**
 * MediaPipe Face Mesh integration for in-browser facial expression tracking.
 * Runs entirely client-side via WebAssembly -- zero API cost.
 *
 * Tracks: eye contact (gaze direction), dominant emotion heuristic,
 * head pitch/yaw, and provides per-frame snapshots.
 *
 * Emotion classification uses calibrated heuristics with temporal smoothing
 * (exponential moving average) and optional resting-face baseline calibration.
 */

import {
  FaceLandmarker,
  FilesetResolver,
  type FaceLandmarkerResult,
} from "@mediapipe/tasks-vision";

export interface FaceFrame {
  timestamp: string;
  dominant_emotion: string;
  emotion_scores: Record<string, number>;
  eye_contact: boolean;
  head_pitch: number;
  head_yaw: number;
}

let faceLandmarker: FaceLandmarker | null = null;
let lastTimestampMs = -1;
let isReady = false;

// Temporal smoothing state (exponential moving average)
const SMOOTHING_FACTOR = 0.3;
let smoothedScores: Record<string, number> = {};

// Resting-face calibration baseline
let baselineShapes: Record<string, number> | null = null;
let calibrating = false;

/**
 * Initialize the MediaPipe FaceLandmarker.
 * Tries GPU delegate first, falls back to CPU if unavailable.
 * Call once on component mount; subsequent calls are no-ops.
 */
export async function initFaceLandmarker(): Promise<FaceLandmarker> {
  if (faceLandmarker && isReady) return faceLandmarker;

  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm"
  );

  const options = {
    runningMode: "VIDEO" as const,
    numFaces: 1,
    outputFaceBlendshapes: true,
    outputFacialTransformationMatrixes: true,
  };

  // Try GPU first, fall back to CPU
  try {
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "GPU",
      },
      ...options,
    });
  } catch {
    console.warn("GPU delegate unavailable, falling back to CPU");
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "CPU",
      },
      ...options,
    });
  }

  isReady = true;
  lastTimestampMs = -1;
  return faceLandmarker;
}

/**
 * Calibrate the resting-face baseline by collecting frames over a short
 * window and averaging each blendshape. This baseline is subtracted from
 * live readings so that per-user resting expression variations do not
 * pollute the emotion classification.
 *
 * Call after the FaceLandmarker is initialized and the video is playing.
 * Resolves once calibration is complete.
 *
 * @param video - The HTMLVideoElement providing the webcam feed.
 * @param frames - Number of frames to sample (default 30, roughly 1 second).
 */
export async function calibrateBaseline(
  video: HTMLVideoElement,
  frames: number = 30
): Promise<void> {
  if (!faceLandmarker || !isReady) return;
  calibrating = true;

  const accumulator: Record<string, number[]> = {};
  let collected = 0;

  while (collected < frames) {
    if (video.readyState < 2) {
      await new Promise((r) => setTimeout(r, 30));
      continue;
    }

    const ts = Math.max(performance.now(), lastTimestampMs + 1);
    lastTimestampMs = ts;

    let result: FaceLandmarkerResult;
    try {
      result = faceLandmarker.detectForVideo(video, ts);
    } catch {
      await new Promise((r) => setTimeout(r, 30));
      continue;
    }

    if (!result.faceBlendshapes || result.faceBlendshapes.length === 0) {
      await new Promise((r) => setTimeout(r, 30));
      continue;
    }

    for (const shape of result.faceBlendshapes[0].categories) {
      if (!accumulator[shape.categoryName]) {
        accumulator[shape.categoryName] = [];
      }
      accumulator[shape.categoryName].push(shape.score);
    }
    collected++;
    await new Promise((r) => setTimeout(r, 33));
  }

  // Average each blendshape across collected frames
  const baseline: Record<string, number> = {};
  for (const [name, values] of Object.entries(accumulator)) {
    baseline[name] = values.reduce((a, b) => a + b, 0) / values.length;
  }
  baselineShapes = baseline;
  calibrating = false;
}

/**
 * Whether a calibration is currently running.
 */
export function isCalibrating(): boolean {
  return calibrating;
}

/**
 * Whether a calibration baseline has been captured.
 */
export function hasBaseline(): boolean {
  return baselineShapes !== null;
}

/**
 * Apply temporal smoothing (exponential moving average) to raw emotion
 * scores so that the displayed dominant emotion does not flicker between
 * frames. A smoothing factor of 0.3 means roughly 70% of the previous
 * smoothed value is retained each frame.
 */
function smoothEmotionScores(
  raw: Record<string, number>
): Record<string, number> {
  const result: Record<string, number> = {};
  for (const [emotion, score] of Object.entries(raw)) {
    const prev = smoothedScores[emotion] || 0;
    result[emotion] = Math.round(
      (prev + SMOOTHING_FACTOR * (score - prev)) * 100
    ) / 100;
  }
  smoothedScores = result;
  return result;
}

/**
 * Process a single video frame and return facial expression data.
 * Returns null if the model is not ready or the video frame is not available.
 */
export function processFrame(
  video: HTMLVideoElement,
  timestampMs: number
): FaceFrame | null {
  if (!faceLandmarker || !isReady) return null;

  // Video must have enough data loaded
  if (video.readyState < 2) return null;

  // MediaPipe requires strictly increasing timestamps
  const ts = Math.max(timestampMs, lastTimestampMs + 1);
  lastTimestampMs = ts;

  let result: FaceLandmarkerResult;
  try {
    result = faceLandmarker.detectForVideo(video, ts);
  } catch {
    // Silently skip frames that fail during warmup
    return null;
  }

  if (!result.faceBlendshapes || result.faceBlendshapes.length === 0) {
    return null;
  }

  const blendshapes = result.faceBlendshapes[0].categories;
  const shapeMap: Record<string, number> = {};
  for (const shape of blendshapes) {
    shapeMap[shape.categoryName] = shape.score;
  }

  // Apply resting-face baseline correction when available.
  // Use a soft subtraction: only remove 60% of the baseline to avoid
  // zeroing out small but meaningful signals. Blendshapes that are
  // below their resting baseline are clamped to 0.
  const BASELINE_STRENGTH = 0.6;
  const adjusted: Record<string, number> = {};
  for (const [name, value] of Object.entries(shapeMap)) {
    const base = baselineShapes ? (baselineShapes[name] || 0) : 0;
    adjusted[name] = Math.max(0, value - base * BASELINE_STRENGTH);
  }

  // Estimate head pose from transformation matrix
  let headPitch = 0;
  let headYaw = 0;
  if (
    result.facialTransformationMatrixes &&
    result.facialTransformationMatrixes.length > 0
  ) {
    const matrix = result.facialTransformationMatrixes[0].data;
    // Extract approximate Euler angles from the 4x4 transformation matrix
    // matrix is stored column-major as Float32Array(16)
    headPitch = Math.asin(-matrix[6]) * (180 / Math.PI);
    headYaw = Math.atan2(matrix[2], matrix[10]) * (180 / Math.PI);
  }

  // Estimate eye contact: eyes looking roughly forward
  const lookLeft =
    (shapeMap["eyeLookOutLeft"] || 0) + (shapeMap["eyeLookInRight"] || 0);
  const lookRight =
    (shapeMap["eyeLookInLeft"] || 0) + (shapeMap["eyeLookOutRight"] || 0);
  const lookUp =
    (shapeMap["eyeLookUpLeft"] || 0) + (shapeMap["eyeLookUpRight"] || 0);
  const lookDown =
    (shapeMap["eyeLookDownLeft"] || 0) + (shapeMap["eyeLookDownRight"] || 0);

  const totalGazeOffset = lookLeft + lookRight + lookUp + lookDown;
  const eyeContact = totalGazeOffset < 0.6 && Math.abs(headYaw) < 20;

  // Classify dominant emotion from baseline-adjusted blendshapes,
  // then apply temporal smoothing to prevent flickering.
  const rawScores = classifyEmotion(adjusted);
  const emotionScores = smoothEmotionScores(rawScores);

  const dominant = Object.entries(emotionScores).reduce(
    (max, [k, v]) => (v > max[1] ? [k, v] : max),
    ["neutral", 0]
  );

  return {
    timestamp: new Date().toISOString(),
    dominant_emotion: dominant[0] as string,
    emotion_scores: emotionScores,
    eye_contact: eyeContact,
    head_pitch: Math.round(headPitch * 10) / 10,
    head_yaw: Math.round(headYaw * 10) / 10,
  };
}

/**
 * Classify emotions from MediaPipe face blendshapes.
 *
 * Uses calibrated heuristics that incorporate additional action units
 * (cheekSquint for genuine smiles, lipPress for anxiety) and gate
 * activations behind meaningful thresholds so that resting faces do
 * not score high on "happy" or "confident" by default.
 *
 * Emotions: neutral, happy, confident, nervous, surprised, confused, focused.
 */
function classifyEmotion(
  shapes: Record<string, number>
): Record<string, number> {
  // Core blendshape aggregates
  const smile =
    ((shapes["mouthSmileLeft"] || 0) + (shapes["mouthSmileRight"] || 0)) / 2;
  const frown =
    ((shapes["mouthFrownLeft"] || 0) + (shapes["mouthFrownRight"] || 0)) / 2;
  const browUp =
    ((shapes["browInnerUp"] || 0) +
      (shapes["browOuterUpLeft"] || 0) +
      (shapes["browOuterUpRight"] || 0)) /
    3;
  const browDown =
    ((shapes["browDownLeft"] || 0) + (shapes["browDownRight"] || 0)) / 2;
  const jawOpen = shapes["jawOpen"] || 0;
  const eyeWide =
    ((shapes["eyeWideLeft"] || 0) + (shapes["eyeWideRight"] || 0)) / 2;

  // Additional action units for better discrimination
  const cheekSquint =
    ((shapes["cheekSquintLeft"] || 0) + (shapes["cheekSquintRight"] || 0)) / 2;
  const lipPress =
    ((shapes["mouthPressLeft"] || 0) + (shapes["mouthPressRight"] || 0)) / 2;
  const eyeSquint =
    ((shapes["eyeSquintLeft"] || 0) + (shapes["eyeSquintRight"] || 0)) / 2;
  const noseSneer =
    ((shapes["noseSneerLeft"] || 0) + (shapes["noseSneerRight"] || 0)) / 2;

  // -- happy: gate behind a deliberate smile threshold (>0.3) and
  //    incorporate cheekSquint (AU6) to distinguish genuine smiles.
  const happy =
    smile > 0.3
      ? Math.min(1, (smile - 0.3) * 1.4 + cheekSquint * 0.5)
      : 0;

  // -- confident: only scores when there is an active positive signal
  //    (smile + cheekSquint), not by subtracting negatives from 1.
  const confident = Math.min(
    1,
    smile * 0.6 + cheekSquint * 0.2 + Math.max(0, 1 - Math.abs(browUp - browDown)) * 0.2
  ) * (smile > 0.15 ? 1 : 0.2);

  // -- nervous: lip pressing is a strong anxiety indicator; also uses
  //    brow tension, frown, jaw clench, and wide eyes.
  const nervous = Math.min(
    1,
    browDown * 0.25 + frown * 0.25 + lipPress * 0.25 + jawOpen * 0.15 + eyeWide * 0.1
  );

  // -- surprised: raised brows, wide eyes, open mouth.
  const surprised = Math.min(
    1,
    browUp * 0.4 + eyeWide * 0.4 + jawOpen * 0.2
  );

  // -- confused: mixed brow signals (down + up), frown, possible nose sneer.
  const confused = Math.min(
    1,
    browDown * 0.35 + frown * 0.25 + browUp * 0.2 + noseSneer * 0.2
  );

  // -- focused: slight eye squint + slight brow engagement, minimal mouth
  //    activity. Useful in an interview context where "neutral" is actually
  //    engaged listening.
  const focused = Math.min(
    1,
    eyeSquint * 0.4 + browDown * 0.2 + Math.max(0, 0.3 - smile) * 0.4
  ) * (jawOpen < 0.1 && frown < 0.15 ? 1 : 0.3);

  // -- neutral: residual when all other emotions are inactive.
  //    Subtracts ALL scored emotions so it only wins by default.
  const neutral = Math.max(
    0,
    1 - happy - confident - nervous - surprised - confused - focused
  );

  return {
    neutral: Math.round(neutral * 100) / 100,
    happy: Math.round(happy * 100) / 100,
    confident: Math.round(confident * 100) / 100,
    nervous: Math.round(nervous * 100) / 100,
    surprised: Math.round(surprised * 100) / 100,
    confused: Math.round(confused * 100) / 100,
    focused: Math.round(focused * 100) / 100,
  };
}

/**
 * Clean up the face landmarker instance and reset all internal state.
 */
export function destroyFaceLandmarker(): void {
  if (faceLandmarker) {
    faceLandmarker.close();
    faceLandmarker = null;
  }
  isReady = false;
  lastTimestampMs = -1;
  smoothedScores = {};
  baselineShapes = null;
  calibrating = false;
}
