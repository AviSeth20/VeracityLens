import { v4 as uuidv4 } from "uuid";

const SESSION_KEY = "veracitylens_session_id";

export class SessionTracker {
  constructor() {
    this.sessionId = this.initializeSession();
  }

  initializeSession() {
    try {
      // Try to retrieve existing session
      let sessionId = localStorage.getItem(SESSION_KEY);

      if (!sessionId) {
        // Generate new UUID v4
        sessionId = uuidv4();
        localStorage.setItem(SESSION_KEY, sessionId);
      }

      return sessionId;
    } catch (error) {
      // localStorage unavailable (private browsing, etc.)
      console.warn("localStorage unavailable, using temporary session");
      return uuidv4();
    }
  }

  getSessionId() {
    return this.sessionId;
  }

  resetSession() {
    const newId = uuidv4();
    try {
      localStorage.setItem(SESSION_KEY, newId);
    } catch (error) {
      console.warn("Failed to persist new session ID");
    }
    this.sessionId = newId;
    return newId;
  }
}

// Singleton instance
export const sessionTracker = new SessionTracker();
