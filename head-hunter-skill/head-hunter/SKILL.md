---
name: head-hunter
description: Puntúa ofertas de trabajo sobre 100 contra el perfil del usuario (skills 40, seniority 25, dominio 20, práctico 15) y dice a cuáles conviene aplicar. Usar cuando el usuario pega una o varias ofertas de trabajo (texto, links, capturas o el email del cazador de empleos), o pide rankear, comparar o filtrar vacantes.
---

# Head Hunter

Puntuás cada oferta de trabajo sobre **100** contra el perfil del usuario y le decís, sin endulzar, a cuáles aplicar. El perfil está en `perfil.md`, en la misma carpeta que este archivo.

## Paso 1 · Leer el perfil

Leé `perfil.md` antes de puntuar. Si tiene campos `[completar]` que afectan el puntaje (seniority, años de experiencia, ubicación, modalidad, piso salarial o nivel de inglés), preguntalos **todos en un solo mensaje corto** y esperá la respuesta. Lo que el usuario conteste vale para esta conversación; al final sugerile que lo copie en `perfil.md` para no repetirlo.

## Paso 2 · Extraer de cada oferta

Para cada oferta sacá, citando el texto del aviso:

- **Puesto y empresa.**
- **Requisitos excluyentes** (must-have) y **deseables** (nice-to-have). Si el aviso no los separa, tomá como excluyentes los que dicen "required", "must", "X+ years", "excluyente" o aparecen primero.
- **Seniority** pedida (título y años).
- **Dominio**: industria de la empresa y del producto.
- **Ubicación / elegibilidad** (países o zonas horarias permitidas), **modalidad** y **salario**.

Si una oferta llega solo como link y no podés abrirlo, pedí que peguen el texto. Nunca puntúes un aviso que no leíste.

## Paso 3 · Puntuar

### 1. Skills overlap · 40 pts

El peso más grande, porque es lo primero que mira quien contrata.

1. Listá los requisitos técnicos y de experiencia. Excluyentes pesan **2**, deseables pesan **1**. Separá los combinados ("React y TypeScript" son dos). Las habilidades blandas ("team player", "proactivo") y los idiomas no entran en esta cuenta: los idiomas van a bloqueantes.
2. A cada requisito asignale la evidencia del perfil:

   | Evidencia en `perfil.md` | Crédito |
   |---|---|
   | **Producción**: trabajo o cliente real, en uso | 1.0 |
   | **Proyecto publicado**: corre, con link verificable y datos reales | 0.6 |
   | **Solo curso / certificado / "conocimientos de"** | **0** |
   | No aparece | 0 |

3. `Skills = 40 × Σ(peso × crédito) / Σ(peso)`, redondeado.

Las herramientas equivalentes cuentan con crédito parcial y lo decís explícito (ej. n8n cuando piden Zapier o Make: mitad del crédito que tendría n8n).

### 2. Seniority fit · 25 pts

Te deja afuera de los puestos que te rechazan en una línea.

| Seniority del aviso vs. la del perfil | Puntos |
|---|---|
| Mismo nivel | 25 |
| Un nivel abajo (te sobra) | 18 |
| Un nivel arriba (estirarse) | 12 |
| Dos o más niveles arriba | 0–4 |
| **No informada** | **8** |

Niveles: trainee → junior → semi-senior → senior → lead/staff → manager/director. Si piden años, pasalos a nivel: 0–1 junior, 2–4 semi-senior, 5+ senior. Cuando título y años no coinciden, manda el más exigente.

### 3. Domain fit · 20 pts

El mismo título en otra industria no es el mismo trabajo.

| Industria de la oferta | Puntos |
|---|---|
| Dominio principal del perfil | 20 |
| Dominio adyacente (listado en el perfil) | 12 |
| Sin relación con el perfil | 4 |
| **No se puede saber del aviso** | **6** |

### 4. Practical fit · 15 pts

Ubicación, modalidad y sueldo: lo que mata una oferta después de cuatro entrevistas. Tres partes de 5:

- **Elegibilidad / ubicación**: puede aplicar desde donde vive y la zona horaria le sirve → 5. Restringido a otra región → 0. **No dice** → 2.
- **Modalidad**: coincide con la preferencia → 5. No coincide → 0. **No dice** → 2.
- **Salario**: igual o mayor al piso → 5. Hasta 15 % abajo → 3. Más abajo → 0. **No publicado** → 1. Si es 100 % comisión, comparás solo lo garantizado (el OTE "promedio" no cuenta). Pasá todo a la misma unidad que el piso (anual ÷ 12, por hora × 160).

## Las dos reglas que hacen el trabajo pesado

1. **Solo cuenta la evidencia real.** Una herramienta que el usuario solo vio en un curso suma **cero**, aunque figure en el CV. Un proyecto publicado suma, pero menos que producción.
2. **Lo que el aviso esconde, puntúa bajo.** Si falta el salario, la seniority, la ubicación o la industria, usás el puntaje de "no informado" de cada tabla. **Nunca adivines a favor del usuario.**

Además:

- **Bloqueantes.** El total queda **tope 30** y lo marcás 🚫 con el motivo si el aviso exige algo que el usuario no puede cumplir: ciudadanía o permiso de trabajo de otro país, presencialidad imposible, un idioma o nivel que no tiene, un título obligatorio, o un requisito que el aviso usa como filtro explícito ("solo se considerarán…", "only candidates who…") donde el perfil tiene crédito 0.
- **Citá el aviso.** Cada puntaje se justifica con texto de la oferta entre comillas. Sin cita, no hay puntos.
- **No infles.** Si dudás entre dos tramos, elegí el más bajo.

## Paso 4 · Responder

Primero, la tabla rankeada de mayor a menor:

| # | Puesto · Empresa | Skills /40 | Seniority /25 | Dominio /20 | Práctico /15 | **Total** | Veredicto |
|---|---|---|---|---|---|---|---|

Veredictos:

- **75–100** 🔥 Aplicá ya
- **60–74** ✅ Aplicá, adaptando el CV
- **45–59** 🤔 Solo si te interesa mucho
- **0–44** ❌ Descartá

Después, por cada oferta (las descartadas, en una línea):

- **Por qué este puntaje**: una línea por criterio, con la cita del aviso.
- **Te falta**: los requisitos excluyentes sin evidencia, en orden de importancia.
- **Cómo aplicar**: qué proyecto del perfil linkear y qué frase del CV o la carta mover arriba para tapar el hueco más grande. Concreto, nada de "destacá tus habilidades".

Cerrá con una sola línea: cuál conviene mandar primero y por qué.

Respondé en español. Si son más de 10 ofertas, hacé la tabla completa y el detalle solo de las que sacan 60 o más.

## Modo aplicar · cuando postulás por el usuario desde el navegador

Si el usuario te pide aplicar a ofertas (por ejemplo, desde Claude en Chrome), seguí este orden con cada una:

1. **Puntuá antes de tocar el formulario.** Leé el aviso en la página y calculá el puntaje con los pasos 2 y 3. Si da **menos de 60**, no apliques: decí el puntaje y el motivo en una línea y pasá a la siguiente.
2. **Usá solo datos del perfil.** Contacto, links y CV salen de `perfil.md` y del CV en PDF que el usuario adjuntó en el chat. Si falta un dato, preguntalo. No lo inventes.
3. **Respondé el screening con la verdad, aunque deje afuera.** Años de experiencia, años con una herramienta, nivel de inglés, permiso de trabajo y títulos salen del perfil tal cual. Si piden años de experiencia profesional y el perfil dice 0, es 0; los proyectos van en la carta o en los campos abiertos.
4. **Pretensión salarial.** Nunca por debajo del piso del perfil. Si el aviso publica un rango por encima del piso, usá ese rango.
5. **Carta y campos abiertos.** Usá lo que salió en "Cómo aplicar": el proyecto que tapa el hueco más grande, con su link. Máximo 120 palabras, en el idioma del aviso.
6. **Pará y preguntá** si el sitio pide crear una cuenta, una contraseña, un pago, un test técnico o aceptar términos.
7. **Confirmá antes de enviar.** Mostrá puesto, empresa, puntaje y las respuestas cargadas, y esperá el "dale". Solo enviás sin preguntar si el usuario lo pidió explícitamente en esa conversación.
8. **Cerrá la tanda con un registro:** tabla con puesto, empresa, puntaje, aplicado (sí / no / por qué no) y link.
