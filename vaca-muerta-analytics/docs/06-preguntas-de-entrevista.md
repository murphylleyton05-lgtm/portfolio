# Cómo defender el proyecto en una entrevista

La app te consigue la conversación. Esta guía te ayuda a ganarla. Son las
preguntas que te van a hacer, con respuestas que podés sostener. **No las
memorices palabra por palabra** — entendé el porqué de cada una, para
contestar con tus palabras.

Regla de oro: **cuando no sepas algo, decilo.** "No lo sé, pero lo pensaría
así..." vale más que inventar. Un reservorista con 20 años detecta el bluff al
instante, y el bluff mata toda la credibilidad que construiste.

---

## Sobre el modelo de declinación (Arps)

**"¿Por qué Arps y no machine learning?"**
> Porque es interpretable, es el estándar de la industria, y es auditable. Con
> pocos meses de historia por pozo, un modelo complejo sobreajusta. Además una
> operadora necesita poder defender el número ante un auditor de reservas — una
> red neuronal que ajusta mejor pero que no podés explicar es peor para el
> negocio, no mejor.

**"Tenés pozos con b cerca de 2. ¿No es un sobreajuste?"**
> Sí, y es una observación correcta. b cercano a 2 con solo 24-30 meses suele
> ser un pozo que todavía está en régimen transitorio — el flujo lineal, la
> mitad de pendiente en log-log — y el hiperbólico lo sobreajusta. Por eso hago
> dos cosas: filtro los ajustes con b pegado al tope (1.98) del ranking, y marco
> en la app los pozos con poca historia. Es una limitación conocida del método,
> no un descuido. Con más tiempo, miraría modelos como Duong, que se diseñaron
> justamente para el transitorio en shale.

**"¿Por qué cortás la hiperbólica al 6% anual?"**
> Porque con b ≥ 1 la integral de Arps diverge: el EUR daría infinito. El corte
> a exponencial en la declinación terminal es la práctica estándar. El 6% está
> en el rango convencional de la industria (5-8% anual). No es un número al azar.

---

## Sobre la validación (backtest)

**"¿Cómo sé que puedo creerle a tu EUR?"**
> No te pido que me creas: te muestro la validación. Entreno el modelo con los
> primeros 24 meses de cada pozo y le pido predecir los siguientes. El pozo ya
> produjo ese período, pero el modelo no lo vio. A 36 meses, el error típico por
> pozo es ~30% y el modelo subestima sistemáticamente ~14%.

**"30% de error es mucho. ¿No invalida el modelo?"**
> Para un pozo individual, sí — y lo digo explícitamente en la app: no conviene
> usarlo para decidir sobre un pozo suelto. Pero en el agregado de cientos de
> pozos el error cae a ~9%, porque los errores individuales se compensan. Así es
> como se usa una curva tipo en la práctica: nadie invierte por el pronóstico de
> un pozo, sino de un programa de decenas. Esa distinción entre error por pozo y
> error del conjunto es el punto central de esa sección.

**"Subestima sistemáticamente. ¿Eso no es un problema?"**
> Un sesgo conocido es mejor que un error aleatorio, porque se puede corregir.
> Y tiene una lectura física: ajustar con 24 meses, con b acotado y declinación
> terminal conservadora, produce estimaciones prudentes. Es coherente con que
> 24 meses no alcanzan para fijar bien el b en shale.

---

## Sobre la normalización por rama

**"¿Por qué normalizás por longitud de rama?"**
> Porque sin eso el ranking está confundido. Un pozo de 3.000 m produce más que
> uno de 1.500 m aunque la roca sea idéntica: atraviesa el doble de reservorio.
> Al normalizar por metro, del top 10 por EUR crudo sobreviven solo 3 — el resto
> estaba arriba por geometría, no por roca.

**"Normalizás linealmente. La productividad no escala lineal con la longitud."**
> Correcto, y es una limitación que reconozco. Hay rendimientos decrecientes:
> pozos más largos no rinden el doble por interferencia intra-pozo y límites de
> fractura. Mi normalización es un primer corte, no la última palabra. Tampoco
> normalizo por libras de arena por etapa ni por spacing, que son los otros dos
> drivers de completación. Es lo que sumaría con más datos y criterio.

---

## Sobre la economía (breakeven)

**"Tu breakeven parece bajo."**
> Es un breakeven de wellhead (boca de pozo) **antes de impuestos**, y lo aclaro
> en la app. Incluye un diferencial de precio (el crudo de Neuquén cotiza con
> descuento respecto al Brent), pero no tiene impuesto a las ganancias, ni
> retenciones, ni costos de transporte y tratamiento completos. Sirve para
> comparar pozos entre sí con la misma regla, no para una decisión de inversión.
> Los supuestos son sliders en vivo justamente para que cualquiera vea la
> sensibilidad y discuta los números.

**"¿Por qué descontás el volumen?"**
> Porque un barril de dentro de diez años vale menos que uno de este mes, y en
> shale la mayor parte del volumen sale en los primeros años. Sin descontar, un
> pozo que produce lento parece igual de bueno que uno que produce rápido — y no
> lo es. Ese descuento es lo que hace no trivial el cálculo del breakeven.

---

## Sobre las ventanas de fluido

**"¿Cómo clasificás la ventana de fluido?"**
> Por el GOR de producción — cuántos m³ de gas por m³ de petróleo, sobre
> acumulados. Petróleo negro, volátil, gas y condensado. Es un proxy, no una
> tipificación PVT de laboratorio: un pozo puede subir su GOR con el tiempo por
> depletación. Pero alcanza para no mezclar ventanas al comparar, que era el
> objetivo. El 20% de los pozos resultó ser gas y condensado — no deberían
> compararse por EUR de petróleo con los demás.

---

## Las preguntas de fondo

**"¿Qué le falta a este proyecto?"** *(la más importante — respondela con seguridad)*
> Tres cosas, y las tengo identificadas:
> 1. No modela interferencia entre pozos (parent-child): cuando perforás al lado
>    de un pozo en producción, el nuevo rinde menos. Se ve en las curvas crudas.
> 2. La normalización por rama es lineal, cuando hay rendimientos decrecientes.
> 3. El modelo económico es simple: le falta el marco impositivo argentino
>    completo.
>
> Ninguna es un error del trabajo actual — son el siguiente nivel, y varias
> necesitan conocimiento de reservorios que voy a ganar en la tecnicatura.

**"¿Esto lo hiciste solo?"**
> Usé IA como herramienta, igual que usaría Stack Overflow o la documentación.
> Las decisiones metodológicas —qué modelo, cómo validar, qué limitaciones
> declarar— las entiendo y las puedo defender, que es lo que importa. [Y después
> demostralo contestando bien el resto. Esa es la única prueba que vale.]

**"¿Por qué querés entrar al sector?"**
> [Esta es tuya, no mía. Pero el proyecto ya es media respuesta: no digo que me
> interesa la energía, lo muestro con 2.400 pozos analizados.]

---

## Lo que NO tenés que hacer

- **No exageres.** No es "análisis de reservorios". Es "análisis de datos
  aplicado al sector, con DCA estándar y validación honesta". Con ese encuadre
  sos imbatible para tu nivel; con el otro, te miden con una vara que todavía no
  sostenés.
- **No defiendas lo indefendible.** Si te marcan algo real, dales la razón y
  mostrá que lo entendés. Reconocer un límite suma credibilidad; negarlo la
  destruye.
- **No memorices.** Entendé el porqué. Si entendés por qué cortás la hiperbólica,
  lo vas a poder explicar aunque te lo pregunten de una forma que no esperabas.
