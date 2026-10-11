# 🎯 Head Hunter · skill de Claude que puntúa ofertas sobre 100

Pegás una o varias ofertas de trabajo y Claude te devuelve un ranking con un puntaje sobre **100** para cada una, el desglose, lo que te falta y a cuál aplicar primero.

Inspirada en la skill *Head Hunter* de Frank Andrade (@artificialcorner), adaptada en español y a mi perfil.

## Cómo puntúa

| Criterio | Puntos | Por qué pesa |
|---|---|---|
| **Skills overlap** | 40 | Es lo primero que mira quien contrata. |
| **Seniority fit** | 25 | Te deja afuera de los puestos que te rechazan en una línea. |
| **Domain fit** | 20 | El mismo título en otra industria no es el mismo trabajo. |
| **Practical fit** | 15 | Ubicación, modalidad y sueldo: lo que mata una oferta después de cuatro entrevistas. |

**Las dos reglas que hacen el trabajo pesado:**

1. **Solo cuenta la evidencia real.** Una herramienta que solo viste en un curso suma cero. Un proyecto publicado suma 0.6; producción, 1.0.
2. **Lo que el aviso esconde, puntúa bajo.** Si no dice salario o seniority, esa parte saca poco en vez de un puntaje adivinado.

Además, los bloqueantes (permiso de trabajo, idioma, filtros explícitos tipo "solo se considerarán…") dejan la oferta con **tope 30**.

| Total | Veredicto |
|---|---|
| 75–100 | 🔥 Aplicá ya |
| 60–74 | ✅ Aplicá, adaptando el CV |
| 45–59 | 🤔 Solo si te interesa mucho |
| 0–44 | ❌ Descartá |

## Archivos

```
head-hunter/
├─ SKILL.md    ← la rúbrica y el formato de respuesta
└─ perfil.md   ← tu perfil y tu evidencia, skill por skill
```

## Instalar

**En claude.ai (app o web):** comprimí la carpeta `head-hunter/` en un `.zip` y subila en *Configuración → Capacidades → Skills*.

**En Claude Code:** copiá la carpeta a `~/.claude/skills/head-hunter/`.

## Usar

```
Puntuá estas ofertas:

[pegá el texto de una o varias ofertas]
```

También sirve con el email que manda el [cazador de empleos de n8n](../cazador-empleos-n8n): te llegan las ofertas nuevas, las pegás y Head Hunter te dice a cuáles mandar el CV.

`perfil.md` ya está completo con mi CV: seniority, ubicación, modalidad, piso salarial, inglés y la evidencia de cada skill. Si algo cambia, se edita ahí.

## Mantener el perfil al día

El puntaje es tan bueno como `perfil.md`. Cuando publiques un proyecto nuevo o consigas un cliente, movés la skill de fila: de **Solo curso** a **Proyecto publicado**, o de ahí a **Producción**.

---

Hecho por **Lleyton Murphy** · Lleyton IA Automation
