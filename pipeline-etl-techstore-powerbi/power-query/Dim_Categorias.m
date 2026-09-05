// ============================================================================
//  Dim_Categorias  —  Dimensión de categorías de referencia
//  Origen: Pipeline_ETL_Dataset.xlsx  ->  hoja "categorias"
//  Tabla limpia (sin duplicados ni nulos). Solo se promueven encabezados y se tipa.
//  Filas: 4
// ============================================================================
let
    Origen = Excel.Workbook(File.Contents(RutaArchivo), null, true),
    categorias_Hoja = Origen{[Item = "categorias", Kind = "Sheet"]}[Data],
    #"Encabezados promovidos" = Table.PromoteHeaders(categorias_Hoja, [PromoteAllScalars = true]),
    #"Tipos asignados" = Table.TransformColumnTypes(#"Encabezados promovidos", {
        {"id_categoria", Int64.Type},
        {"nombre_categoria", type text}
    })
in
    #"Tipos asignados"
