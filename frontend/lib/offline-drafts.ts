type EncryptedDraft = {
  id: string;
  organizationId: string;
  createdAt: string;
  iv: ArrayBuffer;
  ciphertext: ArrayBuffer;
  legacy?: boolean;
};
type DraftValue = { id: string; organizationId: string; createdAt: string; payload: unknown };

const DATABASE = "gsos-offline-drafts-v1";
const DATABASE_VERSION = 2;
const LEGACY_KEY_ID = "aes-gcm";

function requireBrowserCrypto(): void {
  if (!globalThis.indexedDB || !globalThis.crypto?.subtle) {
    throw new Error("Encrypted offline storage is not supported by this browser.");
  }
}

function requireOrganization(organizationId: string): void {
  if (!organizationId || !organizationId.trim()) throw new Error("An organization is required for offline drafts.");
}

function openDatabase(): Promise<IDBDatabase> {
  requireBrowserCrypto();
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE, DATABASE_VERSION);
    let wasBlocked = false;
    request.onupgradeneeded = (event) => {
      const db = request.result;
      const transaction = request.transaction;
      if (!transaction) return;

      if (event.oldVersion < 1) db.createObjectStore("drafts", { keyPath: ["organizationId", "id"] });
      if (event.oldVersion === 1) {
        // Preserve v1 encrypted rows for lazy, organization-specific re-encryption.
        const oldStore = transaction.objectStore("drafts");
        const rowsRequest = oldStore.getAll();
        rowsRequest.onsuccess = () => {
          const rows = rowsRequest.result as EncryptedDraft[];
          db.deleteObjectStore("drafts");
          const drafts = db.createObjectStore("drafts", { keyPath: ["organizationId", "id"] });
          drafts.createIndex("byOrganization", "organizationId", { unique: false });
          for (const row of rows) {
            if (row?.id && row.organizationId && row.iv && row.ciphertext) drafts.put({ ...row, legacy: true });
          }
        };
      } else {
        const drafts = transaction.objectStore("drafts");
        if (!drafts.indexNames.contains("byOrganization")) {
          drafts.createIndex("byOrganization", "organizationId", { unique: false });
        }
      }
      if (event.oldVersion < 1) db.createObjectStore("keys", { keyPath: "id" });
    };
    request.onblocked = () => {
      wasBlocked = true;
      reject(new Error("Offline draft storage is busy in another tab. Close other GSOS tabs and retry."));
    };
    request.onerror = () => reject(request.error ?? new Error("Offline draft storage could not be opened."));
    request.onsuccess = () => {
      const db = request.result;
      if (wasBlocked) {
        db.close();
        return;
      }
      db.onversionchange = () => db.close();
      resolve(db);
    };
  });
}

function readKey(db: IDBDatabase, id: string): Promise<CryptoKey | undefined> {
  return new Promise((resolve, reject) => {
    const request = db.transaction("keys", "readonly").objectStore("keys").get(id);
    request.onsuccess = () => resolve(request.result?.key as CryptoKey | undefined);
    request.onerror = () => reject(request.error ?? new Error("Offline encryption key could not be read."));
  });
}

async function getOrganizationKey(db: IDBDatabase, organizationId: string): Promise<CryptoKey> {
  const id = `organization:${organizationId}`;
  const existing = await readKey(db, id);
  if (existing) return existing;

  const generated = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
  try {
    await new Promise<void>((resolve, reject) => {
      const request = db.transaction("keys", "readwrite").objectStore("keys").add({ id, key: generated });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error ?? new Error("Offline encryption key could not be saved."));
    });
    return generated;
  } catch {
    // Another tab may have created the organization key after our initial read.
    const winner = await readKey(db, id);
    if (winner) return winner;
    throw new Error("Offline encryption key could not be persisted.");
  }
}

function readOrganizationDrafts(db: IDBDatabase, organizationId: string): Promise<EncryptedDraft[]> {
  return new Promise((resolve, reject) => {
    const request = db.transaction("drafts", "readonly").objectStore("drafts").index("byOrganization").getAll(organizationId);
    request.onsuccess = () => resolve(request.result as EncryptedDraft[]);
    request.onerror = () => reject(request.error ?? new Error("Offline drafts could not be read."));
  });
}

function putDraft(db: IDBDatabase, row: EncryptedDraft): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = db.transaction("drafts", "readwrite").objectStore("drafts").put(row);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error ?? new Error("Offline draft could not be saved."));
  });
}

function deleteRow(db: IDBDatabase, organizationId: string, id: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = db.transaction("drafts", "readwrite").objectStore("drafts").delete([organizationId, id]);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error ?? new Error("Offline draft could not be deleted."));
  });
}

function randomIv(): Uint8Array<ArrayBuffer> {
  return crypto.getRandomValues(new Uint8Array(new ArrayBuffer(12)));
}

export async function saveEncryptedDraft(organizationId: string, payload: unknown): Promise<string> {
  requireOrganization(organizationId);
  const db = await openDatabase();
  try {
    const serialized = JSON.stringify(payload);
    if (serialized === undefined) throw new Error("This value cannot be saved as an offline draft.");
    const key = await getOrganizationKey(db, organizationId);
    const id = crypto.randomUUID();
    const iv = randomIv();
    const ciphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, new TextEncoder().encode(serialized));
    await putDraft(db, { id, organizationId, createdAt: new Date().toISOString(), iv: iv.buffer, ciphertext });
    return id;
  } finally {
    db.close();
  }
}

export async function listEncryptedDrafts(organizationId: string): Promise<DraftValue[]> {
  requireOrganization(organizationId);
  const db = await openDatabase();
  try {
    const rows = await readOrganizationDrafts(db, organizationId);
    const key = await getOrganizationKey(db, organizationId);
    const drafts: DraftValue[] = [];
    for (const row of rows) {
      try {
        if (!(row.iv instanceof ArrayBuffer) || !(row.ciphertext instanceof ArrayBuffer)) throw new Error("Malformed encrypted draft");
        let plaintext: ArrayBuffer;
        if (row.legacy) {
          const legacyKey = await readKey(db, LEGACY_KEY_ID);
          if (!legacyKey) throw new Error("Legacy encryption key is missing");
          plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(row.iv) }, legacyKey, row.ciphertext);
          const newIv = randomIv();
          const newCiphertext = await crypto.subtle.encrypt({ name: "AES-GCM", iv: newIv }, key, plaintext);
          await putDraft(db, { ...row, iv: newIv.buffer, ciphertext: newCiphertext, legacy: undefined });
        } else {
          plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(row.iv) }, key, row.ciphertext);
        }
        const payload = JSON.parse(new TextDecoder().decode(plaintext)) as unknown;
        drafts.push({ id: row.id, organizationId, createdAt: row.createdAt, payload });
      } catch {
        // A corrupt or undecryptable row must not hide other drafts or cross tenant boundaries.
        await deleteRow(db, organizationId, row.id);
      }
    }
    return drafts.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  } finally {
    db.close();
  }
}

export async function deleteEncryptedDraft(organizationId: string, id: string): Promise<void> {
  requireOrganization(organizationId);
  if (!id) return;
  const db = await openDatabase();
  try {
    await deleteRow(db, organizationId, id);
  } finally {
    db.close();
  }
}
