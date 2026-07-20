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
- P1: Bloque de evacuación ampliado (recorridos reales por origen, coeficientes nota 4/5 Tabla 2.3.1).
- P1: Completar Tabla 1.3.5 exhaustiva del catálogo de actividades + Rmin por actividad.
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
