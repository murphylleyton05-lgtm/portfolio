const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, PageBreak,
  ImageRun, TableOfContents
} = require('docx');
const fs = require('fs');

const SC = "/tmp/claude-0/-home-user-portfolio/4c309c01-0fb3-591e-b34d-06bb0c3dc912/scratchpad/";
const NAVY="1F3864", ACCENT="2E74B5", GREY="595959", HEADSHADE="1F3864",
      ROWSHADE="DCE6F1", WARN="C00000", GOOD="1F7A1F", CODEBG="F2F4F7";

// helpers -----------------------------------------------------------------
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing:{before:280,after:120},
  children:[new TextRun({text:t,bold:true,color:NAVY,size:30})] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing:{before:220,after:100},
  children:[new TextRun({text:t,bold:true,color:ACCENT,size:26})] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing:{before:160,after:80},
  children:[new TextRun({text:t,bold:true,color:NAVY,size:23})] });
const tr = (t,size=22,o={}) => new TextRun({text:t,size,...o});
function p(runs,opts={}){
  const ch = Array.isArray(runs)? runs : [tr(runs)];
  return new Paragraph({spacing:{after:120,line:276},children:ch,...opts});
}
function bullet(runs, level=0){
  const ch = Array.isArray(runs)? runs : [tr(runs)];
  return new Paragraph({bullet:{level},spacing:{after:60,line:270},children:ch});
}
function numbered(runs, ref){
  const ch = Array.isArray(runs)? runs : [tr(runs)];
  return new Paragraph({numbering:{reference:ref,level:0},spacing:{after:60,line:270},children:ch});
}
function codeBlock(lines){
  return lines.map((ln,i)=> new Paragraph({
    shading:{type:ShadingType.CLEAR,fill:CODEBG,color:"auto"},
    spacing:{after: i===lines.length-1?120:0, before: i===0?60:0},
    border: {
      left:{style:BorderStyle.SINGLE,size:18,color:ACCENT,space:8},
      ...(i===0?{top:{style:BorderStyle.SINGLE,size:2,color:"D9D9D9",space:4}}:{}),
      ...(i===lines.length-1?{bottom:{style:BorderStyle.SINGLE,size:2,color:"D9D9D9",space:4}}:{}),
    },
    children:[new TextRun({text:ln||" ",font:"Consolas",size:18,color:"1A1A1A"})],
  }));
}
function caption(t){
  return new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:40,after:160},
    children:[new TextRun({text:t,italics:true,size:17,color:GREY})]});
}
function cell(children,{width,shade,bold,color,align}={}){
  const paras=(Array.isArray(children)?children:[children]).map(c=>
    typeof c==="string"? new Paragraph({alignment:align||AlignmentType.LEFT,spacing:{before:40,after:40},
      children:[new TextRun({text:c,bold:!!bold,color:color||"000000",size:19})]}) : c);
  return new TableCell({width:{size:width,type:WidthType.DXA},
    shading: shade?{type:ShadingType.CLEAR,fill:shade,color:"auto"}:undefined,
    margins:{top:40,bottom:40,left:90,right:90},children:paras});
}
function makeTable(colWidths,headers,rows,{headShade=HEADSHADE,altShade=ROWSHADE}={}){
  const total=colWidths.reduce((a,b)=>a+b,0);
  const headerRow=new TableRow({tableHeader:true,children:headers.map((hd,i)=>
    cell(hd,{width:colWidths[i],shade:headShade,bold:true,color:"FFFFFF",
      align:i===0?AlignmentType.LEFT:AlignmentType.CENTER}))});
  const bodyRows=rows.map((r,ri)=> new TableRow({children:r.map((val,ci)=>
    cell(String(val),{width:colWidths[ci],shade:ri%2===1?altShade:undefined,
      bold:ci===0,align:ci===0?AlignmentType.LEFT:AlignmentType.CENTER}))}));
  return new Table({columnWidths:colWidths,width:{size:total,type:WidthType.DXA},
    borders:{top:{style:BorderStyle.SINGLE,size:2,color:"BFBFBF"},
      bottom:{style:BorderStyle.SINGLE,size:2,color:"BFBFBF"},
      left:{style:BorderStyle.SINGLE,size:2,color:"BFBFBF"},
      right:{style:BorderStyle.SINGLE,size:2,color:"BFBFBF"},
      insideHorizontal:{style:BorderStyle.SINGLE,size:2,color:"D9D9D9"},
      insideVertical:{style:BorderStyle.SINGLE,size:2,color:"D9D9D9"}},
    rows:[headerRow,...bodyRows]});
}
function image(path,w,h){
  return new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:80,after:40},
    children:[new ImageRun({type:"png",data:fs.readFileSync(path),transformation:{width:w,height:h}})]});
}
function note(runs){
  const ch=Array.isArray(runs)?runs:[tr(runs)];
  return new Paragraph({shading:{type:ShadingType.CLEAR,fill:"FFF4CE",color:"auto"},
    border:{left:{style:BorderStyle.SINGLE,size:18,color:"E0A800",space:8}},
    spacing:{before:100,after:140},children:ch});
}

const C=[];

// ===== PORTADA =====
C.push(new Paragraph({spacing:{before:1600,after:40},alignment:AlignmentType.CENTER,
  children:[tr("PROYECTO INTEGRADOR FINAL",26,{bold:true,color:GREY,allCaps:true})]}));
C.push(new Paragraph({alignment:AlignmentType.CENTER,
  border:{bottom:{style:BorderStyle.SINGLE,size:14,color:ACCENT,space:10}},spacing:{after:200},
  children:[tr("RetailPro — Análisis integral de ventas",48,{bold:true,color:NAVY})]}));
C.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{after:80},
  children:[tr("Evaluación Final · Data Analytics (SQL · Estadística · Power BI)",24,{color:GREY})]}));
C.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:400,after:40},
  children:[tr("Alumno: Murphy, Lleyton",24,{bold:true})]}));
C.push(new Paragraph({alignment:AlignmentType.CENTER,
  children:[tr("Proyecto integrador TechStore / RetailPro — dataset real (50 ventas depuradas, 2023–2024)",20,{color:GREY,italics:true})]}));

// ===== INDICE =====
C.push(new Paragraph({children:[new PageBreak()]}));
C.push(h1("Índice"));
C.push(new TableOfContents("Contenido",{hyperlink:true,headingStyleRange:"1-2"}));

// ===== INTRO / CONTEXTO =====
C.push(new Paragraph({children:[new PageBreak()]}));
C.push(h1("1. Contexto del problema (pregunta de negocio)"));
C.push(p([tr("RetailPro (comercializadora de tecnología, marca de proyecto TechStore) necesita entender el comportamiento de sus ventas para tomar decisiones de compra, precios y foco comercial. La dirección no quiere leer código: quiere respuestas rápidas y confiables. ",22)]));
C.push(p([tr("Pregunta de negocio central: ",22,{bold:true}),
  tr("¿cuánto y cómo vendemos, qué categorías y canales concentran la facturación, y cuál es el ticket realmente representativo del cliente para no tomar decisiones sobre un promedio engañoso?",22)]));
C.push(h3("Preguntas de investigación estadística"));
C.push(bullet([tr("¿El ticket promedio representa al cliente típico o está inflado por ventas extremas? (media vs. mediana)",22)]));
C.push(bullet([tr("¿Existen valores atípicos (outliers) y son errores de datos o negocio legítimo? (método IQR)",22)]));
C.push(bullet([tr("¿Qué categorías y canales concentran la facturación y cómo evoluciona la tendencia mensual?",22)]));
C.push(p([tr("Hilo conductor: ",22,{bold:true}),tr("la misma tabla de ventas depurada en SQL alimenta el análisis estadístico y el dashboard; ningún número del panel sale de datos sin validar.",22)]));

// ===== DATASET =====
C.push(h1("2. Descripción del dataset y fuentes"));
C.push(p([tr("Fuente: base transaccional de TechStore consolidada en ",22),
  tr("Pipeline_ETL_Dataset.xlsx",22,{font:"Consolas"}),
  tr(", modelada como esquema en estrella. Contiene una tabla de hechos (ventas) y tablas de dimensión (clientes, productos, categorías). Volumen de la tabla de hechos: 50 operaciones ya depuradas.",22)]));
C.push(makeTable([2400,1500,4900],
  ["Tabla","Filas (limpias)","Rol y campos clave"],
  [["Fact_Ventas","50","Hechos: id_venta (PK), id_cliente/id_producto (FK), fecha_venta, cantidad, precio_unitario, descuento, total_venta, canal"],
   ["Dim_Clientes","11","Dimensión: id_cliente (PK), nombre, ciudad, país, canal"],
   ["Dim_Productos","12","Dimensión: id_producto (PK), nombre, categoría, precio, stock"],
   ["Dim_Categorias","4","Dimensión: id_categoria (PK), nombre_categoria"]]));
C.push(caption("Tabla 1. Fuentes de datos del proyecto RetailPro."));

// ===== EDA =====
C.push(h1("3. Análisis exploratorio de datos (EDA)"));
C.push(p([tr("Se validó estadísticamente la columna ",22),tr("total_venta",22,{font:"Consolas"}),
  tr(" (n = 50) para verificar que los KPIs sean confiables. Resultado principal: la distribución está sesgada a la derecha, por lo que la media sobreestima el ticket típico.",22)]));
C.push(makeTable([3400,2000,3400],
  ["Medida","Valor (USD)","Lectura"],
  [["Media (AVG)","528,46","Promedio aritmético"],
   ["Mediana (P50)","370,01","Ticket central / típico"],
   ["Desv. est. muestral","617,42","Dispersión alta"],
   ["Q1 / Q3","179,61 / 739,80","Rango intercuartílico"],
   ["IQR","560,19","Q3 − Q1"],
   ["Límite superior (outlier)","1.580,08","Q3 + 1,5·IQR"]]));
C.push(caption("Tabla 2. Estadísticos descriptivos de total_venta."));
C.push(p([tr("La media supera a la mediana en un 43 %. Se detectaron ",22),
  tr("4 outliers (ids 9, 22, 37, 45: 1.700 · 1.596 · 3.682 · 1.748,95)",22,{bold:true}),
  tr(": todos son ventas legítimas de productos caros (notebooks y un smartphone en cantidades de 2–4), no errores de carga. Representan el 8 % de las operaciones pero el 33 % de la facturación. ",22),
  tr("Conclusión de EDA: se reporta media y mediana juntas; el KPI de ticket promedio no debe leerse solo.",22,{bold:true})]));

// ===== SECCION 1 TEORIA =====
C.push(new Paragraph({children:[new PageBreak()]}));
C.push(h1("Sección 1 — Preguntas teóricas"));

C.push(h2("1.1 Diferencia entre datos e información"));
C.push(p([tr("Los ",22),tr("datos",22,{bold:true}),
  tr(" son hechos crudos, sin procesar ni contexto (por ejemplo, la lista de 50 valores de total_venta). La ",22),
  tr("información",22,{bold:true}),
  tr(" es el resultado de procesar, relacionar e interpretar esos datos para darles significado (por ejemplo: “el ticket típico es de $370 y el 33 % de la facturación viene de 4 ventas de alto valor”). ",22)]));
C.push(p([tr("Importa para la toma de decisiones porque un directivo no puede actuar sobre datos sueltos: necesita información que responda “¿y ahora qué hacemos?”. Un dato mal interpretado (leer solo la media de $528) lleva a una decisión equivocada; la información contextualizada (media vs. mediana) lleva a una decisión correcta.",22)]));

C.push(h2("1.2 Sublenguajes de SQL"));
C.push(makeTable([1500,2600,4700],
  ["Sublenguaje","Sentencias","Función principal"],
  [["DDL","CREATE, ALTER, DROP, TRUNCATE","Definir y modificar la estructura de la base (tablas, índices, esquemas)."],
   ["DML","SELECT, INSERT, UPDATE, DELETE","Manipular y consultar los datos dentro de las tablas."],
   ["DCL","GRANT, REVOKE","Controlar permisos y accesos de los usuarios a los objetos de la base."],
   ["TCL","COMMIT, ROLLBACK, SAVEPOINT","Gestionar transacciones para garantizar la integridad de los cambios."]]));
C.push(caption("Tabla 3. Sublenguajes de SQL. (Nota: SELECT se clasifica a veces como DQL, subconjunto de DML.)"));

C.push(h2("1.3 La IA como complemento del análisis de datos"));
C.push(p([tr("La inteligencia artificial no reemplaza al analista, lo potencia en varias etapas:",22)]));
C.push(bullet([tr("Preparación: ",22,{bold:true}),tr("detección automática de valores atípicos, imputación de nulos y sugerencias de limpieza.",22)]));
C.push(bullet([tr("Análisis predictivo: ",22,{bold:true}),tr("modelos de forecast de ventas, segmentación de clientes (clustering) o probabilidad de abandono (churn).",22)]));
C.push(bullet([tr("Lenguaje natural: ",22,{bold:true}),tr("preguntas tipo Q&A sobre el dashboard (“¿ventas de Notebooks el último trimestre?”) y generación de resúmenes narrativos automáticos de los insights.",22)]));
C.push(bullet([tr("Productividad: ",22,{bold:true}),tr("asistentes que ayudan a escribir y optimizar consultas SQL o medidas DAX.",22)]));
C.push(p([tr("En síntesis, la IA acelera lo repetitivo y descubre patrones difíciles de ver a simple vista, pero el criterio de negocio y la validación siguen siendo del analista.",22)]));

C.push(h2("1.4 Principios de storytelling con datos"));
C.push(bullet([tr("Audiencia y objetivo: ",22,{bold:true}),tr("adaptar el mensaje a quién decide (marketing, dirección) y qué acción se busca.",22)]));
C.push(bullet([tr("Un mensaje por visual: ",22,{bold:true}),tr("cada gráfico responde una pregunta; evitar sobrecargar el panel (máx. 5–7 visuales).",22)]));
C.push(bullet([tr("Gráfico adecuado al dato: ",22,{bold:true}),tr("líneas para tendencia, barras para comparar, KPIs para monitoreo.",22)]));
C.push(bullet([tr("Contexto y jerarquía visual: ",22,{bold:true}),tr("títulos narrativos que digan el hallazgo, no solo la métrica; resaltar lo importante con color.",22)]));
C.push(bullet([tr("Cierre accionable: ",22,{bold:true}),tr("terminar siempre con una recomendación (“¿y ahora qué hacemos?”).",22)]));

// ===== SECCION 2 PRACTICA =====
C.push(new Paragraph({children:[new PageBreak()]}));
C.push(h1("Sección 2 — Ejercicios prácticos"));

C.push(h2("Ejercicio 1 — Consulta SQL (ventas de los últimos 30 días)"));
C.push(p([tr("Objetivo: extraer nombre del cliente, fecha de compra y total de la venta, filtrando las ventas de los últimos 30 días (contados desde la última venta del dataset: 2024-11-08) y ordenando por fecha descendente.",22)]));
C.push(h3("Preparación de datos"));
C.push(bullet([tr("Se conservan solo las columnas relevantes: nombre del cliente (vía JOIN con clientes), fecha_venta y total_venta.",22)]));
C.push(bullet([tr("fecha_venta ya está en tipo fecha (depurada en Power Query), lo que permite el filtro por rango de 30 días.",22)]));
C.push(bullet([tr("Se eliminaron previamente duplicados y nulos en las dimensiones durante el ETL.",22)]));
C.push(h3("Consulta"));
C.push(...codeBlock([
  "SELECT",
  "    c.nombre_cliente,",
  "    v.fecha_venta,",
  "    v.total_venta",
  "FROM ventas AS v",
  "JOIN clientes AS c  ON v.id_cliente = c.id_cliente",
  "WHERE v.fecha_venta > (SELECT MAX(fecha_venta) FROM ventas) - INTERVAL '30 days'",
  "ORDER BY v.fecha_venta DESC;",
]));
C.push(p([tr("Nota de portabilidad: en SQL Server, reemplazar el filtro por ",20,{italics:true}),
  tr("WHERE v.fecha_venta > DATEADD(day, -30, (SELECT MAX(fecha_venta) FROM ventas))",20,{font:"Consolas"}),
  tr(".",20,{italics:true})]));
C.push(h3("Resultado"));
C.push(makeTable([3800,3000,2200],
  ["nombre_cliente","fecha_venta","total_venta"],
  [["Carlos Rojas","2024-11-08","758,10"],
   ["Ana Torres","2024-10-31","209,00"],
   ["Carlos Rojas","2024-10-22","399,00"]]));
C.push(caption("Tabla 4. Salida de la consulta: 3 ventas en la ventana de 30 días desde la última venta."));
C.push(h3("Captura de la ejecución"));
C.push(image(SC+"cap_sql_editor.png",640,291));
C.push(caption("Figura 2. Consulta ejecutada en el editor SQL (PostgreSQL): 3 filas recuperadas, ordenadas por fecha descendente."));
C.push(h3("Explicación"));
C.push(p([tr("Se usan dos tablas: ",22),tr("ventas",22,{font:"Consolas"}),
  tr(" (tabla de hechos, aporta fecha y monto) y ",22),tr("clientes",22,{font:"Consolas"}),
  tr(" (dimensión, aporta el nombre legible). El JOIN por id_cliente es adecuado porque es la clave que relaciona ambas entidades (1:N). La subconsulta con MAX(fecha_venta) hace el filtro robusto: siempre toma los últimos 30 días respecto de la venta más reciente del dataset, sin depender de la fecha actual del sistema. El ORDER BY DESC deja arriba la venta más nueva.",22)]));
C.push(h2("Ejercicio 2 — Modelado de datos (diagrama ER)"));
C.push(p([tr("Se modela un esquema en estrella con la tabla de hechos ",22),tr("Fact_Ventas",22,{font:"Consolas"}),
  tr(" en el centro y las dimensiones ",22),tr("Dim_Clientes",22,{font:"Consolas"}),tr(" y ",22),
  tr("Dim_Productos",22,{font:"Consolas"}),tr(" alrededor.",22)]));
C.push(image(SC+"er_diagram.png",600,341));
C.push(caption("Figura 1. Diagrama entidad-relación (esquema en estrella)."));
C.push(h3("Entidades y relaciones"));
C.push(bullet([tr("Cliente ",22,{bold:true}),tr("(id_cliente PK): quién compra. ",22)]));
C.push(bullet([tr("Producto ",22,{bold:true}),tr("(id_producto PK): qué se vende. ",22)]));
C.push(bullet([tr("Venta ",22,{bold:true}),tr("(id_venta PK; id_cliente e id_producto como FK): el hecho, con fecha, cantidad y total. ",22)]));
C.push(p([tr("Relaciones: ",22,{bold:true}),
  tr("un cliente realiza muchas ventas (1:N) y un producto aparece en muchas ventas (1:N). La tabla Venta resuelve la relación N:M entre clientes y productos, y cada fila registra una transacción con su total_venta.",22)]));

C.push(h2("Ejercicio 3 — Visualización y storytelling"));
C.push(p([tr("Escenario: presentar el informe de ventas mensual al equipo de marketing. La narrativa sigue una estructura de tres actos: contexto → hallazgo → acción.",22)]));
C.push(h3("Gráficos elegidos y por qué"));
C.push(makeTable([2900,2400,3500],
  ["Visual","Tipo de gráfico","Por qué"],
  [["Total, ticket y n.º ventas","Tarjetas KPI","Monitoreo de un vistazo."],
   ["Tendencia mensual","Gráfico de líneas","Muestra evolución/estacionalidad en el tiempo."],
   ["Ventas por categoría","Barras horizontales","Compara categorías y ordena de mayor a menor."],
   ["Ventas por canal","Dona (donut)","Muestra participación Online vs. Tienda."],
   ["Distribución del ticket","Histograma","Evidencia el sesgo: media vs. mediana."]]));
C.push(caption("Tabla 5. Selección de visuales para el informe."));
C.push(image(SC+"cap_powerbi.png",650,425));
C.push(caption("Figura 3. Dashboard de ventas RetailPro en Power BI Desktop (datos reales del proyecto)."));
C.push(h3("Narrativa (storytelling)"));
C.push(p([tr("1) Contexto: ",22,{bold:true}),
  tr("“En 2023–2024 facturamos $26.423 en 50 operaciones; el 56 % vino de canal Online.” ",22)]));
C.push(p([tr("2) Hallazgo: ",22,{bold:true}),
  tr("“Notebooks y Smartphones concentran el 73 % de la facturación. Y ojo con el ticket: el promedio ($528) engaña, porque 4 ventas de alto valor lo inflan; el cliente típico gasta $370 (mediana).” ",22)]));
C.push(p([tr("3) Acción (recomendación): ",22,{bold:true}),
  tr("“Invertir el presupuesto de marketing en Notebooks/Smartphones y en el canal Online, que es donde está la facturación; y comunicar los objetivos de venta usando la mediana como ticket de referencia, no el promedio.” ",22)]));

// ===== CONCLUSIONES =====
C.push(new Paragraph({children:[new PageBreak()]}));
C.push(h1("Conclusiones e insights"));
C.push(numbered([tr("Hilo conductor cumplido: ",22,{bold:true}),tr("los mismos datos depurados en SQL sostienen el análisis estadístico y el dashboard.",22)],"conc"));
C.push(numbered([tr("El promedio engaña: ",22,{bold:true}),tr("media $528 vs. mediana $370 (43 % de diferencia). Se comunica la mediana como ticket de referencia.",22)],"conc"));
C.push(numbered([tr("Outliers legítimos: ",22,{bold:true}),tr("4 ventas de alto valor (8 % de las operaciones, 33 % de la facturación); no se eliminan, se explican.",22)],"conc"));
C.push(numbered([tr("Foco comercial: ",22,{bold:true}),tr("Notebooks y Smartphones concentran el 73 % de las ventas; el canal Online lidera con 56 %.",22)],"conc"));
C.push(numbered([tr("Recomendación de negocio: ",22,{bold:true}),tr("priorizar inversión de marketing en las categorías y canal líderes, y fijar metas sobre la mediana.",22)],"conc"));
C.push(note([tr("Checklist antes de entregar: ",20,{bold:true}),
  tr("el documento ya incluye las capturas de la consulta SQL (Figura 2) y del dashboard (Figura 3). Si lo pasás a Google Doc, verificá que tenga acceso público/de revisión y que no haya enlaces externos: todo el análisis debe entenderse solo mirando este documento.",20)]));

// ---- render ----
const doc = new Document({
  creator:"Murphy Lleyton", title:"Evaluación Final — Proyecto Integrador RetailPro",
  features:{updateFields:true},
  numbering:{config:[{reference:"conc",levels:[{level:0,format:"decimal",text:"%1.",alignment:AlignmentType.START}]}]},
  styles:{default:{document:{run:{font:"Calibri",size:22}}}},
  sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1080,bottom:1080,left:1080,right:1080}}},children:C}],
});
Packer.toBuffer(doc).then(buf=>{
  const out=process.argv[2]||"final.docx";
  fs.writeFileSync(out,buf);
  console.log("WROTE",out,buf.length,"bytes");
});
