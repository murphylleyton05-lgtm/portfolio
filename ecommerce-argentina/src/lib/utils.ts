import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { siteConfig } from "@site-config";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const priceFormatter = new Intl.NumberFormat(siteConfig.locale, {
  style: "currency",
  currency: siteConfig.currency,
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

/** 24990 → "$ 24.990" */
export function formatPrice(amount: number) {
  return priceFormatter.format(amount);
}

const dateFormatter = new Intl.DateTimeFormat(siteConfig.locale, {
  dateStyle: "medium",
  timeStyle: "short",
  hourCycle: "h23",
  timeZone: siteConfig.timeZone,
});

export function formatDate(value: string | Date) {
  return dateFormatter.format(typeof value === "string" ? new Date(value) : value);
}

/** "Remera Básica Algodón" → "remera-basica-algodon" */
export function slugify(input: string) {
  return input
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

/** Normaliza texto para búsquedas sin acentos ni mayúsculas. */
export function normalizeText(input: string) {
  return input
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

/** Redondea a 2 decimales evitando errores de punto flotante. */
export function roundMoney(amount: number) {
  return Math.round((amount + Number.EPSILON) * 100) / 100;
}

export function whatsappUrl(message: string, phone: string = siteConfig.contact.whatsapp) {
  return `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
}
