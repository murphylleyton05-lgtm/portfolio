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
  const match = input.trim().toUpperCase().match(/^[A-Z]?(\d{4})[A-Z]{0,3}$/);
  return match ? Number(match[1]) : null;
}
