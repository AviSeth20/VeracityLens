import { describe, test, expect, beforeEach, vi } from "vitest";
import axios from "axios";
import { sessionTracker } from "../utils/sessionTracker";

// Mock axios
vi.mock("axios");

describe("API Client Session ID Header", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  test("adds X-Session-ID header to all requests", async () => {
    // Mock axios.create to return a mock client
    const mockClient = {
      interceptors: {
        request: {
          use: vi.fn(),
        },
      },
      post: vi.fn(),
      get: vi.fn(),
    };

    axios.create.mockReturnValue(mockClient);

    // Import api.js to trigger interceptor setup
    await import("./api.js");

    // Verify interceptor was registered
    expect(mockClient.interceptors.request.use).toHaveBeenCalled();

    // Get the interceptor function
    const interceptorFn = mockClient.interceptors.request.use.mock.calls[0][0];

    // Test the interceptor
    const config = { headers: {} };
    const result = interceptorFn(config);

    // Should add session ID header
    expect(result.headers["X-Session-ID"]).toBeDefined();
    expect(result.headers["X-Session-ID"]).toBe(sessionTracker.getSessionId());

    // Should be valid UUID v4
    const uuidV4Regex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(result.headers["X-Session-ID"]).toMatch(uuidV4Regex);
  });
});
