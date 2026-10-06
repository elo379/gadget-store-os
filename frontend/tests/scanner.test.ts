import assert from "node:assert/strict";
import { test } from "node:test";

import { isValidImei, normalizeScan, ScanNormalizationError } from "../lib/scanner";

test("IMEI scan is normalized and carries source metadata", () => {
  const result = normalizeScan("IMEI1: 490 154 203 237 518", "camera", "CODE_128", "device");
  assert.equal(result.type, "imei");
  assert.equal(result.normalizedValue, "490154203237518");
  assert.equal(result.source, "camera");
  assert.equal(result.format, "CODE_128");
  assert.ok(Number.isFinite(Date.parse(result.timestamp)));
  assert.equal(result.confidence, null);
});

test("invalid IMEI check digits fail closed", () => {
  assert.equal(isValidImei("490154203237518"), true);
  assert.throws(
    () => normalizeScan("490154203237517", "manual", null, "imei"),
    ScanNormalizationError,
  );
});

test("barcode and QR values keep the shared scan contract", () => {
  const barcode = normalizeScan(" sku-001 ", "hardware", "CODE_128", "barcode");
  assert.equal(barcode.type, "barcode");
  assert.equal(barcode.normalizedValue, "SKU-001");
  assert.equal(barcode.source, "hardware");

  const qr = normalizeScan("https://gsos.example/id/123", "camera", "QR_CODE");
  assert.equal(qr.type, "qr");
  assert.equal(qr.normalizedValue, "https://gsos.example/id/123");
});
