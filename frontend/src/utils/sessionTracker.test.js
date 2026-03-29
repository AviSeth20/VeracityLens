import { describe, test, expect, beforeEach, vi } from "vitest";
import fc from "fast-check";
import { SessionTracker, sessionTracker } from "./sessionTracker";

describe("SessionTracker Property Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  // Feature: phase-1-enhancements, Property 9: Session ID Header Presence
  test("Property 9: Session ID is always present and valid UUID v4", () => {
    fc.assert(
      fc.property(fc.constant(null), () => {
        const tracker = new SessionTracker();
        const sessionId = tracker.getSessionId();

        // Should be present
        expect(sessionId).toBeDefined();
        expect(sessionId).not.toBe("");

        // Should be valid UUID v4 format
        const uuidV4Regex =
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        expect(sessionId).toMatch(uuidV4Regex);
      }),
      { numRuns: 100 },
    );
  });

  // Feature: phase-1-enhancements, Property 10: Session ID Round-Trip
  test("Property 10: Session ID round-trip preserves value", () => {
    fc.assert(
      fc.property(fc.uuid(), (sessionId) => {
        // Store to localStorage
        localStorage.setItem("veracitylens_session_id", sessionId);

        // Create new tracker (should retrieve from localStorage)
        const tracker = new SessionTracker();
        const retrieved = tracker.getSessionId();

        // Should match original
        expect(retrieved).toBe(sessionId);
      }),
      { numRuns: 100 },
    );
  });

  test("Property: Session ID persists across multiple retrievals", () => {
    fc.assert(
      fc.property(fc.constant(null), () => {
        const tracker = new SessionTracker();
        const firstId = tracker.getSessionId();
        const secondId = tracker.getSessionId();
        const thirdId = tracker.getSessionId();

        // All retrievals should return the same ID
        expect(firstId).toBe(secondId);
        expect(secondId).toBe(thirdId);
      }),
      { numRuns: 100 },
    );
  });

  test("Property: Reset session generates new valid UUID", () => {
    fc.assert(
      fc.property(fc.constant(null), () => {
        const tracker = new SessionTracker();
        const originalId = tracker.getSessionId();
        const newId = tracker.resetSession();

        // New ID should be different
        expect(newId).not.toBe(originalId);

        // New ID should be valid UUID v4
        const uuidV4Regex =
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        expect(newId).toMatch(uuidV4Regex);

        // Subsequent retrieval should return new ID
        expect(tracker.getSessionId()).toBe(newId);
      }),
      { numRuns: 100 },
    );
  });
});

describe("SessionTracker Unit Tests", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  test("generates valid UUID v4 on first initialization", () => {
    const tracker = new SessionTracker();
    const sessionId = tracker.getSessionId();

    // Should be valid UUID v4 format
    const uuidV4Regex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(sessionId).toMatch(uuidV4Regex);
  });

  test("persists session ID to localStorage", () => {
    const tracker = new SessionTracker();
    const sessionId = tracker.getSessionId();

    // Should be stored in localStorage
    const stored = localStorage.getItem("veracitylens_session_id");
    expect(stored).toBe(sessionId);
  });

  test("retrieves existing session ID from localStorage", () => {
    // Pre-populate localStorage
    const existingId = "12345678-1234-4234-8234-123456789abc";
    localStorage.setItem("veracitylens_session_id", existingId);

    // Create new tracker
    const tracker = new SessionTracker();
    const sessionId = tracker.getSessionId();

    // Should retrieve existing ID
    expect(sessionId).toBe(existingId);
  });

  test("handles localStorage unavailable gracefully", () => {
    // Mock localStorage to throw error
    const originalGetItem = Storage.prototype.getItem;
    const originalSetItem = Storage.prototype.setItem;

    Storage.prototype.getItem = vi.fn(() => {
      throw new Error("localStorage unavailable");
    });
    Storage.prototype.setItem = vi.fn(() => {
      throw new Error("localStorage unavailable");
    });

    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {});

    // Should still generate a session ID
    const tracker = new SessionTracker();
    const sessionId = tracker.getSessionId();

    // Should have valid UUID
    const uuidV4Regex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(sessionId).toMatch(uuidV4Regex);

    // Should have logged warning
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      "localStorage unavailable, using temporary session",
    );

    // Restore original methods
    Storage.prototype.getItem = originalGetItem;
    Storage.prototype.setItem = originalSetItem;
    consoleWarnSpy.mockRestore();
  });

  test("resetSession generates new ID and persists it", () => {
    const tracker = new SessionTracker();
    const originalId = tracker.getSessionId();

    // Reset session
    const newId = tracker.resetSession();

    // Should be different
    expect(newId).not.toBe(originalId);

    // Should be persisted
    const stored = localStorage.getItem("veracitylens_session_id");
    expect(stored).toBe(newId);

    // Subsequent calls should return new ID
    expect(tracker.getSessionId()).toBe(newId);
  });

  test("resetSession handles localStorage failure gracefully", () => {
    const tracker = new SessionTracker();
    const originalId = tracker.getSessionId();

    // Mock localStorage.setItem to fail
    const originalSetItem = Storage.prototype.setItem;
    Storage.prototype.setItem = vi.fn(() => {
      throw new Error("localStorage unavailable");
    });

    const consoleWarnSpy = vi
      .spyOn(console, "warn")
      .mockImplementation(() => {});

    // Reset should still work
    const newId = tracker.resetSession();

    // Should have new ID
    expect(newId).not.toBe(originalId);
    expect(tracker.getSessionId()).toBe(newId);

    // Should have logged warning
    expect(consoleWarnSpy).toHaveBeenCalledWith(
      "Failed to persist new session ID",
    );

    // Restore
    Storage.prototype.setItem = originalSetItem;
    consoleWarnSpy.mockRestore();
  });

  test("singleton instance is exported", () => {
    // Should be able to use singleton
    const sessionId = sessionTracker.getSessionId();
    expect(sessionId).toBeDefined();

    // Should be valid UUID
    const uuidV4Regex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(sessionId).toMatch(uuidV4Regex);
  });
});
