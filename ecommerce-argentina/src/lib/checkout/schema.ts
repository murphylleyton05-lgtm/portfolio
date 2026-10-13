import { z } from "zod";
import { PROVINCES, parsePostalCode } from "@/lib/argentina";

const optionalText = (max: number) =>
  z
    .string()
    .trim()
    .max(max, `Máximo ${max} caracteres`)
    .optional()
    .transform((value) => (value ? value : undefined));

export const addressSchema = z.object({
  street: z.string().trim().min(2, "Ingresá la calle").max(100, "Máximo 100 caracteres"),
  number: z.string().trim().min(1, "Ingresá la altura").max(10, "Máximo 10 caracteres"),
  apartment: optionalText(30),
  city: z.string().trim().min(2, "Ingresá la localidad").max(80, "Máximo 80 caracteres"),
  province: z.enum(PROVINCES, { error: "Elegí una provincia" }),
  postalCode: z
    .string()
    .trim()
    .toUpperCase()
    .refine((value) => parsePostalCode(value) !== null, "Código postal inválido (ej: 1425 o C1425ABC)"),
});

const contactFields = {
  email: z.string().trim().toLowerCase().max(120, "Máximo 120 caracteres").pipe(z.email("Email inválido")),
  name: z.string().trim().min(3, "Ingresá tu nombre y apellido").max(100, "Máximo 100 caracteres"),
  phone: z
    .string()
    .trim()
    .regex(/^[\d\s()+-]{8,20}$/, "Teléfono inválido (ej: 11 2345-6789)"),
  dni: z
    .string()
    .trim()
    .regex(/^(\d{7,8})?$/, "DNI inválido (7 u 8 números, sin puntos)")
    .optional()
    .transform((value) => (value ? value : undefined)),
  notes: optionalText(500),
};

/**
 * Datos que completa el cliente. Con retiro en el local la dirección se ignora
 * (z.object descarta claves que no declara).
 */
export const checkoutFormSchema = z.discriminatedUnion("deliveryMethod", [
  z.object({ deliveryMethod: z.literal("shipping"), address: addressSchema, ...contactFields }),
  z.object({ deliveryMethod: z.literal("pickup"), ...contactFields }),
]);

export const cartLineSchema = z.object({
  variantId: z.uuid("Producto inválido"),
  quantity: z.int().min(1).max(99),
});

export const cartLinesSchema = z.array(cartLineSchema).min(1, "El carrito está vacío").max(50, "Demasiados productos");

/** Lo que recibe el servidor: formulario + líneas del carrito (solo ids y cantidades). */
export const placeOrderSchema = z.object({
  form: checkoutFormSchema,
  items: cartLinesSchema,
});

export type CheckoutFormInput = z.input<typeof checkoutFormSchema>;
export type CheckoutFormValues = z.output<typeof checkoutFormSchema>;
export type ShippingFormInput = Extract<CheckoutFormInput, { deliveryMethod: "shipping" }>;
export type PlaceOrderInput = z.input<typeof placeOrderSchema>;
export type ShippingAddress = z.output<typeof addressSchema>;
