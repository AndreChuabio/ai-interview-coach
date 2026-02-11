/**
 * Audio recording helpers using the native MediaRecorder API.
 */

export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private stream: MediaStream | null = null;

  /** Request microphone permission and prepare the recorder. */
  async initialize(): Promise<void> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000,
      },
    });
  }

  /** Start recording audio. */
  start(): void {
    if (!this.stream) throw new Error("AudioRecorder not initialized");
    this.chunks = [];

    // Prefer webm/opus, fall back to whatever is available
    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";

    this.mediaRecorder = new MediaRecorder(this.stream, { mimeType });
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };
    this.mediaRecorder.start();
  }

  /** Stop recording and return the audio blob. */
  stop(): Promise<Blob> {
    return new Promise((resolve, reject) => {
      if (!this.mediaRecorder) {
        reject(new Error("No active recording"));
        return;
      }
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: this.chunks[0]?.type || "audio/webm" });
        resolve(blob);
      };
      this.mediaRecorder.onerror = (e) => reject(e);
      this.mediaRecorder.stop();
    });
  }

  /** Check if currently recording. */
  get isRecording(): boolean {
    return this.mediaRecorder?.state === "recording";
  }

  /** Release microphone resources. */
  destroy(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.mediaRecorder = null;
  }
}

/** Play an audio data URL (base64 encoded mp3/webm). */
export function playAudioUrl(dataUrl: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = new Audio(dataUrl);
    audio.onended = () => resolve();
    audio.onerror = (e) => reject(e);
    audio.play().catch(reject);
  });
}
