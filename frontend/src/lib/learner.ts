/**
 * Stable learner identity stored in localStorage. No auth in PR 1 -- we just
 * want a UUID that survives page reloads so the trainer can accumulate
 * progress across sessions on the same browser.
 */

const STORAGE_KEY = "trainer_learner_id";

function randomId(): string {
  return crypto.randomUUID();
}

export function getLearnerId(): string {
  if (typeof window === "undefined") {
    // Server-render path: return an empty string; the browser will hydrate
    // with the real value. Callers should guard against empty strings.
    return "";
  }
  let id = window.localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = randomId();
    window.localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

export function resetLearnerId(): string {
  if (typeof window === "undefined") return "";
  window.localStorage.removeItem(STORAGE_KEY);
  return getLearnerId();
}
