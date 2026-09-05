// ============================================================================
//  Dim_Productos  —  Dimensión de productos de TechStore
//  Origen: Pipeline_ETL_Dataset.xlsx  ->  hoja "productos"
//  Problemas resueltos: 1 duplicado (id_producto=103) + 2 nulos (precio, categoria)
//  Filas: 13 crudas  ->  12 limpias
// ============================================================================
let
    Origen = Excel.Workbook(File.Contents(RutaArchivo), null, true),
    productos_Hoja = Origen{[Item = "productos", Kind = "Sheet"]}[Data],

    #"Encabezados promovidos" = Table.PromoteHeaders(productos_Hoja, [PromoteAllScalars = true]),

    // precio y costo -> decimal (importes); stock/activo -> entero; id_producto es la PK.
    #"Tipos asignados" = Table.TransformColumnTypes(#"Encabezados promovidos", {
        {"id_producto", Int64.Type},
        {"nombre_producto", type text},
        {"categoria", type text},
        {"precio", type number},
        {"costo", type number},
        {"stock", Int64.Type},
        {"activo", Int64.Type}
    }),

    // Duplicado por id_producto (103 cargado dos veces al reintentar el alta en origen).
    // Se deduplica por la PK, no por todas las columnas, para no depender de que el
    // resto de los campos sean idénticos byte a byte.
    #"Duplicados quitados por id" = Table.Distinct(#"Tipos asignados", {"id_producto"}),

    // Nulo CRÍTICO en precio (id 107): sin precio no hay ingreso. NO se elimina la fila
    // porque Fact_Ventas referencia ese id_producto; borrarlo rompería la integridad
    // referencial del merge. Se imputa 0 como marcador visible: deja el ingreso en 0
    // (evidentemente incorrecto -> se detecta) en lugar de inventar un importe plausible
    // que contaminaría los KPIs. Queda pendiente de corrección con el dueño del dato.
    #"Precio nulo imputado" = Table.ReplaceValue(#"Duplicados quitados por id",
        null, 0, Replacer.ReplaceValue, {"precio"}),

    // Nulo en categoria (id 111): se etiqueta "Sin Categoria" en vez de eliminar o
    // adivinar la categoría, para que el producto siga apareciendo en los cortes por
    // categoría de forma explícita y auditable.
    #"Categoria nula etiquetada" = Table.ReplaceValue(#"Precio nulo imputado",
        null, "Sin Categoria", Replacer.ReplaceValue, {"categoria"})
in
    #"Categoria nula etiquetada"
