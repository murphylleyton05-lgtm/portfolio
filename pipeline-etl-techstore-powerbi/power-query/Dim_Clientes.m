// ============================================================================
//  Dim_Clientes  —  Dimensión de clientes de TechStore
//  Origen: Pipeline_ETL_Dataset.xlsx  ->  hoja "clientes"
//  Problemas resueltos: 1 duplicado (id_cliente) + 2 nulos (email, ciudad)
//  Filas: 12 crudas  ->  11 limpias
// ============================================================================
let
    // RutaArchivo es un parámetro de consulta; evita hardcodear la ruta absoluta
    // del .xlsx para que el pipeline no se rompa al mover el archivo de máquina.
    Origen = Excel.Workbook(File.Contents(RutaArchivo), null, true),
    clientes_Hoja = Origen{[Item = "clientes", Kind = "Sheet"]}[Data],

    // La primera fila del rango trae los nombres de columna, no datos.
    #"Encabezados promovidos" = Table.PromoteHeaders(clientes_Hoja, [PromoteAllScalars = true]),

    // Tipado explícito: id_cliente como entero (será la PK de la dimensión) y
    // fecha_registro como Date para poder relacionarla con la tabla calendario en M8.
    #"Tipos asignados" = Table.TransformColumnTypes(#"Encabezados promovidos", {
        {"id_cliente", Int64.Type},
        {"nombre_cliente", type text},
        {"email", type text},
        {"ciudad", type text},
        {"pais", type text},
        {"fecha_registro", type date},
        {"canal", type text}
    }),

    // Se eliminan duplicados SOLO por id_cliente: Dim_Clientes es una dimensión y
    // su PK debe ser única para que la relación 1:N con Fact_Ventas no genere
    // filas fantasma ni infle los importes al hacer el JOIN en el modelo.
    #"Duplicados quitados por id" = Table.Distinct(#"Tipos asignados", {"id_cliente"}),

    // Nulos NO críticos: email y ciudad no participan de ningún cálculo de negocio,
    // así que en vez de descartar el cliente (perderíamos sus ventas asociadas por
    // integridad referencial) se rellenan con "Sin dato" para conservar la fila.
    #"Nulos reemplazados" = Table.ReplaceValue(
        Table.ReplaceValue(#"Duplicados quitados por id", null, "Sin dato", Replacer.ReplaceValue, {"email"}),
        null, "Sin dato", Replacer.ReplaceValue, {"ciudad"}
    )
in
    #"Nulos reemplazados"
