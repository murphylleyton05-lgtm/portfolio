export type CartItem = {
  variantId: string;
  productId: string;
  slug: string;
  name: string;
  variantName: string;
  /** Precio unitario mostrado (se recalcula en el servidor al pagar). */
  price: number;
  image: string | null;
  quantity: number;
  /** Stock conocido al agregar/refrescar (para limitar la cantidad). */
  stock: number;
};

export const MAX_QUANTITY_PER_ITEM = 99;

export function cartSubtotal(items: Pick<CartItem, "price" | "quantity">[]) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

export function cartCount(items: Pick<CartItem, "quantity">[]) {
  return items.reduce((sum, item) => sum + item.quantity, 0);
}

export function clampQuantity(quantity: number, stock: number) {
  const max = Math.min(Math.max(stock, 0), MAX_QUANTITY_PER_ITEM);
  return Math.max(0, Math.min(Math.floor(quantity), max));
}
