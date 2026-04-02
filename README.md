# Local Volunteer Coordination Platform
# 🎓 Plataforma de Coordinación de Voluntariado Educativo Comunitario

> Sistema digital para conectar voluntarios con proyectos de apoyo académico en comunidades locales de Bogotá, D.C., Colombia.

---

## 📋 Descripción del Proyecto

Esta plataforma busca optimizar la asignación de voluntarios a proyectos de tutoría y apoyo educativo dirigidos a niños y adolescentes en comunidades vulnerables. A través de un algoritmo de compatibilidad ponderado, el sistema conecta la oferta de talento voluntario con la demanda de apoyo académico, transformando un proceso manual y desorganizado en un sistema digital eficiente y trazable.

**Universidad Distrital Francisco José de Caldas — Ingeniería de Sistemas**  
**Asignatura:** Análisis y Diseño de Sistemas  
**Docente:** Carlos Andrés Sierra, M.Sc  
**Semestre:** 2026-1

### Autores

| Nombre | Código |
|---|---|
| Jose Luis Leudo Mosquera | 20251020148 |
| David Santiago Rojas Hernández | 20251020153 |
| Adrian Mauricio Hernández Ortiz | 20251020147 |
| Johan Sebastian Candia Marín | 20251020139 |

---

## 🎯 Objetivos del Sistema

- **Reducir tiempos de asignación** entre voluntarios e instituciones educativas
- **Mejorar la compatibilidad** entre habilidades del voluntario y necesidades del proyecto
- **Garantizar coordinación efectiva de horarios** sin conflictos de disponibilidad
- **Medir el impacto académico** generado por las sesiones de tutoría
- Contribuir a la **reducción de la deserción escolar** en comunidades vulnerables

---

## ⚙️ Funcionalidades Principales

### Requerimientos Funcionales

| ID | Requerimiento | Prioridad |
|---|---|---|
| RF-01 | Registro de voluntarios (habilidades, experiencia, disponibilidad, ubicación) | Alta |
| RF-02 | Registro de instituciones educativas con definición de necesidad académica | Alta |
| RF-03 | Algoritmo de compatibilidad ponderado (habilidad, horario, ubicación, experiencia) | **Crítica** |
| RF-04 | Coordinación de horarios sin conflictos y confirmación de sesiones | Alta |
| RF-05 | Indicadores de seguimiento de sesiones y medición de impacto académico | Media |
| RF-06 | Generación de reportes (horas voluntario, resultados de sesiones, tasas de mejora) | Media |
| RF-07 | Sistema de notificaciones (correo electrónico) para confirmaciones y recordatorios | Alta |
| RF-08 | Panel de administración para supervisión, cancelaciones y configuración | Media |

---

## 🧠 Algoritmo de Compatibilidad

El núcleo del sistema es un algoritmo que calcula un puntaje de compatibilidad compuesto `C(v, p)` para cada par voluntario–proyecto:

```
C(v, p) = w1·Skill(v,p) + w2·Schedule(v,p) + w3·Location(v,p) + w4·Experience(v,p)
```

| Componente | Descripción | Peso por defecto | Fuente de datos |
|---|---|---|---|
| `Skill(v,p)` | Coincidencia entre competencias del voluntario y necesidades del proyecto | **w1 = 0.40** | Encuesta P2 + Registro del proyecto |
| `Schedule(v,p)` | Porcentaje de franjas horarias requeridas cubiertas por la disponibilidad del voluntario | **w2 = 0.30** | Encuesta P5, P6 |
| `Location(v,p)` | Puntaje de proximidad geográfica (presencial) o calidad de conectividad (virtual) | **w3 = 0.15** | Encuesta P7 + dirección institución |
| `Experience(v,p)` | Puntaje de experiencia pedagógica mapeado al nivel de los estudiantes | **w4 = 0.15** | Encuesta P4 |

---

## 🏗️ Arquitectura del Sistema

El sistema está estructurado en **tres capas** para garantizar separación de responsabilidades, escalabilidad independiente y mantenimiento modular:

```
┌─────────────────────────────────────────────────────────┐
│                   CAPA DE PRESENTACIÓN                  │
│  Portal Voluntario │ Portal Institución │ Dashboard Admin│
│                    Reportes y Analytics                 │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    CAPA DE APLICACIÓN                   │
│  Registro Voluntario │ Registro Institución             │
│  Algoritmo de Matching │ Motor de Programación          │
│                   Monitor de Impacto                    │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                      CAPA DE DATOS                      │
│  DB Perfiles Voluntarios │ DB Proyectos y Horarios      │
│  DB Registro de Sesiones │ Repositorio Analytics        │
│          (Google Sheets API — fase inicial)             │
└─────────────────────────────────────────────────────────┘
```

> **Nota:** Dado el alcance inicial del proyecto, se utilizará **Google Sheets como base de datos temporal** a través de la API de Google Sheets, que permite lectura y escritura de datos desde Python.

---

## 🗺️ Plan de Implementación

### Fase 1 — Fundamentos del Sistema
- [ ] Configuración del repositorio en GitHub con pipeline CI/CD
- [ ] Implementación de módulos de registro de voluntarios e instituciones
- [ ] Despliegue del esquema de Google Sheets como base de datos temporal

### Fase 2 — Motor de Matching
- [ ] Desarrollo y pruebas unitarias del algoritmo de compatibilidad
- [ ] Integración con las bases de datos de voluntarios y proyectos
- [ ] Exposición del endpoint de matching con resultados ordenados por compatibilidad

### Fase 3 — Programación y Notificaciones
- [ ] Motor de programación de horarios sin conflictos
- [ ] Flujo de confirmación de sesiones
- [ ] Integración de servicio de notificaciones por correo y SMS

### Fase 4 — Monitoreo de Impacto y Reportes
- [ ] Formularios de registro de sesiones para voluntarios y organizaciones
- [ ] Métricas de impacto (tasa de asistencia, % mejora académica, horas voluntariado)
- [ ] Generación de reportes periódicos

---

## 🛡️ Gestión de Riesgos

| Factor de Sensibilidad | Referencia | Mecanismo de Mitigación |
|---|---|---|
| Variabilidad en oferta de voluntarios | Workshop 1 - Sec. 3.2 | Cola de espera y asignaciones temporales |
| Conflictos de horario | Workshop 1 - Sec. 3.2 | Detección de conflictos antes de confirmar |
| Baja conectividad en comunidades | Workshop 1 - Sec. 2.5 | App con registro de sesiones en modo offline |
| Cambios en demanda estudiantil | Workshop 1 - Sec. 3.4 | Reportes semanales/mensuales en picos de demanda |

---

## 📊 Métricas de Rendimiento

| Métrica | Objetivo |
|---|---|
| Tiempo de respuesta del matching voluntario–estudiante | < 1 minuto |
| Disponibilidad del sistema (mensual) | > 90% |
| Precisión de asignación (satisfacción voluntario y estudiante) | > 80% retroalimentación positiva |
| Reducción de deserción escolar | Tendencia a la baja |

### Estrategia de Calidad
- **Pruebas unitarias** para todas las funciones del algoritmo
- **Pruebas de integración** en diferentes escenarios
- **Pruebas de carga** con simulaciones de 100+ usuarios concurrentes
- **Pruebas de usabilidad** con sesiones piloto con estudiantes de la UD
- **Monitoreo continuo** con alertas automáticas para tasas de error

---

## 📦 Tecnologías Utilizadas

| Tecnología | Uso |
|---|---|
| Python | Backend y lógica del algoritmo de matching |
| Google Sheets API | Base de datos temporal (fase inicial) |
| GitHub Actions | CI/CD — integración y despliegue continuo |
| Google Forms | Recolección de datos de encuesta |

---

## 📁 Estructura del Repositorio

```
📦 volunteer-coordination-platform
 ┣ 📂 src/
 ┃ ┣ 📂 matching/          # Algoritmo de compatibilidad C(v,p)
 ┃ ┣ 📂 registration/      # Módulos de registro (voluntarios e instituciones)
 ┃ ┣ 📂 scheduling/        # Motor de programación sin conflictos
 ┃ ┣ 📂 notifications/     # Servicio de correo y SMS
 ┃ ┗ 📂 reporting/         # Generación de reportes e indicadores
 ┣ 📂 tests/               # Pruebas unitarias e integración
 ┣ 📂 docs/                # Documentación (Workshops, diagramas)
 ┣ 📂 data/                # Esquemas de Google Sheets y datos de ejemplo
 ┣ 📜 README.md
 ┗ 📜 requirements.txt
```

---

## 🚀 Cómo Empezar

```bash
# 1. Clonar el repositorio
git clone https://github.com/<usuario>/volunteer-coordination-platform.git
cd volunteer-coordination-platform

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar credenciales de Google Sheets API
# Colocar el archivo credentials.json en la raíz del proyecto

# 4. Ejecutar el módulo principal
python src/main.py
```

---

## 📄 Documentación

- [Workshop 1 — Análisis del Sistema](docs/workshop_1_systems_analysis_and_design.pdf)
- [Workshop 2 — Diseño del Sistema](docs/workshop_2_systems_analysis_and_design.pdf)

---

## 📬 Contacto

Para preguntas relacionadas con el proyecto, por favor contactar a través de los canales académicos de la **Universidad Distrital Francisco José de Caldas**.

---

*Proyecto académico — Análisis y Diseño de Sistemas, 2026-1*
