# Proyecto Power BI YA ARMADO (`.pbip`) — Checkpoint 2

Este es un **proyecto de Power BI pre-construido** con TODO el checkpoint ya hecho:

- Las 5 tablas (`Dim_Clientes`, `Dim_Productos`, `Dim_Categorias`, `Fact_Ventas`)
  con los **datos embebidos** (no lee ningún Excel externo → no se cuelga al refrescar).
- `Dim_Fechas` (tabla calendario) con `Año`, `Mes Número`, `Mes Nombre`,
  `Trimestre`, `Semana`, y **marcada como tabla de fechas**.
- Las **4 relaciones** 1:N de dirección única.
- La tabla `_Medidas` con las **5 medidas DAX** (`Total Ventas`, `Ventas Online`,
  `Ventas YTD`, `Ventas LY`, `% Crecimiento Anual` con `VAR` + `DIVIDE`).
- Una página de reporte **Validación** (vacía, para arrastrar la matriz).

## Cómo convertirlo en tu `.pbix` para entregar

1. Descargá **toda** la carpeta `pbix-prearmado` (o el repo completo).
2. Abrí **Power BI Desktop** → *Archivo → Abrir* → elegí el archivo
   **`Murphy_Lleyton_Checkpoint2.pbip`**.
   - Como los datos están embebidos (son ~80 filas), abre **liviano**: no re-lee
     Excel ni hace merges. No debería colgar tu notebook como el otro camino.
   - Si Power BI te pregunta por activar el formato PBIP / TMDL, aceptá.
3. Esperá a que cargue el modelo. Vas a ver las 6 tablas en el panel derecho.
4. **Guardalo como `.pbix`:** *Archivo → Guardar como* → elegí tipo
   **Archivo de Power BI (\*.pbix)** → nombre `Murphy_Lleyton_Checkpoint2.pbix`.
5. (Opcional, 1 min) Página **Validación** → insertá una **Matriz**:
   Filas `Mes Nombre`, Columnas `Año`, Valores `Total Ventas`, `Ventas YTD`,
   `Ventas LY`, `% Crecimiento Anual`.
6. Subí el `.pbix` al repo.

## ⚠️ Si el `.pbip` no abre en tu versión de Power BI

Este proyecto se generó **sin poder probarlo en Power BI Desktop**, así que
puede que tu versión necesite un ajuste. Si no abre o da error:

- Usá el **camino manual** documentado en el
  [README del módulo](../README.md) (calendario + relaciones + medidas). Es más
  lento pero 100% seguro.
- Truco clave para que no se cuelgue tu notebook: creá la tabla `_Medidas`
  como **tabla calculada DAX** (`_Medidas = ROW("x", BLANK())`) en vez de
  *Introducir datos*. Así **no dispara el refresco de Power Query** que fue lo
  que colgó la máquina.

## Qué contiene (estructura PBIP)

```
Murphy_Lleyton_Checkpoint2.pbip          ← este es el que abrís
Murphy_Lleyton_Checkpoint2.SemanticModel/ ← el modelo (tablas, relaciones, medidas) en TMDL
Murphy_Lleyton_Checkpoint2.Report/        ← la página de reporte
```

El PBIP es el formato de proyecto de Power BI basado en texto; Power BI Desktop
lo abre igual que un `.pbix` y desde ahí lo guardás como `.pbix`.
