import assert from "node:assert/strict";
import { test } from "node:test";

import { getOrganizationPermissionsPath, resolveActiveOrganizationId, resolveAndPersistActiveOrganizationId } from "../lib/workspace";

const memberships = [
  { organization_id: "org-first", name: "First" },
  { organization_id: "org-second", name: "Second" },
];

test("valid stored organization is selected for workspace hydration", () => {
  assert.equal(resolveActiveOrganizationId(memberships, "org-second"), "org-second");
});

test("missing or invalid stored organization falls back to first membership", () => {
  for (const storedId of [null, "org-removed"]) {
    let persisted: string | null = null;
    assert.equal(resolveAndPersistActiveOrganizationId(memberships, storedId, (id) => { persisted = id; }), "org-first");
    assert.equal(persisted, "org-first");
  }
});

test("no authenticated workspace membership leaves organization context null", () => {
  assert.equal(resolveActiveOrganizationId([], "org-old"), null);
});

test("hydrated organization scopes AppShell permission loading", () => {
  const organizationId = resolveActiveOrganizationId(memberships, null);
  assert.equal(
    getOrganizationPermissionsPath(organizationId!),
    "/organizations/org-first/my-permissions",
  );
});
