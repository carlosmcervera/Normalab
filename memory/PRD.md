# PRD — NormaLab (Plataforma de estudios normativos)

## Problem statement (original)
App web interna para despacho técnico de ingeniería/arquitectura. Plataforma modular de estudios normativos: módulos por normativa, crear estudio, asistente guiado, informe no vinculante. Arquitectura features-first, extensible mediante module registry. Módulos: CTE, RSCIEI, REBT, RITE, RD Accesibilidad 2023. MVP con RSCIEI operativo.

## Decisiones (user choices)
- BD: MongoDB (PostgreSQL no soportado de forma fiable en el entorno).
- Frontend: React (JS) + validación tipada (react-hook-form + zod).
- Auth: JWT propio (cookies httpOnly), roles admin/tecnico.
- Informe: vista en pantalla + PDF (window.print).
- Alcance: RSCIEI 100% operativo; CTE/REBT/RITE/ACCESS2023 registrados como placeholders.

## Arquitectura
- Backend features-first: `core/` (db, models PyObjectId/BaseDocument, security JWT, deps), `features/` (auth, projects, studies, modules), `normative_modules/` (base `NormativeModule`, `ModuleRegistry`, `rsciei/` con engine+schema+report, `placeholders.py`).
- Module registry: cada normativa es un módulo desacoplado (meta, schema/wizard, compute, build_report). Añadir normativa = crear clase + registrarla en `bootstrap_modules()`.
- Frontend features-first: `features/{auth,dashboard,projects,studies,modules}`, wizard schema-driven (`/modules/{code}/schema`).
- Preparado para multitenancy futuro y RAG/IA (módulos encapsulados, datos por estudio).

## Modelo de datos (Mongo)
- users(email único, password_hash bcrypt, name, role)
- projects(code, name, client, location, description, owner_id)
- studies(project_id, module_code, name, status, data, results, report, current_version)
- study_versions(study_id, version, data, results, report, note)
- login_attempts, password_reset_tokens

## RSCIEI (operativo) — RD 2267/2004
- Cálculo Qs (producción y almacenamiento), NRI (8 niveles / BAJO-MEDIO-ALTO, Tabla 1.3), sectorización superficie máx admisible (Tabla 2.1, config AV/AH/B/C) con factores fachada ×1,25 y rociadores ×2, observaciones y estado global.

## Implementado (2026-07-20)
- Auth JWT completo (login/register/me/refresh/logout, seed admin, brute force).
- Dashboard con stats y tarjetas de módulos.
- Expedientes CRUD + detalle.
- Estudios: crear, autosave, compute, versionado, listado versiones.
- Asistente RSCIEI (2 pasos + resultados) con presets de actividades y validaciones.
- Panel de resultados + Informe no vinculante imprimible (PDF) + histórico de versiones.
- Testing: backend 11/11 pytest, frontend E2E happy-path 100%.

## Backlog
- P1: Completar módulos CTE (Parte I + DB), REBT, RITE, RD Accesibilidad (schema+engine+report por módulo).
- P1: Gestión de usuarios/roles desde UI (panel admin); recuperación de contraseña por email.
- P2: Exportación PDF server-side con maquetación oficial; comparador de versiones (diff).
- P2: Integración RAG documental + IA (consultas sobre normativa, autocompletado del asistente).
- P2: Multitenancy real (organización/tenant scoping).

## Credenciales
admin@normalab.com / Admin1234! (rol admin). Ver /app/memory/test_credentials.md.

## Próximas tareas
1. Implementar segundo módulo operativo (p. ej. CTE DB-SI) para validar la extensibilidad del registry.
2. Panel de administración de usuarios/roles.
