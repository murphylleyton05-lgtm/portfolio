# Armar el dashboard en Tableau Public (cualquier versión) · ~30 min

Usás **`data/VacaMuerta_Tableau.xlsx`**, que abre en cualquier Tableau. Ya trae calculado el grupo de la
dona y la marca del último mes, así que hay solo **2 campos calculados**.
Así tiene que quedar: [`img/referencia_dashboard.png`](img/referencia_dashboard.png).

Colores (siempre los mismos): **azul `#1F4E79`** = dato principal · **naranja `#E8833A`** = foco (YPF, variación) · **gris `#A6B1BB`** = comparación / resto.

---

## 0 · Conectar (1 min)

1. Abrí Tableau Public → **Conectar → Microsoft Excel** → elegí `VacaMuerta_Tableau.xlsx`.
2. Arrastrá la hoja **Datos** al lienzo → abajo, clic en **Hoja 1**.

## 1 · Dos campos calculados (2 min)

*Análisis → Crear campo calculado*:

| Nombre | Fórmula |
|---|---|
| `Productividad` | `SUM([Petroleo_bbl_d]) / SUM([Pozos_activos])` |
| `Var % interanual` | `(SUM([Petroleo_bbl_d]) - SUM([Petroleo_anio_anterior_bbl_d])) / SUM([Petroleo_anio_anterior_bbl_d])` |

Clic derecho en `Var % interanual` → *Formato predeterminado de número* → **Porcentaje**, 1 decimal.

## 2 · Hoja "Eje doble" (5 min) — 20% de la nota

1. Renombrá la hoja (doble clic en la pestaña): **Eje doble**.
2. **Mes** a *Columnas* → clic derecho en la píldora → elegí **Mes** (el segundo "Mes", el de la lista de abajo: *mayo de 2015*, píldora verde).
3. **Petroleo_bbl_d** a *Filas*. Después **Petroleo_anio_anterior_bbl_d** a *Filas*, a la derecha de la anterior.
4. Arrastrá **Petroleo_anio_anterior_bbl_d** a *Filtros* → **Suma** → pestaña *Al menos* → **1** → Aceptar. Así quedan los 16 meses que tienen año anterior (sep-2024 → dic-2025).
5. Clic derecho en la 2.ª píldora de Filas → **Eje doble**.
6. Clic derecho en el eje derecho → **Sincronizar eje** ✔ → otra vez clic derecho → desmarcá **Mostrar encabezado**.
7. Tarjeta *Marcas*:
   - pestaña `SUM(Petroleo_bbl_d)` → tipo **Barra** → *Color* azul `#1F4E79`;
   - pestaña `SUM(Petroleo_anio_anterior_bbl_d)` → tipo **Línea** → *Color* gris `#A6B1BB`.
8. Título (doble clic en el título): **¿Cuánto creció el petróleo frente al mismo mes del año anterior?**

## 3 · Hoja "Dona" (6 min) — 15% de la nota

1. Hoja nueva → **Dona**. Arrastrá **Ultimo_mes** a *Filtros* → dejá solo **Si**.
2. En *Filas* escribí a mano (doble clic en el espacio vacío de Filas) `MIN(0)` y Enter. Repetilo: dos píldoras `MIN(0)`.
3. *Marcas* → pestaña de la **primera** `MIN(0)` → tipo **Circular**:
   - **Grupo_Dona** → *Color* (YPF naranja, Resto gris, el resto en azules: clic en *Color → Editar colores*);
   - **Petroleo_bbl_d** → *Ángulo*;
   - **Grupo_Dona** → *Etiqueta*; **Petroleo_bbl_d** → *Etiqueta* → clic derecho en esa píldora → *Cálculo de tabla rápido* → **Porcentaje del total**.
4. Pestaña de la **segunda** `MIN(0)` → tipo **Circular** → sacale todo lo que tenga → *Color* **blanco** → *Tamaño* más chico → **Petroleo_bbl_d** a *Etiqueta* (va a mostrar 601.990 = total en el centro).
5. Clic derecho en la 2.ª píldora de Filas → **Eje doble**. Clic derecho en el eje → **Sincronizar eje**. Desmarcá *Mostrar encabezado* en los dos ejes.
6. Agrandá la primera torta (*Tamaño*) hasta que quede un anillo.
7. Título: **¿Quién produce el petróleo? (dic-2025)**

## 4 · Hoja "Treemap" (3 min) — 15% de la nota

1. Hoja nueva → **Treemap**. **Ultimo_mes** a *Filtros* → solo **Si**.
2. **Operador** → *Etiqueta*. **Petroleo_bbl_d** → *Tamaño*. **Productividad** → *Color* (editar colores: gris → azul).
3. Arriba a la derecha, *Mostrarme* → **Mapa de árbol** (si no quedó solo).
4. **Petroleo_bbl_d** y **Productividad** también a *Etiqueta*.
5. Título: **¿Cómo se distribuye la producción entre operadores? (dic-2025)**

## 5 · Cuatro hojas KPI (5 min)

Cada una: hoja nueva, **Ultimo_mes** a *Filtros* → solo **Si**, el campo a *Texto* en Marcas, letra grande azul.

| Hoja | Campo(s) a Texto | Tiene que mostrar |
|---|---|---|
| KPI Petróleo | `SUM(Petroleo_bbl_d)` + `Var % interanual` | 601.990 · 32,2% |
| KPI Gas | `SUM(Gas_Mm3_d)` | 50.179 |
| KPI Pozos | `SUM(Pozos_activos)` | 2.642 |
| KPI Productividad | `Productividad` | 228 |

Tip: en *Texto → …* podés editar la etiqueta: `PETRÓLEO · DIC-2025` arriba en gris, el número abajo grande.

## 6 · Dashboard (6 min) — 20% de la nota

1. *Dashboard → Nuevo dashboard*. A la izquierda: *Tamaño* → **Tamaño fijo 1200 × 820**.
2. Arrastrá un **Vertical** (Objetos) al lienzo. Todo va adentro de ese contenedor, en este orden:
   1. **Texto** con el título que concluye (grande, azul, negrita):
      **El petróleo de Vaca Muerta creció 32% en un año y YPF aporta más de la mitad**
      y debajo, chico: *dic-2025: 602 mil bbl/d vs 456 mil en dic-2024. YPF explica 56%.*
   2. Un **Horizontal** con las 4 hojas KPI. A la izquierda de cada KPI, un objeto **Imagen** con su ícono de `img/` (`icono_petroleo.png`, `icono_gas.png`, `icono_pozos.png`, `icono_productividad.png`).
   3. Un **Horizontal** con **Eje doble** (más ancho) y **Dona**.
   4. **Treemap**.
   5. **Texto** chico: *Fuente: Secretaría de Energía (datos abiertos). Elaboración: Lleyton Murphy.*
3. Ocultá los títulos de las hojas KPI (clic en la hoja → flechita → desmarcar *Título*). Borrá las leyendas que aparezcan solas.
4. Título del dashboard (*Dashboard → Mostrar título*) desmarcado: ya está el texto grande.

## 7 · Acción de filtro con reseteo (2 min) — 25% de la nota

*Dashboard → Acciones → Agregar acción → Filtrar…*

- Nombre: **Filtrar por operador**
- Hojas de origen: solo **Treemap** · Ejecutar acción al: **Seleccionar**
- Hojas de destino: **Eje doble** + las 4 **KPI** (destildá Dona y Treemap)
- **Al borrar la selección: Mostrar todos los valores** ← este es el reseteo, sin esto no suma
- Filtro: **Campos seleccionados** → Operador → Operador

Probá: clic en YPF → los KPIs muestran 334.587 y el eje doble solo YPF. Clic de nuevo en YPF → vuelve todo.

## 8 · Publicar (2 min) — 5% de la nota

*Archivo → Guardar en Tableau Public como…* → nombre `Vaca Muerta · Pre-entrega 5` → se abre el navegador → copiá el link → abrilo en **incógnito** → pegalo en la entrega.
