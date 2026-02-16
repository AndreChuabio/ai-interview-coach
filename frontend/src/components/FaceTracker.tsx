"use client";

import { useEffect, useRef, useState } from "react";
import {
  initFaceLandmarker,
  processFrame,
  destroyFaceLandmarker,
  calibrateBaseline,
  hasBaseline,
  type FaceFrame,
} from "@/lib/mediapipe";
import { Eye, EyeOff, Smile, Frown, Meh, Crosshair } from "lucide-react";

interface Props {
  /** Whether tracking is active. */
  active: boolean;
  /** Called with each batch of face frames (every ~2 seconds). */
  onFrameBatch?: (frames: FaceFrame[]) => void;
  /** Show the webcam video preview. */
  showPreview?: boolean;
}

const EMOTION_ICONS: Record<string, React.ReactNode> = {
  happy: <Smile className="w-4 h-4 text-green-500" />,
  confident: <Smile className="w-4 h-4 text-blue-500" />,
  nervous: <Frown className="w-4 h-4 text-amber-500" />,
  confused: <Frown className="w-4 h-4 text-red-400" />,
  surprised: <Meh className="w-4 h-4 text-purple-500" />,
  neutral: <Meh className="w-4 h-4 text-gray-400" />,
  focused: <Crosshair className="w-4 h-4 text-cyan-500" />,
};

export default function FaceTracker({
  active,
  onFrameBatch,
  showPreview = true,
}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameBufferRef = useRef<FaceFrame[]>([]);
  const animFrameRef = useRef<number>(0);

  const [initialized, setInitialized] = useState(false);
  const [calibrated, setCalibrated] = useState(false);
  const [calibrationStatus, setCalibrationStatus] = useState<
    "idle" | "running" | "done"
  >("idle");
  const [currentFrame, setCurrentFrame] = useState<FaceFrame | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize webcam and MediaPipe
  useEffect(() => {
    if (!active) return;

    let cancelled = false;

    async function setup() {
      try {
        // Start webcam
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: 320, height: 240 },
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }

        // Initialize MediaPipe
        await initFaceLandmarker();
        if (cancelled) return;
        setInitialized(true);

        // Run resting-face calibration automatically
        if (videoRef.current && !hasBaseline()) {
          setCalibrationStatus("running");
          await calibrateBaseline(videoRef.current, 30);
          if (!cancelled) {
            setCalibrated(true);
            setCalibrationStatus("done");
          }
        } else {
          setCalibrated(true);
          setCalibrationStatus("done");
        }
      } catch (err) {
        if (!cancelled) {
          setError("Webcam or MediaPipe initialization failed");
          console.error(err);
        }
      }
    }

    setup();

    return () => {
      cancelled = true;
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [active]);

  // Run face detection loop after calibration completes
  useEffect(() => {
    if (!active || !initialized || !calibrated) return;

    let lastBatchTime = Date.now();

    function detect() {
      if (!videoRef.current || videoRef.current.readyState < 2) {
        animFrameRef.current = requestAnimationFrame(detect);
        return;
      }

      const frame = processFrame(videoRef.current, performance.now());
      if (frame) {
        setCurrentFrame(frame);
        frameBufferRef.current.push(frame);

        // Send batch every 2 seconds
        const now = Date.now();
        if (now - lastBatchTime >= 2000 && frameBufferRef.current.length > 0) {
          onFrameBatch?.(frameBufferRef.current);
          frameBufferRef.current = [];
          lastBatchTime = now;
        }
      }

      animFrameRef.current = requestAnimationFrame(detect);
    }

    animFrameRef.current = requestAnimationFrame(detect);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      // Flush remaining frames
      if (frameBufferRef.current.length > 0) {
        onFrameBatch?.(frameBufferRef.current);
        frameBufferRef.current = [];
      }
    };
  }, [active, initialized, calibrated, onFrameBatch]);

  // Cleanup MediaPipe on unmount
  useEffect(() => {
    return () => {
      destroyFaceLandmarker();
    };
  }, []);

  if (!active) return null;

  return (
    <div className="w-64 flex-shrink-0 space-y-3">
      {/* Video preview */}
      {showPreview && (
        <div className="relative rounded-xl overflow-hidden bg-black aspect-[4/3]">
          <video
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="w-full h-full object-cover mirror"
            style={{ transform: "scaleX(-1)" }}
          />
          {!initialized && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white text-xs">
              Initializing face tracking...
            </div>
          )}
          {initialized && calibrationStatus === "running" && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white text-xs text-center px-3">
              <div>
                <div className="font-medium mb-1">Calibrating</div>
                <div className="text-gray-300">
                  Look at the camera with a relaxed expression...
                </div>
              </div>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-red-300 text-xs p-2 text-center">
              {error}
            </div>
          )}
        </div>
      )}

      {/* Real-time indicators */}
      {currentFrame && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-3 border border-gray-200 dark:border-gray-700 space-y-2">
          {/* Eye contact */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 flex items-center gap-1.5">
              {currentFrame.eye_contact ? (
                <Eye className="w-4 h-4 text-green-500" />
              ) : (
                <EyeOff className="w-4 h-4 text-red-400" />
              )}
              Eye Contact
            </span>
            <span
              className={`font-medium text-xs px-2 py-0.5 rounded-full ${
                currentFrame.eye_contact
                  ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                  : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
              }`}
            >
              {currentFrame.eye_contact ? "Good" : "Look at camera"}
            </span>
          </div>

          {/* Dominant emotion */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500 flex items-center gap-1.5">
              {EMOTION_ICONS[currentFrame.dominant_emotion] || (
                <Meh className="w-4 h-4" />
              )}
              Expression
            </span>
            <span className="font-medium text-xs text-gray-700 dark:text-gray-300 capitalize">
              {currentFrame.dominant_emotion}
            </span>
          </div>

          {/* Head position */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Head Position</span>
            <span
              className={`font-medium text-xs ${
                Math.abs(currentFrame.head_yaw) < 10 &&
                Math.abs(currentFrame.head_pitch) < 10
                  ? "text-green-600"
                  : "text-amber-600"
              }`}
            >
              {Math.abs(currentFrame.head_yaw) < 10 &&
              Math.abs(currentFrame.head_pitch) < 10
                ? "Centered"
                : "Off-center"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
