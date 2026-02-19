/**
 * Basic sanity tests for utility functions.
 */

import { formatScore } from "@/lib/utils";

describe("formatScore", () => {
  it("returns score string when both scores are provided", () => {
    expect(formatScore(2, 1)).toBe("2–1");
  });

  it("returns vs when scores are null", () => {
    expect(formatScore(null, null)).toBe("vs");
  });
});
