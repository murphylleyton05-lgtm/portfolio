import { describe, expect, it } from "vitest";
import { getDemoCatalog } from "./demo";
import { catalogHref, parseCatalogQuery, queryCatalog } from "./query";

const { products } = getDemoCatalog();

describe("parseCatalogQuery", () => {
  it("usa valores por defecto con parámetros vacíos o inválidos", () => {
    const query = parseCatalogQuery({ q: "  ", min: "abc", orden: "cualquiera", pagina: "-3", categoria: "<script>" });
    expect(query).toEqual({
      q: undefined,
      categoria: undefined,
      min: undefined,
      max: undefined,
      orden: "destacados",
      pagina: 1,
      stock: undefined,
    });
  });

  it("toma el primer valor si un parámetro viene repetido", () => {
    expect(parseCatalogQuery({ q: ["buzo", "remera"] }).q).toBe("buzo");
  });
});

describe("queryCatalog", () => {
  it("busca sin importar acentos ni mayúsculas", () => {
    const { items } = queryCatalog(products, parseCatalogQuery({ q: "ALGODON" }));
    expect(items.map((p) => p.slug)).toEqual(
      expect.arrayContaining(["remera-basica-algodon", "pack-x3-medias-de-algodon"]),
    );
  });

  it("filtra por categoría y rango de precio", () => {
    const { items } = queryCatalog(products, parseCatalogQuery({ categoria: "accesorios", max: "20000" }));
    expect(items.every((p) => p.category?.slug === "accesorios" && p.minPrice <= 20000)).toBe(true);
    expect(items.length).toBe(3);
  });

  it("ordena por precio", () => {
    const asc = queryCatalog(products, parseCatalogQuery({ orden: "menor-precio" })).items.map((p) => p.minPrice);
    expect(asc).toEqual([...asc].sort((a, b) => a - b));
  });

  it("por defecto pone primero lo que tiene stock", () => {
    const { items } = queryCatalog(products, parseCatalogQuery({}), 100);
    expect(items.at(-1)?.totalStock).toBe(0);
  });

  it("pagina y corrige páginas fuera de rango", () => {
    const result = queryCatalog(products, parseCatalogQuery({ pagina: "99" }), 5);
    expect(result.pageCount).toBe(3);
    expect(result.page).toBe(3);
    expect(result.items).toHaveLength(2);
  });

  it("'solo con stock' excluye agotados", () => {
    const { items } = queryCatalog(products, parseCatalogQuery({ stock: "1" }), 100);
    expect(items.some((p) => p.totalStock === 0)).toBe(false);
  });
});

describe("catalogHref", () => {
  it("omite valores por defecto y conserva filtros", () => {
    expect(catalogHref({ orden: "destacados", pagina: 1 })).toBe("/productos");
    expect(catalogHref({ q: "buzo", orden: "nuevos" }, { pagina: 2 })).toBe("/productos?q=buzo&orden=nuevos&pagina=2");
  });
});
