/**
 * MediaPipe Face Mesh integration for in-browser facial expression tracking.
 * Runs entirely client-side via WebAssembly -- zero API cost.
 *
 * Tracks: eye contact (gaze direction), dominant emotion heuristic,
 * head pitch/yaw, and provides per-frame snapshots.
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

  // Classify dominant emotion from blendshapes
  const emotionScores = classifyEmotion(shapeMap);
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
 * Heuristic mapping -- not a trained emotion model,
 * but sufficient for eye contact and basic expression detection.
 */
function classifyEmotion(
  shapes: Record<string, number>
): Record<string, number> {
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

  const happy = Math.min(1, smile * 2);
  const confident = Math.min(1, smile * 0.5 + (1 - frown) * 0.3 + (1 - browDown) * 0.2);
  const nervous = Math.min(1, browDown * 0.4 + frown * 0.3 + jawOpen * 0.3);
  const surprised = Math.min(1, browUp * 0.4 + eyeWide * 0.4 + jawOpen * 0.2);
  const confused = Math.min(1, browDown * 0.5 + frown * 0.3 + browUp * 0.2);
  const neutral = Math.max(0, 1 - happy - nervous - surprised - confused);

  return {
    neutral: Math.round(neutral * 100) / 100,
    happy: Math.round(happy * 100) / 100,
    confident: Math.round(confident * 100) / 100,
    nervous: Math.round(nervous * 100) / 100,
    surprised: Math.round(surprised * 100) / 100,
    confused: Math.round(confused * 100) / 100,
  };
}

/**
 * Clean up the face landmarker instance.
 */
export function destroyFaceLandmarker(): void {
  if (faceLandmarker) {
    faceLandmarker.close();
    faceLandmarker = null;
  }
  isReady = false;
  lastTimestampMs = -1;
}
