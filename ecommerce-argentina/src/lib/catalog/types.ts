export type CatalogCategory = {
  id: string;
  name: string;
  slug: string;
  description: string;
  position: number;
};

export type CatalogVariant = {
  id: string;
  name: string;
  sku: string | null;
  /** Precio final de la variante (la propia o, si no tiene, la del producto). */
  price: number;
  stock: number;
  position: number;
};

export type CatalogProduct = {
  id: string;
  slug: string;
  name: string;
  description: string;
  price: number;
  compareAtPrice: number | null;
  images: string[];
  featured: boolean;
  createdAt: string;
  category: Pick<CatalogCategory, "id" | "name" | "slug"> | null;
  variants: CatalogVariant[];
  /** Precio más bajo entre variantes (para "Desde $X"). */
  minPrice: number;
  /** true si las variantes tienen precios distintos. */
  hasPriceRange: boolean;
  totalStock: number;
};

export type Catalog = {
  categories: CatalogCategory[];
  products: CatalogProduct[];
};
