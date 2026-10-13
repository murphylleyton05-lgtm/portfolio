import { describe, expect, it } from "vitest";
import { parsePostalCode } from "./argentina";

describe("parsePostalCode", () => {
  it.each([
    ["1425", 1425],
    ["C1425ABC", 1425],
    ["c1425abc", 1425],
    [" B1636 ", 1636],
    ["5000", 5000],
  ])("acepta %s", (input, expected) => {
    expect(parsePostalCode(input)).toBe(expected);
  });

  it.each(["", "142", "14255", "AB1425", "1425ABCD", "abcd"])("rechaza %s", (input) => {
    expect(parsePostalCode(input)).toBeNull();
  });
});
