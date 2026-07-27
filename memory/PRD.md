# PRD — NormaLab (Plataforma de estudios normativos)

## Problem statement (original)
App web interna para despacho técnico de ingeniería/arquitectura. Plataforma modular de estudios normativos: módulos por normativa, crear estudio, asistente guiado, informe no vinculante. Arquitectura features-first, extensible mediante module registry. Módulos: CTE, RSCIEI, REBT, RITE, RD Accesibilidad 2023. MVP con RSCIEI operativo.

## Decisiones (user choices)
- BD: MongoDB. Frontend: React (JS) + react-hook-form + zod. Auth: JWT propio (cookies httpOnly), roles admin/tecnico.
- Informe: vista en pantalla + PDF (window.print).
- Normativa RSCIEI: **RD 164/2025** (migrado desde RD 2267/2004 en iteración multi-sector, según Guía RSCIEI 2025 y Excel real del despacho).

## Arquitectura
- Backend features-first: `core/`, `features/` (auth, projects, studies, modules), `normative_modules/` (base + registry + `rsciei/` + `placeholders.py`).
- Frontend features-first: `features/{auth,dashboard,projects,studies,modules}`, wizard schema-driven.

## Modelo de datos (Mongo)
- users, projects, studies(data, results, report, current_version), study_versions, login_attempts, password_reset_tokens.

## RSCIEI multi-sector (operativo) — RD 164/2025
Modelo de datos del estudio (`study.data`):
- `establecimiento`: { actividad, config }
- `sectores[]`: { id, nombre, tipo(sector|area_exterior), config, situacion, num_salidas, fachada_accesible, rociadores, altura_evacuacion, cubierta_ligera, ra? }
- `dependencias[]`: { id, nombre, planta, sup_util, sup_construida, sector_id, densidad, sin_ocupacion, uso_ocupacion, modo(produccion|almacenamiento), qsi|qvi, ci, hi, ra, rmin? }

Flujo del asistente: 1) Establecimiento → 2) Cuadro de superficies (útil/construida) + agrupación por sectores → 3) Ocupación (CTE por densidad) → 4) Carga de fuego (por dependencia) → 5) Resultados.
- La superficie construida de un sector = suma de sus dependencias (cobertura 100% automática).
- Cálculo por sector: Qs = Σ(aporte)/A·Ra, NRI (Tabla 1.3.1), superficie máx admisible (Tabla 2.1.1 RD164/2025), requisitos Anexo II (estabilidad Tabla 2.5.1) + Anexo III (detección, BIE, rociadores, humos, hidrantes, **hidrante llenado camión Tabla 3.3.1**), evacuación (Tabla 2.3.1).
- Validación Rmin (Tabla 1.3.4/1.3.5): aviso si Ra del sector < Rmin de una actividad.
- Ocupación CTE por dependencia (techo(sup_útil/densidad)); total del establecimiento.
- Informe incluye: cuadro de superficies, ocupación, resumen de sectores, detalle+instalaciones por sector, tablas de referencia resaltadas.

## Implementado
- 2026-07-21 (iter 14 — Mejoras UX del paso Sectores + Evacuación + escaleras protegidas):
  - Tarjetas de sector a **ancho completo apiladas** (no grid).
  - **Carga de fuego con catálogo Tabla 1.3.5**: al elegir actividad/subactividad se autocompletan qs/qv, Ci y Rmin (además de edición manual y modo producción/almacenamiento).
  - **LRE**: tooltip que avisa de que la superficie no cuenta en la carga de fuego + clasificación según **Tabla 2.1 DB-SI** (riesgo bajo/medio/alto → R, con justificación). Ya excluidos del Qs del sector.
  - **Escaleras protegidas**: nueva clasificación que SÍ computa carga de fuego (zona de paso) y exige justificación CTE (tipo protegida/especialmente protegida, interior/exterior, anchura, capacidad, uso restringido, justificación), que se traslada al informe (observaciones).
  - **Evacuación**: los recorridos se **precargan** desde las estancias del cuadro de superficies (excluyendo LRE), eliminables individualmente, con botón de recarga. Origen conservado.
  - Silenciado el overlay benigno de dev «ResizeObserver loop». Testing: 53/53 pytest + API E2E + frontend E2E 100% (iter 14).
- 2026-07-21 (iter 14 — Anexo II · estabilidad al fuego (R) modulada por altura de evacuación):
  - En **plantas sobre rasante**, la estabilidad al fuego exigida (R) se incrementa según la altura de evacuación (Anexo II, Tabla 2.2): **+1 escalón** para 15 < h ≤ 28 m y **+2 escalones** para h > 28 m, sobre la escala R 30 → R 60 → R 90 → R 120 → R 180 → R 240 (tope R 240). Bajo rasante no se modula por altura. El detalle del requisito explica el tramo y el incremento aplicado.
  - `_modular_r_por_altura` en `rsciei/requirements.py`; el sector aporta `altura_evacuacion` (campo `sector-N-altura`). Testing: 53/53 pytest + verificación API (h=8 → R 30; h=32 → R 90).
- 2026-07-21 (iter 13 — FLUJO SECTOR-CÉNTRICO estilo Excel KION + LRE + sectores CTE con carga de fuego):
  - Reconstruido el módulo INCENDIOS según el modelo profesional del Excel del usuario. Se **eliminó el paso «Ámbitos»**; el carácter industrial (RSCIEI) / CTE es ahora una propiedad **de cada sector**.
  - **Paso 1 · Cuadro de superficies**: inventario puro de estancias/dependencias (S. útil + S. construida), sin sectores.
  - **Paso 2 · Sectores de incendio**: crear sectores, **asignar** cada estancia a un sector, marcar estancias como **Local de Riesgo Especial (LRE)** (excluidas del cálculo de la carga de fuego, evaluadas aparte con su R), y definir la **carga de fuego** por estancia (producción qsi/Ci/Ra o almacenamiento qvi/hi/Ra).
  - **Sectores CTE también calculan carga de fuego (Qs)** y se evalúan además con CTE DB-SI (SI 1–6), como en el Excel.
  - Motor: RSCIEI ampliado (LRE fuera del sumatorio de Qs; sectores CTE con bloque `dbsi`). `incendios` en modo dual (nuevo sector-céntrico + compatibilidad legacy por ámbitos).
  - Nuevos/rehechos: `ProyectoSuperficiesStep` (estancias), `SectoresStep`, `ResultsPanel` (bloques LRE + DB-SI). Testing: backend 52/52 + API E2E; frontend E2E 100% (iter 13).
- 2026-07-21 (iter 12 — cuadro único de superficies a nivel proyecto + gestión de expedientes):
  - **RSCIEI Anexo III · hidrantes (Tabla 3.3.1)** contrastado con el texto literal (Iberley/BOE). Consolidada en UNA sola instalación «Hidrantes exteriores (Tabla 3.3.1)» con umbrales por configuración×riesgo *decrecientes con el riesgo* (AV/AH: bajo 1000/medio 300; B: 3500/2500/1000; C: medio 3500/alto 2000; D: 5000). Eliminada la instalación separada e inventada «hidrante para llenado de camiones». Añadido «Sistema de comunicación de alarma» (punto 5.1, ≥10.000 m²).
  - **CTE DB-SI SI 2** · separación mínima entre huecos según el **ángulo** entre planos de fachada (Tabla 1.1: 0°=3,00 … 180°=0,50 m, interpolación lineal; 50 % para edificios colindantes; exención si huecos EI 60). Nuevos campos: angulo_fachadas, distancia_huecos, huecos_ei60, edificio_colindante.
  - **CTE DB-SI SI 4** · dotación matizada **por planta** (campo num_plantas; detalle «en cada una de las N plantas» para extintores/alumbrado/señalización) y **por zona** (extintores orientativos ≥1 cada 300 m² por dependencia).
  - Testing: backend 51/51 pytest; frontend E2E 7/7 (iter 11). Sin issues. NOTA: los valores de Tabla 3.3.1 se alinean a la Tabla 3.1 consolidada (Iberley/BOE); si el despacho requiere el desdoble llenado/impulsión de RD 164/2025 con números exactos, aportar la tabla literal del BOE.
- 2026-07-20 (iter 10 — P0: DB-SI COMPLETO SI 1–SI 6 + tabla maestra):
  - **Tabla maestra oficial** `cte_dbsi/tablas_oficiales.py` como única fuente de verdad (SI1 Tabla 1.1/1.2/2.2, SI3 Tabla 3.1/4.1/5.1, SI5 vial/maniobra, SI6 Tabla 3.1/3.2).
  - Motor DB-SI reescrito: cubre **SI 1** (sector, delimitadores, riesgo especial, reacción al fuego), **SI 2** (propagación exterior + chequeo de distancia a colindantes), **SI 3** (salidas, recorridos, ancho A≥P/200, protección de escaleras, humos, PMR), **SI 4** (dotación por uso, Tabla 1.1), **SI 5** (vial/espacio de maniobra/accesibilidad bomberos), **SI 6** (estructura por uso/altura/rasante + riesgo especial). Salida como lista `secciones` con estado por sección.
  - Frontend: `DbsiResultsPanel` iterando SI 1–SI 6 con badges de estado; informe con secciones SI + tablas de referencia resaltadas. Nuevos campos en el asistente DB-SI.
  - **Test integral único** `tests/test_incendios_complete.py`: 49/49 (referencia la tabla maestra). Frontend 4/4 escenarios. Sin issues.
- 2026-07-20 (iter 9 — MÓDULO UNIFICADO «Incendios»):
  - Unificación de RSCIEI (RD 164/2025) y CTE DB-SI en un único módulo operativo **INCENDIOS** (reemplaza las entradas separadas; sub-motores reutilizados).
  - Soporte de **proyectos mixtos**: un estudio se compone de «ámbitos», cada uno de tipo industrial (RSCIEI) o edificación (DB-SI). Motor enruta cada ámbito a su sub-motor; resultados y estado global agregados.
  - Frontend: asistente con paso «Ámbitos» + un paso por ámbito (sub-formulario completo vía `StepBody`), `IncendiosResultsPanel` (bloque por ámbito) e informe con separadores `ambito_header`.
  - Testing: backend 7/7, frontend flows críticos 100%. Sin issues.
- 2026-07-20 (iter 8):
  - RSCIEI · Bloque de evacuación ampliado: recorridos reales por origen (hasta_salida/sin_alternativa) con validación cumple/no cumple, y coeficientes de incremento notas 4/5 de la Tabla 2.3.1 (nota4a/4b +25%, nota4c +100%, nota5 solo riesgo bajo nivel 1). Nuevo paso «Evacuación» en el asistente; recorridos en informe y panel de resultados.
  - Nuevo módulo OPERATIVO **CTE DB-SI** (RD 314/2006): SI 1 (compartimentación/sup. máx sector), SI 3 (ocupación, salidas, recorridos, ancho A≥P/200), SI 4 (instalaciones) y SI 6 (estabilidad estructural). Registrado en el registry (sustituye al placeholder CTE), asistente propio (Datos del edificio + Ocupación) y panel/informe dedicados. Valida la extensibilidad del module registry.
  - Testing: backend 22/22 (iter8 11 + regresión iter7 11), frontend E2E RSCIEI evacuación + CTE DB-SI 100%. Sin issues.
- 2026-07-20 (iter 1-7):
- 2026-07-20 (iter 1-3): Auth JWT, dashboard, expedientes CRUD, estudios (autosave/compute/versionado), RSCIEI single-sector con motor Qs/NRI/sectorización/requisitos e informe con tablas resaltadas.
- 2026-07-20 (iter 7 — REFACTOR MULTI-SECTOR, RD 164/2025):
  - Migración normativa a RD 164/2025 (Tabla 2.1.1 corregida: AV n6-8=NO ADMITIDO, AH n7=1500/n8=NO ADMITIDO, B/C actualizadas).
  - Arquitectura multi-sector (dependencia = unidad atómica con superficie/ocupación/carga de fuego, agrupada en sectores).
  - Nuevo flujo del asistente (superficies → sectores → ocupación CTE → carga de fuego).
  - Tabla 3.3.1 (hidrante llenado camión bomberos) y validación Rmin (Tabla 1.3.5).
  - Tabla 2.3.1 (evacuación) integrada en requisitos e informe.
  - Ocupación CTE y cuadro de superficies en el informe final.
  - Testing: backend 11/11 (test_rsciei_multisector.py), frontend E2E 100%. Sin issues.

## Backlog
- **P1 (fase 2): Anejos de cálculo estructural DB-SI** (B tiempo equivalente; C hormigón; D acero; E madera; F fábrica) — calculadoras de ingeniería.
- P1: Verificar/contrastar los umbrales del Anexo III RSCIEI y la Tabla 3.3.1 contra el texto literal — HECHO (iter 11, alineado a Tabla 3.1 consolidada Iberley/BOE).
- P1: Refinar SI 4 (dotación) por planta y por zona; SI 2 separación de huecos por ángulo (Tabla 1.1) — HECHO (iter 11).
- P1 (pendiente): Anexo II RSCIEI · modular la estabilidad (R) por altura de evacuación en plantas sobre rasante.
- P2 (aprobado): tabla resumen ejecutiva al inicio del informe unificado (estado cumple/no cumple por ámbito y sección).
- P1: Completar Tabla 1.3.5 exhaustiva del catálogo de actividades + Rmin por actividad — HECHO (2026-07-20): 131 actividades en 12 categorías con qsi/qvi, Ci orientativo y Rmin, mapeando MJ/m²→producción y MJ/m³→almacenamiento.
- P1: Bloque de evacuación ampliado (recorridos reales por origen, coeficientes nota 4/5 Tabla 2.3.1).
- P1: Módulos CTE DB-SI, REBT, RITE, RD Accesibilidad 2023 (schema+engine+report).
- P1: Panel admin de usuarios/roles; recuperación de contraseña por email.
- P2: Cálculos de licencia ambiental del Excel (consumo de agua, sistema de depuración, ventilación) — fuera de RSCIEI.
- P2: PDF server-side maquetado; comparador de versiones (diff); RAG documental + IA.
- P3: Multitenancy real.

## Credenciales
admin@normalab.com / Admin1234! (rol admin). Ver /app/memory/test_credentials.md.

## Próximas tareas
1. Ampliar catálogo de actividades a la Tabla 1.3.5 completa con Rmin por actividad.
2. Segundo módulo operativo (CTE DB-SI) para validar la extensibilidad del registry.

## Changelog
- 2026-07-27: **FASE 1 — LRE fuera del Qs · config CTE oculta · tablas multi-sector con color (validado iter 21, 100%)**
  - (1a) **LRE ya NO computan carga de fuego**: se excluyen del Qs (calc_deps) y de la validación; se clasifican solo por el CTE (Tabla 2.1: uso + volumen/potencia → riesgo → R). Se quitó el bloque de carga de fuego del detalle LRE; columna «Carga (MJ)» = «no computa».
  - (1b) **Sectores CTE**: en el informe la columna Config. = «—» y su sectorización se marca «no aplica» (Tabla 2.1.1 RSCIEI no procede; se evalúa por DB-SI).
  - (1c) **Tablas de referencia multi-sector**: cada sector RSCIEI tiene color propio + leyenda; las celdas/filas aplicables se pintan con el color del sector que las activa (`tablas.py` genera `legend` + `cell_sectors`/`row_sectors`; `RefTable` y DOCX `_ref_table` los renderizan). Los sectores CTE se excluyen de las tablas RSCIEI.
  - Testing: 3/3 E2E Fase 1 + flujo UI (1a/1b/1c) + 53/53 unit. Sin issues. (Eliminado test obsoleto `test_incendios_lre_e2e.py`.)
- 2026-07-27: **LRE clasificados por uso + volumen (Tabla 2.1 DB-SI) con riesgo automático (validado iter 20, 100%)**
  - Al marcar una estancia como Local de Riesgo Especial ahora se pide el **uso** (modal buscador `LreUseDialog` con la Tabla 2.1 del CTE DB-SI, agrupada por uso previsto) y la **altura**; con la superficie del cuadro se calcula el **volumen (= superficie × altura)** y se **determina automáticamente el riesgo** (bajo/medio/alto) y su resistencia R según la métrica del uso (V=volumen, S=superficie, P=potencia, QS, fijo). El riesgo es editable manualmente.
  - Nuevo `lib/lreCatalog.js` (LRE_USES + `classifyLre`), modal `LreUseDialog.jsx`, y `AssignmentRows.applyLre` que recalcula y persiste `lre_uso/lre_metric/lre_criterio/lre_valor/lre_riesgo/lre_r`. `draftLRE` redacta la justificación con uso + volumen/superficie/potencia + criterio.
  - Motor (`engine.py`) surfacea en `locales_riesgo_especial`: uso, uso_grupo, altura, volumen, potencia, metric, criterio (+ riesgo/R/superficie/justificación). Informe HTML y DOCX muestran uso, volumen/potencia y criterio. Los LRE siguen computando carga de fuego.
  - Testing: 6/6 E2E LRE (volumen MEDIO, potencia BAJO/MEDIO/ALTO, escaleras excluidas, informe/DOCX) + flujo UI + 53/53 unit. Sin issues.
- 2026-07-27: **LRE computan carga de fuego · escaleras no (+ validaciones)**
  - Se **invierte** el tratamiento: los **Locales de Riesgo Especial (LRE)** ahora SÍ computan carga de fuego (se incluyen en A y en el numerador del Qs del sector) y, además, siguen evaluándose como LRE con su resistencia R (Tabla 2.1 DB-SI). Las **escaleras** dejan de computar carga de fuego (zona de paso); solo requieren justificación CTE DB-SI/SUA.
  - Motor (`engine.py`): `calc_deps` excluye escaleras e incluye LRE; `esc_deps` para el listado de escaleras; observaciones y comentarios actualizados. UI (`SectoresStep.jsx`): el detalle LRE incorpora el bloque de carga de fuego (`CargaFuegoInline`); el de escalera lo elimina; fila «Carga (MJ)» muestra «no computa» solo para escaleras; tooltip y drafts actualizados. `fireload.js` filtra escaleras (no LRE). Informe HTML/XLSX con textos coherentes.
  - **Validaciones**: los LRE exigen ahora Ci y qsi/qvi (o campos de depósito); las escaleras quedan exentas → el informe puede generarse. Verificado por script (LRE en zonas, escalera fuera, validación LRE, escalera sin carga OK) + smoke UI. 53/53 unit.
- 2026-07-27: **Depósitos de combustible · Ci y Ra = 1 por defecto** (la carga la da la fórmula PCI×densidad×volumen×Ci, sin incrementos). Editables.
- 2026-07-27: **Tabla 1.3.5 completa (BOE) + modal buscador de actividades (validado iter 19, 100%)**
  - `catalog.py` reescrito con la **Tabla 1.3.5 literal del RSCIEI (BOE-A-2025-7190)**: 11 categorías con texto exacto (A. OFICINAS, B. CARTÓN PAPEL, C. INDUSTRIA ALIMENTARIA, D. INDUSTRIA QUÍMICA, E. LOGÍSTICA, F. MATERIAS Y MERCANCÍAS DIVERSAS, G. TEXTILES, H. TRANSFORMACIÓN DE METALES, I. TRANSFORMACIÓN DE PLÁSTICOS, J. ARTÍCULOS DE MADERA, K. OTROS) y 158 subactividades de producción (qs MJ/m²) y almacenamiento (qv bruto y neto MJ/m³), con Ci y Rmin. Helpers `_p`/`_a` (con `qvi_neto`).
  - Nuevo **modal buscador** `ActivityCatalogDialog.jsx`: al pulsar el campo «Actividad» se abre un diálogo con caja de búsqueda que filtra por texto, agrupado por categoría, con badges Prod./Almac. y valores qs/qv·Ci·Rmin; al seleccionar una fila se rellena la estancia (actividad/subactividad/modo/qsi|qvi/Ci/Ra/Rmin) y recalcula la carga en vivo. Enlaces «Personalizada» y «Elegir de la tabla».
  - Testing: 9/9 E2E catálogo + modal + 53/53 unit. Sin issues.
- 2026-07-27: **P0 · Qs con superficie ÚTIL + depósitos de combustible (validado iter 18, 100%)**
  - Carga de fuego Qs ahora usa la **superficie útil** como denominador A y como superficie de aporte de cada estancia (`engine._compute_sector`: `A_util` para Qs, `A_const` para Tabla 2.1.1/sectorización). `calculo` expone `A` (útil) y `A_construida`. `fireload.js` replicado en cliente.
  - Nueva clasificación de estancia **modo='deposito'** (depósito de combustible), tratada como almacenamiento: `Q = PCI(MJ/kg) × densidad(kg/m³) × volumen(m³) × Ci`, sumada al numerador del Qs del sector. Combustibles precargados y editables (Gasoil 42,7/845, Gasolina 44,0/750, Fuelóleo 40,6/960, Otro). UI en `SectoresStep` (campos combustible/pci/dens_comb/volumen). Validación en `_validate`.
  - Justificación del depósito (fórmula + clasificación) en el **Resumen ejecutivo** del informe HTML (`report-depositos-just`), DOCX (bullets) y observaciones. XLSX: aporte del depósito como valor estático en la hoja Qs. Tabla de asignación muestra ahora m² útil.
  - Testing: 53/53 pytest + 6/6 E2E (iter 18) + flujo UI del depósito. Sin issues.
- 2026-07-27: **Ocupación reordenada al paso 2 y agrupada por planta** — nuevo orden del asistente: Superficies → Ocupación → Sectores (carga de fuego) → Evacuación. `OcupacionStep` reescrito: tabla agrupada por planta (mismo esquema que el paso 1) con subtotal de ocupación por planta + total; se retiró la columna Sector (los sectores se definen después). Mantiene botón IA, ocupación personalizada a mano (sin m²/persona) y nota obligatoria.
- 2026-07-24: **Carga de fuego en vivo en el paso 2** — nuevo `lib/fireload.js` (réplica cliente del motor RSCIEI). Bloque A: cada tile de sector muestra A (m² sin LRE), Qs (MJ/m²) y badge NRI que se actualizan al asignar estancias. Bloque B: columna «Carga (MJ)» con el aporte por estancia, visible con la fila contraída o expandida (LRE → «no computa»). Confirmado que «Ocupación personalizada» ya usa solo nº de personas a mano (sin m²/persona).
- 2026-07-24: **Rediseño del paso 2 (Sectores) — vista compacta y técnica**
  - Bloque A «Sectores» como mosaico compacto de tiles (grid 2-3 col, campos densos h-8); Bloque B «Asignación» como tabla densa tipo hoja de cálculo con filas expandibles (chevron) que ocultan por defecto la clasificación (LRE/Escalera) y la carga de fuego. Badges de clase (Normal/LRE/Escalera), cabeceras numeradas con divisor para diferenciar ambos bloques. Sin cambios de lógica; testids preservados. Blueprint en `design_guidelines.json`.
- 2026-07-24: **Plantas + Ocupación por planta + Propuesta IA (validado iter 17, 100%)**
  - Plantas como entidad gestionable (crear/renombrar/eliminar) en el paso 1; cuadro de superficies agrupado por planta con subtotales. Motor: `_build_superficies` devuelve `grupos`; informe y DOCX/XLSX muestran subtotales por planta.
  - Ocupación por planta: bloque de subtotales en el paso 3, en el informe y en descargables. `_build_ocupacion` devuelve `por_planta`.
  - Propuesta de ocupación con IA: botón que llama a OpenAI **gpt-4o-mini** (clave propia del usuario en `OPENAI_API_KEY`) vía emergentintegrations (`features/studies/ai.py`, endpoint `POST /studies/{id}/ai-ocupacion`); propone uso+densidad de la Tabla 2.1 CTE DB-SI y el usuario revisa/aplica en un diálogo.
- 2026-07-23: **3 observaciones del usuario (validadas iter 16 + fix informe)**
  - Números con coma: nuevo `NumberInput` (acepta coma/punto, valida y marca en rojo; expone `data-invalid`). Aplicado en todos los pasos (superficies, carga de fuego, Ci/Ra, alturas, anchuras, densidades, evacuación, DynamicField). `StudyWizardPage.goTo` bloquea el avance si hay campos inválidos.
  - Clasificación «Escalera» (antes «Escalera protegida») con 4 tipos: Abierta (solo Descendente), Protegida, Especialmente protegida, Compartimentada (con sentido Asc/Desc). Justificación automática, informe, motor RSCIEI y exportadores actualizados.
  - Ocupación personalizada: introducir ocupación a mano (nº personas) en vez de densidad, con nota obligatoria justificativa. La nota sale como tabla/pie independiente en informe HTML, DOCX y XLSX (columna Nota).
- 2026-07-23: **Fix «no me deja avanzar» (sesión larga)**: interceptor de refresco de token en `lib/api.js` (401 → `/auth/refresh` → reintento) + `goTo` con aviso en vez de fallo silencioso.
- 2026-07-22: **Exportación e informe (4 features, validadas iter 15)**
  - Expedientes: toggle vista tarjetas/tabla; multiselección con checkboxes (select-all + por fila) y borrado masivo vía `POST /api/projects/bulk-delete`.
  - Tablas DB-SI (SI1/SI3/SI6) con resultado resaltado, renderizadas POR SECTOR CTE tanto en Resultados on-screen (`ResultsPanel` MiniRefTable) como en el informe (`StudyReportPage` RefTable). Sectores industriales no muestran DB-SI.
  - Export DOCX del informe completo (`build_docx`, python-docx) — `GET /api/studies/{id}/export/docx`.
  - Export XLSX con fórmulas vivas (`build_xlsx`, openpyxl): hojas Superficies, Ocupación y una hoja Qs por sector con Aporte/Qs como fórmulas editables — `GET /api/studies/{id}/export/xlsx`.
  - Añadido render de la sección `resumen_ejecutivo` en el informe.
