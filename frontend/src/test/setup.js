import { expect, afterEach, beforeEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import React from "react";

// Mock framer-motion
vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (target, prop) => {
        const Component = React.forwardRef((props, ref) =>
          React.createElement(prop, { ...props, ref }),
        );
        Component.displayName = `motion.${String(prop)}`;
        return Component;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

// Mock lucide-react icons
vi.mock("lucide-react", () => {
  const MockIcon = (props) =>
    React.createElement("svg", {
      ...props,
      "data-testid": "mock-icon",
    });

  return {
    CheckCircle: MockIcon,
    AlertTriangle: MockIcon,
    Zap: MockIcon,
    Eye: MockIcon,
    BarChart2: MockIcon,
    MessageSquare: MockIcon,
    Send: MockIcon,
    X: MockIcon,
    ThumbsUp: MockIcon,
    Lightbulb: MockIcon,
    Loader2: MockIcon,
    Brain: MockIcon,
    ChevronDown: MockIcon,
    ChevronUp: MockIcon,
    Moon: MockIcon,
    Sun: MockIcon,
    Clock: MockIcon,
    TrendingUp: MockIcon,
  };
});

// Mock matchMedia for theme tests
beforeEach(() => {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

// Cleanup after each test
afterEach(() => {
  cleanup();
});
