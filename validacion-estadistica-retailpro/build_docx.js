const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak
} = require('docx');
const fs = require('fs');

const NAVY = "1F3864";
const ACCENT = "2E74B5";
const GREY = "595959";
const HEADSHADE = "1F3864";
const ROWSHADE = "DCE6F1";
const WARN = "C00000";

// ---- helpers -------------------------------------------------------------
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, color: NAVY, size: 30 })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, bold: true, color: ACCENT, size: 26 })],
  });
}
function p(runs, opts = {}) {
  const children = Array.isArray(runs) ? runs : [new TextRun({ text: runs, size: 22 })];
  return new Paragraph({ spacing: { after: 120, line: 276 }, children, ...opts });
}
function bullet(text, bold=false) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 60, line: 276 },
    children: [new TextRun({ text, size: 22, bold })],
  });
}
function tr(text, size = 22, opts = {}) { return new TextRun({ text, size, ...opts }); }

function cell(children, { width, shade, bold, color, align } = {}) {
  const paras = (Array.isArray(children) ? children : [children]).map(c =>
    typeof c === "string"
      ? new Paragraph({
          alignment: align || AlignmentType.LEFT,
          spacing: { before: 40, after: 40 },
          children: [new TextRun({ text: c, bold: !!bold, color: color || "000000", size: 20 })],
        })
      : c
  );
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 90, right: 90 },
    children: paras,
  });
}

function makeTable(colWidths, headers, rows, { headShade = HEADSHADE, altShade = ROWSHADE } = {}) {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((hd, i) =>
      cell(hd, { width: colWidths[i], shade: headShade, bold: true, color: "FFFFFF",
                 align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })),
  });
  const bodyRows = rows.map((r, ri) =>
    new TableRow({
      children: r.map((val, ci) =>
        cell(String(val), {
          width: colWidths[ci],
          shade: ri % 2 === 1 ? altShade : undefined,
          bold: ci === 0,
          align: ci === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
        })),
    }));
  return new Table({
    columnWidths: colWidths,
    width: { size: total, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      left: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      right: { style: BorderStyle.SINGLE, size: 2, color: "BFBFBF" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "D9D9D9" },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "D9D9D9" },
    },
    rows: [headerRow, ...bodyRows],
  });
}

// ---- document ------------------------------------------------------------
const children = [];

// Cover / title block
children.push(new Paragraph({
  spacing: { after: 40 },
  children: [tr("PROYECTO INTEGRADOR RetailPro · Módulo 10", 20, { color: GREY, bold: true, allCaps: true })],
}));
children.push(new Paragraph({
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 8 } },
  spacing: { after: 160 },
  children: [tr("Pre-entrega: Validación estadística del proyecto", 40, { bold: true, color: NAVY })],
}));
children.push(p([
  tr("Alumno: ", 22, { bold: true }), tr("Murphy, Lleyton", 22),
]));
children.push(p([
  tr("Dataset validado: ", 22, { bold: true }),
  tr("ventas.total_venta — Pipeline_ETL_Dataset.xlsx (proyecto TechStore/RetailPro, n = 50 registros)", 22),
]));
children.push(p([
  tr("Herramientas: ", 22, { bold: true }),
  tr("SQL (PERCENTILE_CONT / STDDEV_SAMP) + verificación en Python. Dispersión medida como desviación estándar muestral.", 22),
]));

// Resumen ejecutivo
children.push(h2("Resumen ejecutivo"));
children.push(p([
  tr("El caso guiado (Parte 1) muestra que dos sucursales con ", 22),
  tr("idéntica media (500 USD)", 22, { bold: true }),
  tr(" pueden tener realidades opuestas: Norte es estable (desvío 7,91) y Sur es volátil (desvío 518,41). La media, por sí sola, engaña. ", 22),
  tr("Al aplicar ese mismo criterio sobre los datos reales de RetailPro (Parte 2), la media del ticket (528,46) supera a la mediana (370,01) en un 43 %: el promedio está inflado por 4 ventas legítimas de alto valor. ", 22),
  tr("Conclusión: el KPI “Ticket Promedio” del dashboard no es representativo por sí solo y se ajusta el visual (ver sección final).", 22, { bold: true }),
]));

// =========================================================================
// PARTE 1
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Parte 1 — Consistencia de ventas (caso guiado)"));
children.push(p([
  tr("Rol: analista de una tienda de electrónica. Se comparan las ventas diarias (USD) de dos sucursales durante 5 días laborales para determinar cuál es más estable. Los cinco valores se tratan como una ", 22),
  tr("muestra", 22, { italics: true }),
  tr(" de la operación anual, por lo que la dispersión se calcula con la desviación estándar muestral (denominador n−1).", 22),
]));

children.push(h2("Datos de origen"));
children.push(makeTable(
  [2600, 1140, 1140, 1140, 1140, 1140],
  ["Sucursal", "Día 1", "Día 2", "Día 3", "Día 4", "Día 5"],
  [
    ["Norte", "500", "510", "490", "505", "495"],
    ["Sur", "100", "900", "50", "1.200", "250"],
  ]
));

children.push(h2("Medidas calculadas"));
children.push(makeTable(
  [1900, 1600, 1600, 1750, 2350],
  ["Sucursal", "Media", "Rango", "Desv. est. muestral", "Interpretación"],
  [
    ["Norte", "500,00", "20", "7,91", "Muy estable"],
    ["Sur", "500,00", "1.150", "518,41", "Muy volátil"],
  ]
));
children.push(new Paragraph({
  spacing: { before: 60, after: 120 },
  children: [tr("Detalle del cálculo (Sur): media = 2.500 / 5 = 500 · rango = 1.200 − 50 = 1.150 · varianza muestral = 1.075.000 / 4 = 268.750 · √268.750 ≈ 518,41.", 18, { italics: true, color: GREY })],
}));
children.push(new Paragraph({
  spacing: { after: 120 },
  children: [tr("Verificación SQL: STDDEV_SAMP(venta) sobre la tabla ventas_semana devuelve Norte ≈ 7,91 y Sur ≈ 518,41, coincidiendo con el cálculo manual.", 18, { italics: true, color: GREY })],
}));

children.push(h2("Conclusión (Parte 1)"));
children.push(p([
  tr("Preferiría gestionar la ", 22),
  tr("Sucursal Norte", 22, { bold: true }),
  tr(". Aunque ambas facturan lo mismo en promedio (500 USD), su desviación estándar es de solo 7,91 frente a los 518,41 de Sur: Norte es predecible y permite planificar stock, personal y caja con confianza. ", 22),
  tr("La facturación de Sur oscila entre 50 y 1.200 USD, lo que genera riesgo operativo (quiebres de stock o sobrestock) pese a la misma media. La media sin una medida de dispersión oculta el riesgo real.", 22),
]));

// =========================================================================
// PARTE 2
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(h1("Parte 2 — Validación estadística de RetailPro"));
children.push(p([
  tr("Se aplican los mismos conceptos sobre la columna ", 22),
  tr("total_venta", 22, { font: "Consolas", bold: true }),
  tr(" del dataset real del proyecto (tabla ventas, 50 registros ya depurados en el pipeline ETL). El objetivo es verificar que los KPIs del dashboard son estadísticamente confiables.", 22),
]));

children.push(h2("a) Ticket promedio real vs. representativo"));
children.push(makeTable(
  [3200, 1900, 3200],
  ["Medida", "Valor (USD)", "Lectura"],
  [
    ["Media (AVG)", "528,46", "Promedio aritmético"],
    ["Mediana (P50)", "370,01", "Valor central típico"],
    ["Diferencia media − mediana", "158,45", "Media 43 % por encima"],
  ]
));
children.push(p([
  tr("La media (528,46) y la mediana (370,01) ", 22),
  tr("no son similares: difieren en un 43 %", 22, { bold: true }),
  tr(". Cuando la media supera claramente a la mediana, la distribución está ", 22),
  tr("sesgada a la derecha (cola positiva)", 22, { bold: true }),
  tr(": unas pocas ventas muy grandes empujan el promedio hacia arriba, mientras que la mayoría de las operaciones son más chicas (la mitad de los tickets está por debajo de 370). ", 22),
]));
children.push(p([
  tr("Por lo tanto, el KPI “Ticket Promedio” del dashboard ", 22),
  tr("está inflado por ventas extremas y no representa al cliente típico", 22, { bold: true, color: WARN }),
  tr(". Un gerente que lea “528” creería que el ticket habitual ronda ese valor, cuando en realidad la mitad de las ventas no llega a 370.", 22),
]));

children.push(h2("b) Detección de outliers con el método IQR"));
children.push(makeTable(
  [3600, 2100, 2600],
  ["Estadístico", "Valor (USD)", "Fórmula"],
  [
    ["Q1 (cuartil 1)", "179,61", "PERCENTILE_CONT(0,25)"],
    ["Q3 (cuartil 3)", "739,80", "PERCENTILE_CONT(0,75)"],
    ["IQR", "560,19", "Q3 − Q1"],
    ["Límite inferior", "−660,67", "Q1 − 1,5 × IQR"],
    ["Límite superior", "1.580,08", "Q3 + 1,5 × IQR"],
  ]
));
children.push(p([
  tr("Ningún valor cae por debajo del límite inferior (no hay ventas negativas). Por encima del límite superior (1.580,08) hay ", 22),
  tr("4 registros outliers", 22, { bold: true }),
  tr(" — el 8 % de las operaciones, pero el 33 % de la facturación total:", 22),
]));
children.push(makeTable(
  [1500, 3100, 1300, 1300, 1600],
  ["id_venta", "Producto", "Cantidad", "Total (USD)", "¿Error o negocio?"],
  [
    ["37", "Notebook HP Pavilion", "4", "3.682,00", "Negocio legítimo"],
    ["9", "Notebook Lenovo IdeaPad", "2", "1.700,00", "Negocio legítimo"],
    ["45", "Notebook HP Pavilion", "2", "1.748,95", "Negocio legítimo"],
    ["22", "Samsung Galaxy A54", "4", "1.596,00", "Negocio legítimo"],
  ]
));
children.push(p([
  tr("Interpretación: los cuatro outliers son ", 22),
  tr("eventos legítimos de negocio, no errores de carga", 22, { bold: true }),
  tr(". Todos corresponden a productos de alto precio unitario (notebooks de 850–920 USD y un smartphone de 399 USD) comprados en cantidades de 2 a 4 unidades, y en cada caso se cumple precio_unitario × cantidad − descuento = total_venta. Son ventas mayoristas/de ticket alto reales: no deben eliminarse, pero sí explican por qué la media se despega de la mediana.", 22),
]));

children.push(h2("c) Conexión con el dashboard"));
children.push(p([
  tr("Los KPIs actuales del proyecto se construyen sobre ", 22),
  tr("SUM(Fact_Ventas[total_venta])", 22, { font: "Consolas" }),
  tr(" (medida ", 22),
  tr("Total Ventas", 22, { italics: true }),
  tr(", y sus derivadas Ventas Online, YTD, LY y % Crecimiento Anual). El hallazgo estadístico ", 22),
  tr("confirma un riesgo", 22, { bold: true }),
  tr(" en cualquier tarjeta que muestre un “promedio” de ticket: al estar sesgado por los 4 outliers, un único número de ticket promedio comunica mal.", 22),
]));
children.push(bullet("Se agrega un KPI de Mediana del Ticket (370) junto al de Ticket Promedio (528), para que el gerente vea ambos y entienda la dispersión.", false));
children.push(bullet("Se añade una nota aclaratoria en el visual: “Promedio influido por ventas de alto valor (4 operaciones = 33 % de la facturación).”", false));
children.push(bullet("Se ajusta el título narrativo del visual de ticket.", false));
children.push(makeTable(
  [4300, 4300],
  ["Título anterior (M7)", "Título ajustado"],
  [
    ["“Ticket Promedio: $528”", "“Ticket típico $370 (mediana) — promedio $528 elevado por ventas de alto valor”"],
  ]
));

// =========================================================================
// Sección final
children.push(h1("Ajustes aplicados al dashboard"));
children.push(p([
  tr("A partir de la validación estadística se realizaron los siguientes ajustes sobre el boceto de M7, para que los KPIs sean confiables y no induzcan a conclusiones erróneas:", 22),
]));
children.push(makeTable(
  [2600, 3200, 2800],
  ["Elemento", "Antes", "Después del hallazgo"],
  [
    ["KPI de ticket", "Solo Ticket Promedio (528)", "Ticket Promedio + Mediana del Ticket (370)"],
    ["Título narrativo", "“Ticket Promedio: $528”", "“Ticket típico $370 — promedio elevado por ventas de alto valor”"],
    ["Nota aclaratoria", "—", "4 ventas (8 %) concentran el 33 % de la facturación"],
    ["Tratamiento de outliers", "Sin revisar", "Confirmados como ventas legítimas; se conservan"],
  ]
));
children.push(p([
  tr("Cierre: ", 22, { bold: true }),
  tr("sí se ajustaron un KPI y un título narrativo. El dashboard pasa de mostrar un único promedio potencialmente engañoso a mostrar media y mediana juntas con una nota de contexto, de modo que el monitoreo rápido siga siendo honesto respecto de la distribución real de las ventas.", 22),
]));

// ---- render --------------------------------------------------------------
const doc = new Document({
  creator: "Murphy Lleyton",
  title: "Pre-entrega: Validación estadística del proyecto",
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = process.argv[2] || "output.docx";
  fs.writeFileSync(out, buf);
  console.log("WROTE", out, buf.length, "bytes");
});
