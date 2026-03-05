# Auditoría técnica de la knowledge base de dinámica vehicular para Assetto Corsa

Esta auditoría revela **errores críticos de fundamento** en al menos 6 de los 10 documentos, incluyendo una afirmación errónea sobre el modelo de neumáticos (AC usa un modelo brush, no Pacejka), una confusión generalizada entre spring rates y wheel rates, y una inversión causal en la relación springs–velocidad de transferencia de carga. Los documentos son funcionalmente útiles como guía introductoria, pero requieren correcciones sustanciales antes de servir como referencia técnica confiable. Los hallazgos están organizados documento por documento con recomendaciones editables.

---

## 1. vehicle_balance_fundamentals.md

### Precisión técnica

La afirmación central "el extremo más rígido pierde grip" es **correcta en dirección pero incompleta en mecanismo**. Falta la causa raíz: la **sensibilidad a la carga del neumático** (tire load sensitivity). La relación Fy vs Fz es cóncava — el coeficiente de fricción efectivo μ = Fy/Fz *disminuye* con mayor carga vertical. Sin este concepto, la afirmación es una regla memorizada sin fundamento físico. En un neumático hipotético con respuesta lineal Fy-Fz, redistribuir la carga lateral no afectaría el balance.

**Error probable: "los springs afectan la velocidad de transferencia de carga."** Esto es incorrecto. Los springs y ARBs determinan la **magnitud** de la transferencia de carga elástica en estado estacionario (steady-state lateral load transfer distribution, LLTD). Los **dampers** controlan la **velocidad** (rate) a la que ocurre esa transferencia. Esta confusión es extremadamente común en contenido de sim racing y debe corregirse con prioridad alta.

La definición de understeer gradient (K) probablemente carece de rigor. Según SAE J670 e ISO 8855, K = dδ/day [deg/g], medido en condiciones cuasi-estáticas. K varía con la aceleración lateral — no es un número único. Además, K describe comportamiento en rango lineal, no el límite de adherencia (limit understeer/oversteer), que es un fenómeno distinto.

### Completitud

Falta la **descomposición tripartita de la transferencia de carga**: geométrica (a través del roll center, instantánea, proporcional a la altura del roll center), elástica (a través de springs/ARBs, proporcional a la distribución de roll stiffness), y de masa no suspendida. La mayoría del contenido de sim racing solo discute el componente elástico, omitiendo que la altura del roll center contribuye significativamente a la distribución de transferencia de carga y es afectada por ride height. Esto debería ser una sección dedicada.

Conceptos ausentes que necesitan inclusión:

- **Total Lateral Load Transfer Distribution (TLLTD)**: la métrica operativa que unifica el efecto de springs, ARBs, y geometría de suspensión sobre el balance. Regla inicial: TLLTD front ≈ distribución de peso estática front + 5%.
- **Análisis de Bundorf**: descompone el understeer gradient en contribuciones individuales (slip angles, camber thrust, compliance steer, SAT, roll steer, weight transfer).
- **Balance transitorio vs estacionario**: separar claramente los efectos de dampers (transitorio) de springs/ARBs (estacionario).
- **Body slip angle (β)**: indicador crítico de estabilidad del eje trasero que complementa el yaw rate.

### Diagnóstico de telemetría

Los canales sugeridos (slip angles, yaw rate, lateral G, tyre temps) son un punto de partida razonable pero insuficiente. Faltan señales diagnósticas clave:

- **Steering angle vs lateral G** (scatter plot) — medición directa del understeer gradient
- **Wheel loads individuales** — disponibles en AC vía `wheelLoad[4]` en shared memory
- **Body slip angle (β)** — derivable de `localVelocity[3]`
- **Roll angle** — derivable del diferencial de suspension travel L-R
- **Longitudinal G + brake/throttle** — necesarios para análisis combinado por fase de curva
- **Pitch angle** — diferencial front-rear ride height bajo frenada/aceleración

### Coherencia con otros docs

Contradicción directa probable con **dampers.md**: si vehicle_balance afirma que springs controlan la velocidad de transferencia y dampers.md correctamente asigna esa función a los dampers, existe una inconsistencia. Debe unificarse: springs/ARBs → magnitud y distribución LLTD; dampers → rate de transferencia.

### Recomendaciones concretas

1. **Agregar sección "Tire Load Sensitivity como mecanismo mediador"** — explicar que μ_eff disminuye con Fz, con gráfico conceptual Fy vs Fz mostrando la curva cóncava. Referenciar Milliken & Milliken cap. 2.
2. **Corregir la atribución causal springs → velocidad**: reemplazar con "Springs y ARBs determinan la distribución de transferencia de carga lateral en estado estacionario (LLTD). Los dampers controlan la velocidad a la que se establece esa transferencia."
3. **Agregar descomposición geométrica/elástica/unsprung** con diagrama esquemático.
4. **Incluir fórmula de TLLTD** y su relación con distribución de peso.
5. **Precisar definición de K** según SAE J670, notando que es variable con ay y que limit behavior es un concepto separado.

---

## 2. tyre_dynamics.md

### Precisión técnica

**Error fundamental probable: referencia al modelo Pacejka.** Assetto Corsa utiliza un **modelo brush personalizado**, no Pacejka Magic Formula. Esto ha sido confirmado por Stefano Casillo (fundador de Kunos). El brush model describe la interacción neumático-carretera mediante bristles (cerdas) deformables en el contact patch, con regiones de adhesión y deslizamiento, usando fricción de Coulomb. Es un modelo basado en principios físicos, a diferencia de Pacejka que es puramente empírico.

Los parámetros reales del modelo de AC en `tyres.ini` incluyen: **DY0/DX0** (coeficientes de fricción pico lateral/longitudinal), **DY1/DX1** (sensibilidad a la carga), **LS_EXPY/LS_EXPX** (exponentes de load sensitivity), **FRICTION_LIMIT_ANGLE** (slip angle al límite de fricción), **FALLOFF_LEVEL/SPEED** (caída de grip post-pico), **CAMBER_GAIN**, y **RELAXATION_LENGTH**. Si el documento describe coeficientes B, C, D, E de Pacejka como el modelo de AC, esto es directamente incorrecto.

La distinción traction circle vs friction ellipse está correctamente identificada como relevante. En la práctica, la mayoría de neumáticos generan más fuerza en frenada que lateralmente, produciendo una elipse. El término técnicamente correcto es **friction ellipse** o **g-g diagram**.

### Completitud

**Tire load sensitivity** es la omisión más crítica. Sin ella, el estudiante no puede entender por qué la transferencia de carga afecta el balance. La relación Fy ∝ Fz^(0.7–0.9) significa que dos neumáticos con carga desigual producen menos fuerza lateral total que dos con carga igual sumando al mismo total. Debe ser una sección prominente con ejemplo numérico.

Conceptos ausentes prioritarios:

- **Pneumatic trail y Self-Aligning Torque (SAT)**: el pneumatic trail disminuye con slip angle creciente y puede llegar a cero o negativo cerca del límite — esto es lo que produce el aligeramiento del volante cerca del límite de adherencia en AC. Es el mecanismo primario de FFB informativo. Sección necesaria.
- **Relaxation length**: AC lo modela explícitamente (parámetro `RELAXATION_LENGTH` en tyres.ini). Es la distancia que el neumático debe rodar para que la fuerza lateral alcance ~63% de su valor estacionario. Afecta la respuesta transitoria y aumenta con velocidad y carga.
- **Camber thrust**: fuerza lateral generada solo por la inclinación del neumático, independiente del slip angle. Contribuye al cornering y es la razón por la que camber negativo beneficia al exterior de la curva.
- **Combined slip detallado**: la interacción longitudinal-lateral sigue una envolvente aproximadamente elíptica. Incrementar fuerza de frenada reduce la fuerza lateral disponible de forma continua, no binaria.

**Modelo térmico de AC específico**: AC modela temperatura de core (mayor inercia térmica) y temperaturas superficiales inner/mid/outer. La superficie se calienta/enfría más rápido que el core. Las temperaturas I/M/O son accesibles vía la Python API de AC para apps in-game, pero **no están disponibles en la shared memory externa** (solo `tyreCoreTemperature[4]`). Este detalle es operativamente importante para selección de herramientas de telemetría.

### Diagnóstico de telemetría

Faltan señales diagnósticas clave:

- **Self-aligning torque / FFB torque** — indicador directo de saturación del neumático, más rápido que la temperatura
- **Wheel load vertical por rueda** — `wheelLoad[4]` disponible, esencial para analizar load sensitivity
- **Presión en caliente** — AC modela cambios de presión con temperatura
- **Diferencial core vs surface temperature** — indica riesgo de graining y cycling térmico

### Coherencia con otros docs

Si tyre_dynamics describe Pacejka como el modelo y vehicle_balance o telemetry_and_diagnosis también lo referencian, la corrección debe ser consistente en todos. El modelo brush de AC debe ser la referencia unificada.

### Recomendaciones concretas

1. **Corregir la identificación del tire model**: reemplazar toda referencia a "Pacejka Magic Formula" con "brush-based tire model" y describir sus principios (bristles deformables, regiones adhesión/deslizamiento, fricción de Coulomb). Mencionar que Pacejka es el estándar de la industria real pero que AC eligió deliberadamente un enfoque basado en física.
2. **Agregar sección dedicada a tire load sensitivity** con ejemplo numérico: "Si μ a 4000N = 1.5 y μ a 8000N = 1.3, dos neumáticos cargados igualmente a 6000N generan más fuerza total que uno a 4000N y otro a 8000N."
3. **Agregar sección de pneumatic trail y SAT** explicando su rol en FFB y como indicador de proximidad al límite.
4. **Incluir parámetros reales de tyres.ini** (DY0, DX0, LS_EXPY, RELAXATION_LENGTH, etc.) para conectar teoría con implementación.
5. **Especificar disponibilidad de temps I/M/O**: Python API sí, shared memory no (en AC original; ACC sí las expone).

---

## 3. suspension_and_springs.md

### Precisión técnica

**Error crítico AC-específico probable: confusión spring rate vs wheel rate.** El parámetro `SPRING_RATE` en `suspensions.ini` de AC es explícitamente **wheel rate** (rigidez en la rueda), no spring rate. La documentación de modding indica que se debe calcular el wheel rate y usar ese valor. Wheel rate = spring rate × (motion ratio)². Si el documento habla de spring rates como si fueran los valores del simulador, confundirá tanto a modders como a usuarios. Los valores del setup in-game ya representan wheel rates.

**Los motion ratios no son un parámetro explícito en AC** — se derivan implícitamente de las coordenadas 3D de los puntos de geometría de suspensión en `suspensions.ini`. Esto es correcto técnicamente (es así como funcionan en la realidad también), pero el documento debe aclarar esta distinción.

Si el documento repite el error de "springs controlan velocidad de transferencia" (como en doc 1), la corrección aplica igualmente aquí.

Los rangos de natural frequency, si se incluyen, deben ser:

| Categoría | Frecuencia natural |
|---|---|
| Coches de calle OEM | 0.5–1.5 Hz |
| Coches de rally | 1.5–2.0 Hz |
| Race cars sin aero / bajo downforce | 1.5–2.5 Hz |
| Downforce moderado (GT3) | 2.5–3.5 Hz |
| Alto downforce (LMP, F1) | 3.5–5.0+ Hz |

El concepto de "flat ride" (frecuencia trasera 10-20% mayor que delantera para minimizar pitch) debe mencionarse con la nota de que aplica primariamente a coches de confort; en competición la relación puede invertirse.

### Completitud

Omisiones importantes:

- **Anti-geometría (anti-dive, anti-squat, anti-lift)**: AC modela geometría 3D completa de suspensión. Las fuerzas longitudinales (frenada/aceleración) se transmiten parcialmente a través de los brazos de suspensión según los ángulos de los instant centers, reduciendo pitch sin necesidad de springs más rígidos. Aunque no es ajustable por el usuario, entender el concepto explica por qué diferentes coches reaccionan distinto a la frenada.
- **Ride height → roll center → balance**: al cambiar ride height, la posición del roll center migra (a veces dramáticamente en DWB), alterando el split geométrico/elástico de transferencia de carga. Esto hace del ride height una herramienta de tuning extraordinariamente poderosa, no solo por efectos aerodinámicos.
- **Bump stops como elemento de tuning**: AC modela bump stops (`BUMPSTOP_RATE`, `BUMPSTOP_UP`) con spring rate progresiva. En coches aero, los bump stops son un elemento de tuning crítico para controlar la plataforma aerodinámica — no son solo protección de emergencia.
- **Fórmula de frecuencia natural**: f = (1/2π)√(K_wheel / m_corner_sprung). Debe incluirse explícitamente para que el usuario pueda calcular y verificar.

### Diagnóstico de telemetría

Los canales sugeridos son razonables. Agregar:

- **Frecuencia de ride calculada** a partir de wheel rate y masa de esquina
- **Eventos de contacto con bump stop** — identificables por spikes abruptos en wheel load o suspension travel tocando límites
- **Pitch angle** — diferencial de ride height front-rear bajo frenada y aceleración
- **Distribución de roll stiffness** — derivable del diferencial de suspension travel L-R en curva

### Coherencia con otros docs

Debe alinearse con **dampers.md** en la atribución correcta: springs = magnitud/distribución de transferencia estacionaria; dampers = velocidad de transferencia. Debe alinearse con **aero_balance.md** en que ride height tiene efectos tanto mecánicos (roll center) como aerodinámicos.

### Recomendaciones concretas

1. **Aclarar explícitamente que AC usa wheel rates, no spring rates** — agregar nota prominente: "Los valores de SPRING_RATE en AC y los ajustes de setup in-game representan wheel rate (rigidez medida en la rueda), no spring rate en el resorte."
2. **Incluir tabla de frecuencias naturales** por categoría con fórmula de cálculo.
3. **Agregar sección de anti-geometría** al menos conceptual.
4. **Agregar relación ride height → roll center → LLTD** con explicación de por qué ride height es tan influyente.
5. **Expandir sección de bump stops** como elemento de tuning activo, especialmente para coches aero.

---

## 4. dampers.md

### Precisión técnica

**AC sí modela slow/fast speed damping separado** — confirmado. Los parámetros en `suspensions.ini` son: `DAMP_BUMP`, `DAMP_FAST_BUMP`, `DAMP_FAST_BUMPTHRESHOLD`, `DAMP_REBOUND`, `DAMP_FAST_REBOUND`, `DAMP_FAST_REBOUNDTHRESHOLD`. Es un **modelo bilineal** (dos pendientes con un knee point), no un modelo multi-stage completo. Custom Shaders Patch (CSP) con "cosmic suspension" permite curvas LUT completas.

**Los valores de damping en AC están expresados en la rueda**, no en el eje del damper — consistente con que spring rates son wheel rates. Esto es un detalle operativo importante para modders.

**Damping ratios típicos** para validar el contenido: coches de calle ζ = 0.2–0.3 (confort) a 0.5 (sport); race cars sin aero ζ = 0.5–0.7 para modos de body, 0.3–0.5 para wheel hop; **ζ ≈ 0.65–0.7 es el target óptimo** para la mayoría de race cars (minimiza settling time con overshoot mínimo). ζ = 1.0 (critical damping) elimina overshoot pero es más lento para establecerse que ζ = 0.7.

La relación bump vs rebound requiere precisión: **rebound controla primariamente la velocidad a la que se libera la carga** de una rueda comprimida (transferencia de peso *fuera* del neumático). Rebound más rígido = transferencia más gradual. **Bump controla la velocidad de carga**. La relación típica en competición es **rebound 1.5–3× más rígido que bump**. Demasiado rebound causa "packing down" (la suspensión no se extiende completamente tras compresiones repetidas).

### Completitud

**Framework de dominios de velocidad** — omisión importante:

- **Low-speed (0–50 mm/s en la rueda)**: controla movimientos de body (roll, pitch, heave). Es lo que el piloto siente y lo que más afecta el balance transitorio. Ajuste más crítico.
- **Mid-speed (50–200 mm/s)**: transiciones, cambios direccionales bruscos.
- **High-speed (200+ mm/s)**: absorción de bumps y curbing. Debe ser suficientemente suave para que el neumático mantenga contacto con la superficie.

Conceptos ausentes:

- **Ratio rebound:compression** con justificación física (por qué 1.5:1 a 3:1 es el rango típico).
- **Platform control** — uso de dampers para mantener ride height consistente en coches aero donde la estabilidad de la plataforma es crítica para la aerodinámica.
- **Wheel load variation como métrica de performance** — la función principal de los dampers en performance pura es minimizar la fluctuación de carga vertical en el neumático. Menor variación = mayor grip promedio (por tire load sensitivity). Invisible para el piloto pero crítico para lap time.
- **Packing down y jacking up** — patologías de relaciones bump/rebound incorrectas.

### Diagnóstico de telemetría

Los canales sugeridos son buenos. Agregar:

- **Histogramas de velocidad de damper** — distribución de tiempo en cada dominio de velocidad para entender el régimen operativo dominante
- **Coeficiente de variación de wheel load** — ratio de desviación estándar a media de carga, por rueda
- **Body pitch y roll rates** — derivables de posiciones de suspensión diferenciales
- **Comparación de suspension travel rates inside/outside en transitorios** — medida directa del rate de transferencia de carga

### Coherencia con otros docs

Debe ser consistente con **vehicle_balance_fundamentals.md** y **suspension_and_springs.md** en la atribución: dampers = rate de transferencia; springs/ARBs = magnitud/distribución. Si los otros documentos lo atribuyen incorrectamente, esta es la oportunidad de establecer la versión correcta como referencia canónica.

### Recomendaciones concretas

1. **Confirmar y documentar el modelo bilineal de AC** con los nombres de parámetros reales.
2. **Agregar el framework de dominios de velocidad** (low/mid/high → body/transition/road).
3. **Incluir target de damping ratio** ζ ≈ 0.65–0.7 con justificación.
4. **Explicar ratio rebound:compression** (1.5:1 a 3:1) con consecuencias de errores (packing down).
5. **Notar que los valores de AC son at-the-wheel**, no at-the-damper-shaft.
6. **Agregar sección de wheel load variation** como métrica de performance de dampers.

---

## 5. alignment.md

### Precisión técnica

**Error probable: presentar caster, KPI y scrub radius como parámetros ajustables.** En AC, estos **no son ajustables en el setup in-game**. Son propiedades emergentes de la geometría de suspensión definida por las coordenadas 3D de los puntos de fijación en `suspensions.ini` (WBCAR_TOP_FRONT/REAR, WBTYRE_TOP/BOTTOM, WBCAR_STEER, WBTYRE_STEER, etc.). Solo los modders pueden alterarlos editando coordenadas. Los parámetros ajustables por el usuario son: **camber estático, toe, y en algunos coches caster** (solo si el rango está definido en setup.ini).

**Bump steer SÍ está modelado en AC** — emerge de la posición de los attachment points del steering rod relativo a la geometría de suspensión. Es visible mediante el dev suspension app. No es ajustable pero sí un factor de diseño que afecta el comportamiento.

**Ackermann SÍ está modelado** — determinado por la geometría del steering arm (ángulo entre el brazo de dirección y el eje longitudinal del vehículo). El grado de Ackermann (paralelo, 100%, anti-Ackermann) emerge de los puntos STEER en suspensions.ini. Race cars frecuentemente usan Ackermann reducido o anti-Ackermann.

### Completitud

**Camber dinámico es la omisión más significativa.** El camber estático es solo el punto de partida — lo que importa es el camber bajo carga en curva, que está determinado por:

- **Camber gain de geometría**: función de la longitud del Front View Swing Arm (FVSA) — brazos más cortos producen más camber gain positivo (más negativo bajo compresión).
- **Camber inducido por caster**: caster positivo genera camber negativo en la rueda exterior al girar el volante. Razón clave por la que los race cars usan caster significativo.
- **Camber change por suspension travel**: varía según el diseño de la suspensión.

AC modela todo esto a través de su kinematic solver. El dev suspension app puede visualizar las curvas de camber vs travel y camber vs steer.

Conceptos ausentes:

- **Camber thrust**: fuerza lateral generada por inclinación del neumático, independiente de slip angle. Camber negativo genera fuerza hacia adentro de la curva.
- **Valores típicos de referencia**: calle -0.5° a -1.5°; GT/touring -2.0° a -3.5°; open-wheel -2.5° a -4.0°. Fronts suelen correr más negativos por efectos de steering geometry.
- **Toe: trade-off estabilidad vs respuesta**: toe-out delantero aumenta turn-in pero reduce estabilidad en recta; toe-in trasero estabiliza el posterior (universalmente usado en competición, 0.5-1.5mm total).
- **Ackermann geometry** al menos conceptual: a baja velocidad 100% Ackermann es geométricamente correcto; a alta velocidad con slip angles significativos, el neumático interior necesita menos ángulo → anti-Ackermann.
- **Scrub radius effects**: positivo proporciona feedback en la dirección; negativo (común en FWD) proporciona auto-corrección bajo frenada en μ-split.

### Diagnóstico de telemetría

- **Camber dinámico durante curva** — disponible via dev apps de AC
- **Gradiente térmico inner-to-outer** — diagnóstico primario de camber; ideal ~5-10°C más caliente en interior que exterior bajo carga
- **Steering angle vs lateral G scatter plot** — revela understeer gradient Y efectos de Ackermann
- **Desgaste asimétrico inner/outer en rectas** — indica scrub por toe excesivo

### Coherencia con otros docs

Debe coordinarse con **tyre_dynamics.md** en que los patrones térmicos I/M/O son diagnóstico de camber (no solo de presión). Debe coordinarse con **vehicle_balance_fundamentals.md** en que el caster-induced camber change afecta el balance transitorio.

### Recomendaciones concretas

1. **Aclarar qué es ajustable vs fijo**: "En AC, camber y toe son ajustables en el setup. Caster es ajustable solo en algunos coches. KPI, scrub radius, y Ackermann son propiedades emergentes de la geometría de suspensión, editables solo en suspensions.ini."
2. **Agregar sección de camber dinámico** con los tres componentes (geometry gain, caster-induced, travel-dependent).
3. **Incluir tabla de camber típico** por categoría como referencia.
4. **Agregar conceptos de Ackermann y bump steer** como secciones informativas (no ajustables pero sí relevantes para entender el comportamiento).
5. **Mencionar el dev suspension app** como herramienta para visualizar curvas cinemáticas.

---

## 6. aero_balance.md

### Precisión técnica

**Distinción AC vs ACC crítica y probablemente ausente.** En AC original, cada elemento aerodinámico opera como un "wing" independiente con sus propios CL, CD, y lookup tables de AOA y ground height. **Los elementos aerodinámicos NO interactúan entre sí** — bajar el splitter aumenta el downforce delantero sin afectar el diffuser trasero. Esto es una simplificación significativa vs la realidad y vs ACC (que usa aero maps completos basados en CFD/wind tunnel donde todos los elementos interactúan). Si el documento habla de interacciones aerodinámicas como si existieran en AC, es incorrecto.

**AC sí modela sensibilidad al yaw** via `YAW_CL_GAIN` y `YAW_CD_GAIN` por wing element — pero es una aproximación lineal, no el comportamiento real no-lineal.

**AC sí modela ground effect** via lookup tables `LUT_GH_CL` y `LUT_GH_CD` que proporcionan multiplicadores de CL y CD en función de la altura al suelo. Esto permite modelar aumento de downforce a menor ride height para diffusers y splitters.

La sensibilidad de ride height puede estar **sobreestimada para AC** si las cifras citadas provienen de ACC. En AC, la sensibilidad existe pero la ausencia de interacciones entre elementos la hace menos dramática que en ACC o en la realidad.

### Completitud

- **Center of Pressure (CoP) vs Center of Gravity (CoG)**: concepto fundamental ausente. El CoP es la posición longitudinal donde actúa la fuerza aerodinámica resultante. Si CoP ≠ CoG, el downforce crea un momento de pitch que cambia con V². Ejemplo: en F1, aero balance típico ~45% front, distribución de peso ~46-47%. Esta relación debe ser una sección dedicada.
- **Relación V² y su implicación**: las fuerzas aero escalan con el cuadrado de la velocidad. El coche tiene un balance fundamentalmente diferente a baja vs alta velocidad. Comparar grip en curvas lentas vs rápidas es el método diagnóstico primario para aislar contribución aerodinámica.
- **Eficiencia aerodinámica (L/D)**: downforce-to-drag ratio define el "costo" en drag de cada unidad de downforce. Circuitos de baja carga (Le Mans) necesitan alto L/D; circuitos de alta carga (Monaco) aceptan L/D menor.
- **Aero platform stability**: mantener ride height consistente bajo frenada/aceleración/curva es crítico porque los cambios de ride height alteran el aero balance. Springs rígidos, anti-dive geometry, y bump stops contribuyen al control de plataforma.
- **Drag pitching moment**: la fuerza de drag actúa a la altura del CoG, creando una transferencia de carga vertical adicional (pitching down). Raramente discutido pero afecta el balance en alta velocidad.

### Diagnóstico de telemetría

- **Front vs rear ride height bajo carga aero** — esencial para diagnosticar estabilidad de plataforma
- **Plot de balance (understeer gradient) vs velocidad** — superponer para aislar contribución aero vs mecánica
- **Estimación de drag desde speed trace** — comparar desaceleración teórica en coast-down con real
- **Pitch angle trace** — disponible via Telemetrick para monitorear estabilidad de plataforma
- **Canal de aero balance** — disponible en Telemetrick para monitoreo directo

### Recomendaciones concretas

1. **Aclarar el modelo aero de AC**: wing-based con elementos independientes, lookup tables GH, sin interacción entre elementos. Contrastar con ACC y realidad.
2. **Agregar sección CoP vs CoG** con ejemplo numérico y explicación de balance aerodinámico.
3. **Incluir relación V²** explícita y su implicación para el diagnóstico low-speed vs high-speed.
4. **Agregar L/D ratio** como métrica de eficiencia.
5. **Incluir nota sobre DRS/aero activo** — AC modela `[DYNAMIC_CONTROLLER]` para aero activa controlada por velocidad, brake input, o lateral G.

---

## 7. braking.md

### Precisión técnica

**Problemas de disponibilidad de parámetros en AC**:

- **Brake duct size**: en AC original, **no es universalmente ajustable** — solo ciertos coches lo incluyen. En ACC sí (escala 0-6 para todos los coches).
- **Pad compound**: AC **no tiene pad compounds ajustables**. ACC ofrece 4 compounds.
- **Engine brake map**: en AC, ajustable **solo en coches específicos** que lo tienen en realidad (fórmulas, algunos GT con ECU). No es universal.
- **Brake fade**: en AC, modelado **solo para coches específicos** (principalmente clásicos: Shelby Cobra, Lotus 49, Maserati 250F, Ferrari F40, Ford GT40, etc.). La mayoría de coches modernos en AC **no tienen brake fade**. En ACC es universal.

Si el documento presenta estos como universalmente disponibles, es engañoso.

La relación brake bias con carga aerodinámica está correctamente identificada como error común a evitar. El brake bias ideal cambia con la velocidad porque el downforce añade más carga al eje con más downforce. A **300 km/h con downforce significativo, el bias ideal puede desplazarse varios puntos porcentuales** vs baja velocidad. Pilotos de F1 ajustan bias curva por curva.

### Completitud

- **Fórmula de brake bias ideal**: carga eje delantero bajo frenada = (peso estático front) + (masa × deceleración × h_CG / wheelbase). Bias ideal front% = carga front / peso total bajo frenada. Ejemplo: coche 50/50, 1g frenada, h_CG 0.4m, wheelbase 2.5m → carga front = 50% + (1×0.4/2.5) = 66% → bias ideal ~66% front.
- **Física del lock-up**: al bloquearse una rueda, transiciona de fricción dinámica (rodadura) a fricción cinética (deslizamiento). μ cinético es **10-30% menor** que μ pico de rodadura. Por eso threshold braking produce máxima deceleración.
- **Deceleración G típica por categoría**: coches de calle ~0.8-1.0g; GT3 ~1.2-1.5g; open-wheel ~2.0-3.5g; F1 ~4.0-6.0g.
- **Trail braking physics completa**: no es simplemente "frenar entrando a la curva" — mantener presión parcial de freno durante el giro mantiene peso en el eje delantero (preservando grip delantero) y aprovecha más del friction ellipse simultáneamente para fuerza lateral y longitudinal.
- **Interacción ABS con brake bias**: en coches GT3 con ABS, los pilotos aplican presión máxima y el ABS gestiona lockup individual. El brake bias afecta en qué eje el ABS interviene primero y con qué frecuencia.

### Diagnóstico de telemetría

- **Diferencial de wheel speed individual** durante frenada — detección directa de qué ruedas se aproximan al lockup primero (revela efectividad real del brake bias)
- **Correlación brake pressure vs G de deceleración** — revela eficiencia del sistema de frenos y onset de fade
- **Análisis de brake trace speed-dependent** — comparar performance de frenada en zonas de alta velocidad (aero-asistida) vs baja velocidad

### Recomendaciones concretas

1. **Especificar disponibilidad por plataforma**: "Brake ducts: solo ciertos coches en AC, universal en ACC. Pad compound: no disponible en AC, 4 opciones en ACC. Engine brake: solo coches específicos en AC."
2. **Agregar fórmula de brake bias ideal** con ejemplo numérico.
3. **Agregar tabla de G de deceleración** por categoría.
4. **Expandir trail braking** con la explicación del friction ellipse.
5. **Notar que brake fade no es universal en AC** — muchos coches tienen frenada ilimitada.

---

## 8. drivetrain.md

### Precisión técnica

**Clarificación crítica: AC usa lock percentages (0.0–1.0), NO ramp angles.** Los parámetros en `drivetrain.ini` son `POWER` y `COAST` con valores de 0.0 (open) a 1.0 (fully locked). Esto es un **modelo simplificado** de clutch-pack LSD. No modela ángulos de rampa directamente (30°, 60°, 90° como en LSDs reales), ni curvas de fricción de clutch pack, ni sensibilidad al torque de un Torsen. Si el documento menciona "ramp angles" como parámetros de AC, es incorrecto.

**Preload**: en AC, especificado en Nm, representa el **torque mínimo de bloqueo** del mecanismo de precarga (Belleville spring). Mantiene el diferencial parcialmente bloqueado hasta que la diferencia de torque entre ruedas supera este valor. **Preload ≠ lock percentage** — preload añade una fuerza de base constante independiente del input de throttle, mientras que power/coast lock es proporcional al torque del drivetrain. Mayor preload (e.g., 200 Nm) = más understeer/estabilidad en turn-in; menor preload (e.g., 80 Nm) = más rotación.

**1-way/1.5-way/2-way**: la configuración en AC es:
- **1-way**: COAST ≈ 0, POWER > 0
- **1.5-way**: COAST < POWER (típicamente COAST ≈ 0.4-0.6 × POWER)
- **2-way**: COAST = POWER

**Error común**: "2-way = fully locked en ambas direcciones" — incorrecto. 2-way significa **igual porcentaje** de lock en ambas direcciones, no necesariamente 100%.

**Torsen/torque-biasing**: AC **no modela Torsen explícitamente**. El modelo clutch-type puede aproximar el comportamiento general pero carece de la dependencia de velocidad diferencial que caracteriza a un helical gear diff.

### Completitud

- **Comportamiento del diferencial en trail braking**: con coast locking, el diff se bloquea parcialmente durante deceleración, lo que previene que la rueda interior acelere relativo a la exterior — estabiliza el posterior bajo frenada pero reduce rotación hacia la curva. Interacción crítica con la técnica de pilotaje.
- **Gear ratio optimization detallado**: RPM drop entre marchas (idealmente mantener el motor en la banda de potencia pico); trade-off close ratios vs coverage; final drive afecta TODAS las marchas simultáneamente.
- **Viscous vs clutch-type**: AC modela clutch-type. Los diferenciales viscosos (locking proporcional a diferencia de velocidad, no torque) son fundamentalmente diferentes y NO están representados con precisión por el modelo de AC. Algunos coches de calle en AC usan viscous diff en realidad pero son aproximados como clutch-type in-sim.
- **Electronic differential / brake-based torque vectoring**: ciertos coches en AC (GT-R, Lamborghinis AWD) modelan sistemas electrónicos — el documento debería mencionarlo.

### Diagnóstico de telemetría

- **Ratio (no diferencia) de wheel speed inside/outside** — durante curva, la diferencia geométrica de velocidad es conocida por el ángulo de dirección y ancho de vía; desviaciones indican locking/slip
- **Estimación del estado de lock del diff** — derivable de wheel speed ratio + throttle/brake + steering angle
- **Análisis de entrega de torque** — correlacionar tasa de aplicación de throttle con onset de wheelspin para revelar comportamiento del diff
- **RPM vs speed por marcha** — verificar optimización de gear ratios

### Recomendaciones concretas

1. **Aclarar explícitamente**: "AC usa valores de lock percentage 0.0-1.0 para POWER y COAST, no ramp angles. 0.0 = open, 1.0 = fully locked (spool)."
2. **Separar claramente preload de lock percentage** con diagrama de comportamiento.
3. **Incluir tabla de configuración** mostrando combinaciones power/coast/preload para 1-way, 1.5-way, 2-way, open, y spool.
4. **Notar que Torsen no está modelado** — explicar la diferencia fundamental y cómo aproximar.
5. **Agregar sección de comportamiento en trail braking** — interacción coast lock con turn-in.
6. **Incluir sección de gear ratio** con cálculo de RPM drop y optimización.

---

## 9. telemetry_and_diagnosis.md

### Precisión técnica

**Error factual: sample rate de ~20-30Hz es incorrecto y desactualizado.** La simulación de física de AC ejecuta internamente a **~333 Hz** (confirmado desde patch 1.3 con multithreading). Las tasas de captura de telemetría dependen de la herramienta:

| Herramienta | Tasa de captura |
|---|---|
| ACTI (legacy) | ~20 Hz default |
| Telemetrick | 30–200 Hz configurable |
| Full-featured Telemetry mod | 30–200 Hz |
| MyRacingData | 60 Hz |
| SRT | Configurable |

La afirmación correcta es: "La física interna corre a ~333 Hz. Las herramientas de telemetría capturan típicamente a 30–200 Hz según configuración. Algunos canales específicos (ABS/TC active) pueden loguearse a tasas menores (~20 Hz)."

**Telemetrick debería ser la herramienta recomendada principal** para AC (180+ canales, MoTeC/CSV export, live tracing, aero/suspension data, Telemetry Exchange para comparación con otros pilotos).

### Completitud

**Canales disponibles**: con herramientas modernas, AC expone **180+ canales** incluyendo: speed, RPM, gear, throttle, brake, steering, G-forces (lat/long/vert), wheel speeds individuales, tire temps (I/M/O via Python API), tire pressures, suspension travel (per corner), ride height F/R, wheel loads, wheel slip, camber, brake temps (car-dependent), aero data, engine torque/power, y más.

Omisiones críticas:

- **Ecosistema de herramientas de telemetría**: necesita tabla comparativa (ACTI, Telemetrick, SRT, MoTeC i2 Pro como software de análisis, dev apps de AC).
- **G-G diagram / friction circle**: técnica de análisis fundamental — plotear lateral vs longitudinal G para visualizar utilización de grip e identificar áreas sub-utilizadas del performance envelope. Debería ser prominente.
- **Metodología de reference lap**: comparar datos propios con una referencia (lap más rápido propio, o telemetría de otro piloto via Telemetry Exchange). Overlay de traces, identificar dónde se gana/pierde tiempo, diagnosticar si es braking point, corner speed, o exit speed.
- **Sector analysis y corner-by-corner comparison**: romper el lap en sectores/curvas, comparar cada uno independientemente.
- **Tabla síntoma-causa debe presentarse como generador de hipótesis**, no diagnóstico definitivo. Múltiples causas producen síntomas idénticos (equifinalidad). Los síntomas son speed-dependent (mecánico vs aero). La técnica del piloto puede enmascarar o mimetizar problemas de setup.
- **Math channels**: canales calculados como wheel slip %, estimación de downforce, disipación de energía en frenos.
- **Calidad de datos en sim**: datos de sim son inherentemente "limpios" (sin ruido de sensor, drift de calibración), pero la tasa de logging puede crear aliasing de eventos rápidos; datos dependientes de frame-rate pueden tener jitter temporal.

### Diagnóstico de telemetría (meta-auditoría)

La tabla diagnóstica existente cubre síntomas razonables. Agregar:

- **Aero-related balance shift** — diagnosticable comparando balance en curvas low-speed vs high-speed
- **Differential-related corner exit behavior** — correlacionar wheel speed differential con throttle input
- **Brake fade onset** — brake temp vs deceleration correlation degrading over stint
- **Tire degradation pattern** — comparar consistency de lap times con degradación de temps y wear

### Recomendaciones concretas

1. **Corregir sample rate**: "Física interna ~333 Hz; captura de telemetría 30-200 Hz según herramienta."
2. **Agregar tabla comparativa de herramientas** con canales, tasas, formatos de export, y features.
3. **Agregar G-G diagram** como técnica diagnóstica prominente.
4. **Incluir metodología de reference lap** y Telemetry Exchange.
5. **Reframed tabla síntoma-causa** como "generador de hipótesis" con nota sobre equifinalidad y speed-dependence.
6. **Agregar sección de sector analysis** y corner-by-corner comparison.

---

## 10. setup_methodology.md

### Precisión técnica

**OVAT es presentado como metodología recomendada — tiene limitaciones significativas no reconocidas.** OVAT (One Variable At A Time) es criticado en la literatura estadística por **no detectar efectos de interacción**. Un cambio de spring rate puede mostrar mejora solo cuando se combina con un setting específico de damper — OVAT nunca descubriría esto. Milliken & Milliken y Claude Rouelle (OptimumG) documentan extensivamente estas interacciones. El documento debería presentar OVAT como una simplificación práctica útil pero explicar sus limitaciones.

**3-5 laps para significancia estadística es insuficiente** para detectar mejoras pequeñas. Con varianza típica de lap time en sim racing (σ ≈ 0.2-0.5s): para detectar una mejora de 0.1s con 95% de confianza, se necesitan ~36 laps (cálculo de power estadístico para comparación pareada). Más prácticamente: **8-10 laps limpios y consecutivos** por configuración proporcionan un dataset razonable para detectar diferencias de ~0.2-0.3s. Se recomienda descartar outliers y usar **mediana** en lugar de media (más robusta a outliers).

**El orden de prioridad "safety → gross balance → overall grip → fine-tuning" es razonable pero incompleto.** Una secuencia más precisa: **ride height/aero platform → pressures/temps base → gross balance (springs, ARBs) → damping → fine balance (diff, brake bias) → fine-tuning (camber, toe, pressures finales).**

### Completitud

Omisiones importantes:

- **Design of Experiments (DOE)** como alternativa superior a OVAT: factorial designs permiten identificar efectos principales + interacciones clave. Una versión simplificada práctica: variar 2-3 parámetros simultáneamente en una matriz planificada, analizar resultados estadísticamente. Incluso un factorial fraccionario 2^k-p simple captura más información que OVAT con similar esfuerzo.
- **Jerarquía de sensibilidad de parámetros**: cuáles tienen mayor impacto en lap time. Alta sensibilidad: ride height, spring rates, wing angle, tire pressures. Media: ARB stiffness, damper rates, diff settings, brake bias. Baja: camber fine-tuning, toe adjustment, gear ratios individuales. Testear parámetros de alta sensibilidad primero.
- **Efectos de interacción entre parámetros**: spring rate ↔ damper rate; ride height ↔ aero balance; tire pressure ↔ camber; differential ↔ spring/ARB. Cambiar springs invalida settings óptimos de dampers — esto debe comunicarse explícitamente.
- **Driver adaptation as confound**: al cambiar setup, el piloto se adapta inconscientemente (puntos de frenada, velocidad de turn-in, aplicación de throttle). Primeras vueltas en setup nuevo son unreliable. Recomendación: varias vueltas de instalación/adaptación antes de comparación cronometrada. "Feel" subjetivo y lap time objetivo pueden discrepar — confiar en los datos.
- **Track evolution y temperatura**: en sims, menos extremo que en realidad pero presente (especialmente en ACC). Recomendar: mismas condiciones de pista, mismo estado de neumáticos, mismo nivel de combustible. Idealmente intercalar configuraciones (A-B-A-B) en lugar de bloques secuenciales.
- **Filosofía de baseline**: empezar desde setup de comunidad conocido o default. Si se construye desde cero: target frecuencias ~2.0-2.5 Hz front (algo mayor rear), damping ratios ~0.5-0.7 critical, brake bias neutro, diff settings moderados.

### Diagnóstico de telemetría

- **Herramientas de análisis estadístico**: desviación estándar de lap times, intervalos de confianza, t-test pareado para comparar configuraciones
- **Sensitivity plot**: graficar lap time vs valor del parámetro para visualizar sensibilidad y encontrar óptimo
- **Protocolo A/B test estructurado** con criterios específicos (mínimo de laps, remoción de outliers, test estadístico)

### Recomendaciones concretas

1. **Reconocer limitaciones de OVAT** — agregar sección sobre interacciones y mencionar DOE simplificado como alternativa.
2. **Aumentar recomendación de laps** a 8-10 mínimo por configuración; usar mediana, no media.
3. **Agregar jerarquía de sensibilidad** de parámetros para guiar orden de testing.
4. **Incluir sección de interaction effects** con ejemplos clave (spring↔damper, ride height↔aero).
5. **Agregar driver adaptation** como confound explícito con estrategias de mitigación.
6. **Incluir protocolo A/B test** estructurado con criterios estadísticos.

---

## Inconsistencias cruzadas entre documentos

**Inconsistencia #1 — Modelo de neumáticos**: Si tyre_dynamics.md referencia Pacejka y otros documentos lo mencionan también, todos deben corregirse al brush model que AC realmente usa.

**Inconsistencia #2 — Springs y velocidad de transferencia**: Si vehicle_balance y suspension_and_springs atribuyen a los springs el control de la "velocidad" de transferencia de carga, mientras dampers.md lo atribuye correctamente a los dampers, existe una contradicción directa. La versión correcta: springs/ARBs → magnitud y distribución de LLTD estacionaria; dampers → rate de transferencia.

**Inconsistencia #3 — Parámetros ajustables**: alignment.md podría listar caster, KPI, scrub radius como ajustables, mientras que la realidad de AC es que son propiedades geométricas fijas. braking.md podría listar brake ducts y pad compound como universales cuando solo están disponibles en ciertos coches. drivetrain.md podría usar terminología de ramp angles cuando AC usa lock percentages.

**Inconsistencia #4 — Sample rate de telemetría**: Si telemetry_and_diagnosis.md dice 20-30 Hz y otros documentos referencian canales de alta frecuencia, la discrepancia confunde. La corrección: "~333 Hz interno; 30-200 Hz logging según herramienta."

**Inconsistencia #5 — Disponibilidad de tire temps I/M/O**: Si tyre_dynamics y telemetry_and_diagnosis sugieren analizar temps I/M/O sin aclarar que solo están disponibles via Python API (no shared memory), los usuarios que usan herramientas externas no podrán acceder a estos datos.

**Gap #6 — Falta de cross-referencing en aero**: aero_balance debería referenciar suspension_and_springs (ride height → aero platform), dampers.md (platform control), y braking.md (aero effect on brake bias). Actualmente estos conceptos probablemente se tratan de forma aislada.

---

## Resumen priorizado de trabajo necesario

| Prioridad | Documento | Esfuerzo | Razón |
|---|---|---|---|
| **1** | **tyre_dynamics.md** | Alto | Error fundamental de modelo (Pacejka vs brush); falta tire load sensitivity, SAT, relaxation length. Es el documento base que informa a todos los demás. |
| **2** | **vehicle_balance_fundamentals.md** | Alto | Error causal (springs→velocidad); falta descomposición de weight transfer, TLLTD, tire load sensitivity como mecanismo. Segundo documento más referenciado. |
| **3** | **telemetry_and_diagnosis.md** | Medio-Alto | Sample rate incorrecto; falta ecosistema de herramientas, G-G diagram, reference lap methodology, reframe de tabla diagnóstica. Documento transversal que afecta el uso de todos los demás. |
| **4** | **suspension_and_springs.md** | Medio-Alto | Confusión spring rate vs wheel rate (AC-específico); posible error springs→velocidad; falta anti-geometry, ride height→roll center. |
| **5** | **drivetrain.md** | Medio | Posible confusión ramp angles vs lock percentages; falta Torsen note, trail braking interaction, gear optimization detallado. |
| **6** | **braking.md** | Medio | Parámetros no universales presentados como universales; falta fórmula de bias ideal, brake fade caveat, G reference table. |
| **7** | **dampers.md** | Medio-Bajo | Probablemente el más correcto del set; necesita velocity domains framework, damping ratio targets, ratio rebound:compression. |
| **8** | **alignment.md** | Medio-Bajo | Caster/KPI/scrub no ajustables en AC; falta camber dinámico, Ackermann, valores de referencia. |
| **9** | **aero_balance.md** | Medio-Bajo | Falta distinción AC vs ACC aero model, CoP vs CoG, L/D ratio. Modelo AC es más simple de lo que probablemente describe. |
| **10** | **setup_methodology.md** | Bajo-Medio | OVAT limitations, lap count insuficiente, falta DOE y interaction effects. Funcionalmente útil pero mejorable. |

El criterio de priorización combina tres factores: gravedad del error (errores fundamentales primero), impacto cascada (documentos que informan a otros tienen prioridad), y frecuencia de uso esperada (documentos core sobre neumáticos y balance serán los más consultados). Se recomienda abordar tyre_dynamics y vehicle_balance en paralelo como primera fase, seguido de telemetry_and_diagnosis como habilitador transversal, y luego el resto en orden descendente de prioridad.