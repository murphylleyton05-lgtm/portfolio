/** Las 24 jurisdicciones de Argentina (para el formulario de envío). */
export const PROVINCES = [
  "Ciudad Autónoma de Buenos Aires",
  "Buenos Aires",
  "Catamarca",
  "Chaco",
  "Chubut",
  "Córdoba",
  "Corrientes",
  "Entre Ríos",
  "Formosa",
  "Jujuy",
  "La Pampa",
  "La Rioja",
  "Mendoza",
  "Misiones",
  "Neuquén",
  "Río Negro",
  "Salta",
  "San Juan",
  "San Luis",
  "Santa Cruz",
  "Santa Fe",
  "Santiago del Estero",
  "Tierra del Fuego",
  "Tucumán",
] as const;

export type Province = (typeof PROVINCES)[number];

/**
 * Acepta CP de 4 dígitos ("1425") o CPA ("C1425ABC") y devuelve los 4 números.
 * Devuelve null si el formato no es válido.
 */
export function parsePostalCode(input: string): number | null {
  const match = input
    .trim()
    .toUpperCase()
    .match(/^[A-Z]?(\d{4})[A-Z]{0,3}$/);
  return match ? Number(match[1]) : null;
}

/** Letra del CPA → provincia (ISO 3166-2:AR). */
const PROVINCE_BY_LETTER: Record<string, Province> = {
  A: "Salta",
  B: "Buenos Aires",
  C: "Ciudad Autónoma de Buenos Aires",
  D: "San Luis",
  E: "Entre Ríos",
  F: "La Rioja",
  G: "Santiago del Estero",
  H: "Chaco",
  J: "San Juan",
  K: "Catamarca",
  L: "La Pampa",
  M: "Mendoza",
  N: "Misiones",
  P: "Formosa",
  Q: "Neuquén",
  R: "Río Negro",
  S: "Santa Fe",
  T: "Tucumán",
  U: "Chubut",
  V: "Tierra del Fuego",
  W: "Corrientes",
  X: "Córdoba",
  Y: "Jujuy",
  Z: "Santa Cruz",
};

/** Si el CP viene en formato CPA ("C1425ABC") devuelve la provincia. */
export function provinceFromPostalCode(input: string): Province | null {
  const match = input
    .trim()
    .toUpperCase()
    .match(/^([A-Z])\d{4}[A-Z]{0,3}$/);
  return match ? (PROVINCE_BY_LETTER[match[1]] ?? null) : null;
}

/**
 * Teléfono argentino → número para wa.me (549 + característica + número).
 * Heurística simple: quita símbolos, el 0 inicial y el prefijo 15 más común.
 */
export function toWhatsAppNumber(phone: string): string | null {
  let digits = phone.replace(/\D/g, "");
  if (digits.startsWith("549")) return digits.length >= 12 ? digits : null;
  if (digits.startsWith("54")) digits = digits.slice(2);
  if (digits.startsWith("0")) digits = digits.slice(1);
  // 11 15 1234-5678 → 11 1234-5678 (celulares con 15 después del código de área de CABA/GBA)
  if (digits.length === 12 && digits.startsWith("11") && digits.slice(2, 4) === "15") digits = `11${digits.slice(4)}`;
  return digits.length === 10 ? `549${digits}` : null;
}
