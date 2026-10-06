export type ScanSource = "camera" | "hardware" | "manual";
export type ScanIdentifierType = "imei" | "serial" | "barcode" | "qr" | "sku" | "unknown";
export type ScanExpectation = "imei" | "device" | "serial" | "barcode" | "sku" | "auto";
export type ScannerState =
  | "idle"
  | "requesting_permission"
  | "ready"
  | "scanning"
  | "detected"
  | "processing"
  | "success"
  | "invalid"
  | "duplicate"
  | "not_found"
  | "permission_denied"
  | "camera_unavailable"
  | "unsupported_browser"
  | "network_error"
  | "cancelled";

export type ScanResult = {
  type: ScanIdentifierType;
  format: string | null;
  rawValue: string;
  normalizedValue: string;
  confidence: number | null;
  timestamp: string;
  source: ScanSource;
};

export class ScanNormalizationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ScanNormalizationError";
  }
}

export function isValidImei(value: string): boolean {
  if (!/^\d{15}$/.test(value)) return false;
  const sum = [...value].reverse().reduce((total, char, index) => {
    let digit = Number(char);
    if (index % 2 === 1) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    return total + digit;
  }, 0);
  return sum % 10 === 0;
}

export function normalizeScan(
  rawValue: string,
  source: ScanSource,
  format: string | null = null,
  expectation: ScanExpectation = "auto",
): ScanResult {
  const raw = rawValue.trim();
  if (!raw || raw.length > 512 || /[\u0000-\u001f\u007f]/.test(raw)) {
    throw new ScanNormalizationError("The scanned value is empty or contains unsupported characters.");
  }

  const imeiMatch = raw.match(/(?:\d[ -]?){14}\d/);
  const compactImei = imeiMatch?.[0].replace(/\D/g, "") ?? "";
  let type: ScanIdentifierType;
  let normalizedValue: string;

  if (expectation === "imei" || (expectation === "device" && compactImei.length === 15)) {
    if (compactImei.length !== 15 || !isValidImei(compactImei)) {
      throw new ScanNormalizationError("Enter or scan a valid 15-digit IMEI and check digit.");
    }
    type = "imei";
    normalizedValue = compactImei;
  } else if (expectation === "serial") {
    type = "serial";
    normalizedValue = raw.replace(/\s+/g, "").toUpperCase();
  } else if (expectation === "barcode") {
    type = "barcode";
    normalizedValue = raw.replace(/\s+/g, "").toUpperCase();
  } else if (expectation === "sku") {
    type = "sku";
    normalizedValue = raw.replace(/\s+/g, "").toUpperCase();
  } else if (compactImei.length === 15 && isValidImei(compactImei)) {
    type = "imei";
    normalizedValue = compactImei;
  } else if (format?.toUpperCase().includes("QR")) {
    type = "qr";
    normalizedValue = raw;
  } else {
    type = "unknown";
    normalizedValue = raw.replace(/\s+/g, "").toUpperCase();
  }

  return {
    type,
    format,
    rawValue: raw,
    normalizedValue,
    confidence: null,
    timestamp: new Date().toISOString(),
    source,
  };
}
