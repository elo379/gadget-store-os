import "fake-indexeddb/auto";
import assert from "node:assert/strict";
import { test } from "node:test";

import { deleteEncryptedDraft, listEncryptedDrafts, saveEncryptedDraft } from "../lib/offline-drafts";

function openAtVersion(name: string, version: number): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("drafts")) db.createObjectStore("drafts", { keyPath: "id" });
      if (!db.objectStoreNames.contains("keys")) db.createObjectStore("keys", { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

test("offline drafts are encrypted, organization-scoped, recoverable, and upgrade safely", async () => {
  const legacyDb = await openAtVersion("gsos-offline-drafts-v1", 1);
  const legacyKey = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  const legacyIv = crypto.getRandomValues(new Uint8Array(12));
  const legacyCiphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: legacyIv }, legacyKey, new TextEncoder().encode('{"cart":[]}'));
  await new Promise<void>((resolve, reject) => {
    const transaction = legacyDb.transaction(["drafts", "keys"], "readwrite");
    transaction.objectStore("drafts").put({ id: "legacy-1", organizationId: "org-old", createdAt: new Date().toISOString(), iv: legacyIv.buffer, ciphertext: legacyCiphertext });
    transaction.objectStore("keys").put({ id: "aes-gcm", key: legacyKey });
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  legacyDb.close();
  assert.deepEqual(await listEncryptedDrafts("org-old").then((rows) => rows[0]?.payload), { cart: [] });
  assert.deepEqual(await listEncryptedDrafts("org-old").then((rows) => rows[0]?.payload), { cart: [] });

  const firstId = await saveEncryptedDraft("org-a", { cart: [{ productId: "p1", quantity: 2 }] });
  const sameOrganizationId = await saveEncryptedDraft("org-a", { cart: [{ productId: "p3", quantity: 1 }] });
  const secondId = await saveEncryptedDraft("org-b", { cart: [{ productId: "p2", quantity: 1 }] });
  assert.equal((await listEncryptedDrafts("org-a")).length, 2);
  assert.deepEqual(await listEncryptedDrafts("org-b").then((rows) => rows.map((row) => row.id)), [secondId]);

  const db = await openAtVersion("gsos-offline-drafts-v1", 2);
  const allRows = await new Promise<Array<{ id: string; organizationId: string; ciphertext: ArrayBuffer; iv: ArrayBuffer }>>((resolve, reject) => {
    const request = db.transaction("drafts", "readonly").objectStore("drafts").getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  const scopedRows = allRows.filter((row) => [firstId, sameOrganizationId, secondId].includes(row.id));
  assert.equal(scopedRows.length, 3);
  assert.equal(new Set(scopedRows.map((row) => Array.from(new Uint8Array(row.iv)).join(","))).size, 3);
  assert.ok(scopedRows.every((row) => !new TextDecoder().decode(row.ciphertext).includes("productId")));

  // Deletion includes the organization in its compound persistence key.
  await deleteEncryptedDraft("org-b", firstId);
  assert.equal((await listEncryptedDrafts("org-a")).length, 2);
  await deleteEncryptedDraft("org-a", firstId);
  assert.deepEqual(await listEncryptedDrafts("org-a").then((rows) => rows.map((row) => row.id)), [sameOrganizationId]);

  // A corrupt row is isolated and removed without affecting valid sibling drafts.
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction("drafts", "readwrite");
    transaction.objectStore("drafts").put({ id: "corrupt", organizationId: "org-a", createdAt: new Date().toISOString(), iv: new ArrayBuffer(12), ciphertext: new ArrayBuffer(3) });
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  assert.deepEqual(await listEncryptedDrafts("org-a").then((rows) => rows.map((row) => row.id)), [sameOrganizationId]);
  db.close();
});

test("unavailable IndexedDB and malformed organization scope fail clearly", async () => {
  const original = globalThis.indexedDB;
  Object.defineProperty(globalThis, "indexedDB", { configurable: true, value: undefined });
  await assert.rejects(listEncryptedDrafts("org-a"), /not supported/);
  Object.defineProperty(globalThis, "indexedDB", { configurable: true, value: original });
  await assert.rejects(saveEncryptedDraft("  ", {}), /organization is required/);
});
