# Antenna 3D Pattern Generator 📡

This project implements a system for generating **3D antenna radiation patterns** from partial data sources, such as:

* **2D radiation pattern images** extracted from antenna datasheets (`.png`).
* **Analytical equations** describing radiation pattern views.

The system reconstructs an approximated 3D radiation pattern and provides interactive visualization, analysis, and export capabilities.

---

## Objectives

- [ ] Reconstruct a 3D radiation pattern from partial 2D inputs.
- [ ] Support multiple input modalities (image-based and equation-based).
- [ ] Visualize the generated pattern interactively.
- [ ] Evaluate reconstruction accuracy using quantitative metrics.
- [ ] Export generated 3D mesh data in structured formats (e.g., JSON).

---

## System Architecture


```text
antenna-3D-pattern-generator/
│
├── client/        # Frontend (React + Three.js)
├── server/        # Backend (Node.js API)
└── docs/          # Documentation and academic material