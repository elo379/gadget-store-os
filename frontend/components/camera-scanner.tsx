"use client";

import { useEffect, useRef, useState } from "react";

type DetectedBarcode = { rawValue: string };
type BarcodeDetectorLike = {
  detect: (source: HTMLVideoElement) => Promise<DetectedBarcode[]>;
};
type BarcodeDetectorConstructor = new (options?: { formats?: string[] }) => BarcodeDetectorLike;

/** Native camera barcode scanning where supported, with an explicit manual fallback. */
export function CameraScanner({ onDetected }: { onDetected: (value: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const frameRef = useRef<number | null>(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState("");

  function stop() {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
  }

  useEffect(() => () => {
    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  async function start() {
    setError("");
    const Detector = (window as Window & { BarcodeDetector?: BarcodeDetectorConstructor }).BarcodeDetector;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Camera access is unavailable in this browser. Enter the code or use a connected scanner.");
      return;
    }
    if (!Detector) {
      setError("Camera barcode scanning is not supported here. Enter the code or use a connected scanner.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      streamRef.current = stream;
      const video = videoRef.current;
      if (!video) { stop(); return; }
      video.srcObject = stream;
      await video.play();
      setActive(true);
      const detector = new Detector({ formats: ["qr_code", "ean_13", "ean_8", "code_128", "code_39", "upc_a", "upc_e"] });
      let scanning = false;
      const scan = async () => {
        if (!streamRef.current) return;
        if (!scanning && video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
          scanning = true;
          try {
            const found = await detector.detect(video);
            const value = found[0]?.rawValue?.trim();
            if (value) {
              stop();
              onDetected(value);
              return;
            }
          } catch {
            stop();
            setError("The camera could not read this code. Try better lighting or enter it manually.");
            return;
          } finally { scanning = false; }
        }
        frameRef.current = requestAnimationFrame(scan);
      };
      frameRef.current = requestAnimationFrame(scan);
    } catch (cause) {
      stop();
      const name = cause instanceof DOMException ? cause.name : "";
      setError(name === "NotAllowedError"
        ? "Camera permission was denied. Allow camera access in your browser or enter the code manually."
        : "Could not start the camera. Check that it is available, then try again or enter the code manually.");
    }
  }

  return (
    <div className="mt-4 rounded-xl border border-[var(--border)] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Scan with camera</p>
          <p className="mt-1 text-xs text-[var(--muted)]">Uses your rear camera when available. Camera access requires a secure connection.</p>
        </div>
        {active
          ? <button type="button" onClick={stop} className="rounded-lg border px-3 py-2 text-sm">Stop camera</button>
          : <button type="button" onClick={() => void start()} className="rounded-lg border px-3 py-2 text-sm font-semibold">Open camera</button>}
      </div>
      <video ref={videoRef} autoPlay muted playsInline aria-label="Camera barcode preview" className={active ? "mt-4 max-h-72 w-full rounded-lg bg-black object-contain" : "hidden"} />
      {error && <p role="status" className="mt-3 text-sm text-red-700">{error}</p>}
    </div>
  );
}
