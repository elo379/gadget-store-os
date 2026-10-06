"use client";

import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader } from "@zxing/browser";
import type { IScannerControls } from "@zxing/browser/esm/common/IScannerControls";
import { ApiError } from "@/lib/api";
import { normalizeScan, ScanNormalizationError, type ScanExpectation, type ScanResult, type ScannerState } from "@/lib/scanner";

/** Camera QR/barcode reader plus keyboard-wedge scanner and manual entry fallback. */
export function CameraScanner({ onDetected, expectation = "auto" }: {
  onDetected: (result: ScanResult) => void | Promise<void>;
  expectation?: ScanExpectation;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const startingRef = useRef(false);
  const mountedRef = useRef(false);
  const scanningRef = useRef(false);
  const dispatchingRef = useRef(false);
  const lastKeyAtRef = useRef(0);
  const wedgeKeysRef = useRef(0);
  const [state, setState] = useState<ScannerState>("idle");
  const [error, setError] = useState("");
  const [value, setValue] = useState("");

  function stop() {
    scanningRef.current = false;
    controlsRef.current?.stop();
    controlsRef.current = null;
    if (mountedRef.current) setState("cancelled");
  }

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      scanningRef.current = false;
      controlsRef.current?.stop();
      controlsRef.current = null;
    };
  }, []);

  async function dispatch(raw: string, source: ScanResult["source"], format: string | null = null) {
    if (dispatchingRef.current) return;
    dispatchingRef.current = true;
    setState("detected");
    try {
      const result = normalizeScan(raw, source, format, expectation);
      setState("processing");
      await onDetected(result);
      if (mountedRef.current) setState("success");
    } catch (cause) {
      if (!mountedRef.current) return;
      setState(cause instanceof ScanNormalizationError
        ? "invalid"
        : cause instanceof ApiError && cause.status === 404
          ? "not_found"
          : cause instanceof ApiError && cause.status === 409
            ? "duplicate"
          : cause instanceof ApiError && cause.status === 422
            ? "invalid"
            : cause instanceof ApiError && cause.status >= 400 && cause.status < 500
              ? "invalid"
              : "network_error");
      setError(cause instanceof Error ? cause.message : "The scanned identifier could not be processed.");
    } finally {
      dispatchingRef.current = false;
    }
  }

  async function start() {
    if (startingRef.current || state === "scanning") return;
    startingRef.current = true;
    scanningRef.current = true;
    setError("");
    setState("requesting_permission");
    if (!navigator.mediaDevices?.getUserMedia) {
      setState("unsupported_browser");
      setError("Camera access is unavailable. Use HTTPS on a supported browser, or use a connected scanner or enter the code.");
      startingRef.current = false;
      return;
    }

    try {
      const reader = new BrowserMultiFormatReader();
      let found = false;
      const controls = await reader.decodeFromConstraints(
        { audio: false, video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } } },
        videoRef.current ?? undefined,
        (result) => {
          const scanned = result?.getText().trim();
          if (!scanned || found || !scanningRef.current || !mountedRef.current) return;
          found = true;
          scanningRef.current = false;
          setValue(scanned);
          setError("");
          const format = result ? String(result.getBarcodeFormat()) : null;
          void dispatch(scanned, "camera", format);
          controlsRef.current?.stop();
          controlsRef.current = null;
        },
      );
      // The permission prompt may resolve after the dialog was closed. Stop
      // the newly acquired stream instead of leaking a camera in the background.
      if (!mountedRef.current || !scanningRef.current) {
        controls.stop();
        return;
      }
      if (found) controls.stop();
      else {
        controlsRef.current = controls;
        setState("scanning");
      }
    } catch (cause) {
      scanningRef.current = false;
      if (!mountedRef.current) return;
      const name = cause instanceof DOMException ? cause.name : "";
      setState(name === "NotAllowedError" ? "permission_denied" : name === "NotFoundError" ? "camera_unavailable" : "camera_unavailable");
      setError(name === "NotAllowedError"
        ? "Camera permission was denied. Allow camera access in browser settings, then retry, or enter the code."
        : name === "NotFoundError"
          ? "No camera was found. Connect a camera or enter the code."
          : "Could not start camera scanning. Check camera permission and HTTPS, then retry or enter the code.");
    } finally {
      startingRef.current = false;
    }
  }

  function submit() {
    const scanned = value.trim();
    if (!scanned) return;
    setError("");
    if (scanningRef.current) stop();
    const source = wedgeKeysRef.current >= 8 ? "hardware" : "manual";
    void dispatch(scanned, source);
    wedgeKeysRef.current = 0;
    setValue("");
  }

  const active = state === "scanning";
  const statusText: Partial<Record<ScannerState, string>> = {
    requesting_permission: "Requesting camera access…",
    scanning: "Camera is ready. Point it at a barcode or QR code.",
    detected: "Identifier detected.",
    processing: "Checking the identifier…",
    success: "Identifier sent to the active workflow.",
    cancelled: "Scanner closed. You can reopen it or enter the identifier.",
    unsupported_browser: "Camera scanning is unavailable here. Use a connected scanner or enter the code.",
    permission_denied: "Allow camera access in browser settings, then retry or enter the code.",
    camera_unavailable: "Could not start the camera. Check HTTPS and camera access, then retry or enter the code.",
    not_found: "No matching record was found. Check the identifier or use manual search.",
    duplicate: "This identifier is already recorded in this workflow.",
    invalid: "This identifier is invalid for the active workflow.",
    network_error: "The identifier could not be checked because the service is unavailable. Retry or continue manually.",
  };

  return (
    <div className="mt-4 space-y-3 rounded-xl border border-[var(--border)] p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Scan a QR code or barcode</p>
        <p className="mt-1 text-xs text-[var(--muted)]">Uses the rear camera when available. A connected USB/Bluetooth scanner can type into the field below.</p>
        </div>
        {active
          ? <button type="button" onClick={stop} className="min-h-11 rounded-lg border px-3 py-2 text-sm">Stop camera</button>
          : <button type="button" onClick={() => void start()} className="min-h-11 rounded-lg border px-3 py-2 text-sm font-semibold">Open camera</button>}
      </div>
      <video ref={videoRef} autoPlay muted playsInline aria-label="Live camera barcode preview" className={active ? "max-h-72 w-full rounded-lg bg-black object-contain" : "hidden"} />
      <div className="flex flex-col gap-2 sm:flex-row">
        <label className="sr-only" htmlFor="scanner-code">Barcode, IMEI or serial number</label>
        <input id="scanner-code" value={value} onChange={(event) => setValue(event.target.value)} onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            submit();
            return;
          }
          if (event.key.length !== 1 || event.ctrlKey || event.metaKey || event.altKey) return;
          const now = performance.now();
          wedgeKeysRef.current = now - lastKeyAtRef.current > 120 ? 1 : wedgeKeysRef.current + 1;
          lastKeyAtRef.current = now;
        }} placeholder="Scan with connected reader or enter code" autoComplete="off" className="min-h-11 min-w-0 flex-1 rounded-lg border px-3 text-sm" />
        <button type="button" onClick={submit} disabled={!value.trim()} className="min-h-11 rounded-lg bg-neutral-900 px-4 text-sm font-semibold text-white disabled:opacity-50">Use code</button>
      </div>
      {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
      {!error && (statusText[state] || (value ? "Code entered. Submit to use it." : "")) && <p role="status" className="text-sm text-neutral-600">{statusText[state] || "Code entered. Submit to use it."}</p>}
    </div>
  );
}
