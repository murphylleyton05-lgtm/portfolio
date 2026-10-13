import { describe, expect, it } from "vitest";
import { parsePostalCode, provinceFromPostalCode, toWhatsAppNumber } from "./argentina";

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


describe("provinceFromPostalCode", () => {
  it("deduce la provincia de la letra del CPA", () => {
    expect(provinceFromPostalCode("C1425ABC")).toBe("Ciudad Autónoma de Buenos Aires");
    expect(provinceFromPostalCode("x5000")).toBe("Córdoba");
    expect(provinceFromPostalCode("1425")).toBeNull();
  });
});

describe("toWhatsAppNumber", () => {
  it.each([
    ["11 2345-6789", "5491123456789"],
    ["011 15 2345-6789", "5491123456789"],
    ["+54 9 11 2345-6789", "5491123456789"],
    ["(0351) 456-7890", "5493514567890"],
  ])("%s → %s", (input, expected) => {
    expect(toWhatsAppNumber(input)).toBe(expected);
  });

  it("devuelve null si no parece un número argentino", () => {
    expect(toWhatsAppNumber("123")).toBeNull();
  });
});
