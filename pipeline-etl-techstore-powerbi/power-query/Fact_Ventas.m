// ============================================================================
//  Fact_Ventas  —  Tabla de hechos: transacciones de venta 2023-2024
//  Origen: Pipeline_ETL_Dataset.xlsx  ->  hoja "ventas"
//  Tabla limpia. Se enriquece con nombre_producto y categoria vía Merge.
//  Filas: 50
// ============================================================================
let
    Origen = Excel.Workbook(File.Contents(RutaArchivo), null, true),
    ventas_Hoja = Origen{[Item = "ventas", Kind = "Sheet"]}[Data],

    #"Encabezados promovidos" = Table.PromoteHeaders(ventas_Hoja, [PromoteAllScalars = true]),

    // fecha_venta como Date es CRÍTICO: sin este tipo no se puede armar la línea de
    // tiempo ni relacionar con la tabla calendario del modelo (M8). Importes -> decimal.
    #"Tipos asignados" = Table.TransformColumnTypes(#"Encabezados promovidos", {
        {"id_venta", Int64.Type},
        {"fecha_venta", type date},
        {"id_cliente", Int64.Type},
        {"id_producto", Int64.Type},
        {"cantidad", Int64.Type},
        {"precio_unitario", type number},
        {"descuento", type number},
        {"total_venta", type number},
        {"canal", type text}
    }),

    // Merge para enriquecer la tabla de hechos: Fact_Ventas trae id_producto pero no
    // su descripción. Se une contra Dim_Productos por id_producto (LeftOuter: se
    // conservan TODAS las ventas aunque algún producto faltara en la dimensión).
    #"Merge con Dim_Productos" = Table.NestedJoin(#"Tipos asignados", {"id_producto"},
        Dim_Productos, {"id_producto"}, "Dim_Productos", JoinKind.LeftOuter),

    // Del merge se expanden únicamente nombre_producto y categoria: el resto de las
    // columnas de la dimensión no se materializan en la fact para no duplicar datos
    // que ya viven (y se mantienen) en Dim_Productos.
    #"Columnas de producto expandidas" = Table.ExpandTableColumn(#"Merge con Dim_Productos",
        "Dim_Productos", {"nombre_producto", "categoria"}, {"nombre_producto", "categoria"})
in
    #"Columnas de producto expandidas"
