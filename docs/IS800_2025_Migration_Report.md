# Technical Report: Migration of Osdag Core Design Library to Draft IS 800:2025

**Deliverable Module:** `src/osdag_core/utils/common/is800_2025.py`  
**Reference Baseline:** `src/osdag_core/utils/common/is800_2007.py` (IS 800:2007)  
**Target Standard:** Draft IS 800:2025 (Fourth Revision – General Construction in Steel)

---

## 1. Executive Summary & Objectives

This report documents the design, implementation, and verification of `is800_2025.py` for the Osdag open-source structural steel design suite. The implementation covers **22 clauses, lookup tables, and limit-state checks** across Sections 2, 3, 6, 7, 8, 9, and 10 of Draft IS 800:2025, adhering strictly to Osdag's class interface (`IS800_2025`), clause-mapped method naming, and consistent SI base units ($	ext{N}$, $	ext{mm}$, $	ext{MPa}$, $	ext{N-mm}$).

---

## 2. Implemented Clauses & Functions

| Section / Clause | Method / Constant in `IS800_2025` | Engineering Purpose |
| :--- | :--- | :--- |
| **Sec. 2 & Table 1 / 5 / 11** | `STEEL_GRADES`, `BOLT_GRADES`, `GAMMA_M0`..`GAMMA_MW_FIELD` | Material constants (E250–E650), bolt classes (4.6–12.9), and partial safety factors. |
| **Cl. 3.7 & Table 2** | `cl_3_7_epsilon()`, `cl_3_7_classify_section()` | Yield stress ratio $arepsilon = \sqrt{250/f_y}$ and cross-section classification (Plastic, Compact, Semi-compact, Slender). |
| **Cl. 3.8 & Table 3** | `cl_3_8_max_slenderness_ratio()` | Maximum permissible effective slenderness ratios ($KL/r$) by member category. |
| **Cl. 6.2 & 6.3.1** | `cl_6_2_tension_yielding()`, `cl_6_3_1_tension_rupture_plate()` | Gross-section yielding ($T_{dg}$) and net-section rupture ($T_{dn}$) with high-strength $lpha_r$ adjustment. |
| **Cl. 6.3.3 & 6.4.1** | `cl_6_3_3_tension_rupture_angle()`, `cl_6_4_1_block_shear()` | Single-angle rupture with shear-lag factor $eta$ and block shear rupture/yielding ($T_{db}$). |
| **Cl. 7.1.2 & Table 7** | `cl_7_1_2_design_compressive_stress()`, `cl_7_1_2_compression_resistance()` | Perry-Robertson buckling curves (`a0`, `a`, `b`, `c`, `d`) and axial compression capacity ($P_d$). |
| **Cl. 7.5.1.2** | `cl_7_5_1_2_single_angle_strut_equivalent_slenderness()` | Equivalent non-dimensional slenderness $\lambda_e$ for single-angle discontinuous struts. |
| **Cl. 8.2.1.2 & 8.2.2** | `cl_8_2_1_2_bending_strength()`, `cl_8_2_2_lateral_torsional_buckling_strength()` | Laterally supported and laterally unsupported (LTB) beam bending capacities ($M_d$). |
| **Cl. 8.4.1 & 8.7.4** | `cl_8_4_1_shear_capacity()`, `cl_8_7_4_web_bearing_capacity()` | Plastic web shear resistance ($V_d$) and local web bearing strength ($F_w$). |
| **Cl. 9.3.1.1** | `cl_9_3_1_1_section_strength_interaction()` | Combined axial force and biaxial bending interaction check for `I_H` and `RHS` sections. |
| **Cl. 10.2.1 – 10.3.6** | `cl_10_2_1_bolt_hole_diameter()`, `cl_10_3_3_*`, `cl_10_3_4_*`, `cl_10_3_5_*`, `cl_10_3_6_*` | Hole clearance, long-joint factor $eta_{lj}$, bolt shear, bearing, tension, and shear-tension interaction. |
| **Cl. 10.4.3** | `cl_10_4_3_hsfg_slip_resistance()` | HSFG bolt slip resistance ($V_{dsf}$) at ULS ($\gamma_{mf}=1.25$) and SLS ($\gamma_{mf}=1.10$). |
| **Cl. 10.5.7 & 10.5.10.1** | `cl_10_5_7_fillet_weld_strength()`, `cl_10_5_10_1_weld_combined_stresses()` | Shop/field fillet weld strength ($P_{dw}$) with $eta_{lw}$ reduction and combined normal/shear check. |

---

## 3. Side-by-Side Comparison: IS 800:2007 vs. Draft IS 800:2025

| Design Aspect | IS 800:2007 Provision | Draft IS 800:2025 Provision | Implementation Impact |
| :--- | :--- | :--- | :--- |
| **High-Strength Steels** | Covers grades up to E410 ($f_y \le 410	ext{ MPa}$). | Expands coverage up to **E550** and **E650** ($f_y = 650	ext{ MPa}$). | Added `E450`, `E550`, `E650` to `STEEL_GRADES` and `12.9` to `BOLT_GRADES`. |
| **Section Classification (Table 2)** | Welded outstand limits and web uniform compression limits. | Harmonizes welded outstand limits ($8.4arepsilon, 9.4arepsilon, 13.6arepsilon$) and tighter limits for high-strength steels. | Implemented `cl_3_7_classify_section()` for rolled/welded sections under bending/compression. |
| **Tension Rupture Factor ($lpha_r$)** | Fixed $lpha = 0.90$ for plates ($\ge 4$ bolts). | Applies $lpha_r = 0.85$ when $f_y > 450	ext{ MPa}$ to account for reduced $f_u/f_y$ ductility. | `cl_6_3_1_tension_rupture_plate()` automatically selects $lpha_r = 0.85$ for $f_y > 450	ext{ MPa}$. |
| **Column Buckling Curves (Table 7)** | Curves `a` ($0.21$), `b` ($0.34$), `c` ($0.49$), `d` ($0.76$). | Adds buckling curve **`a0`** ($lpha = 0.13$) for hot-finished hollow sections and high-strength grades. | Added `"a0": 0.13` to `IMPERFECTION_FACTORS` in `cl_7_1_2_design_compressive_stress()`. |
| **LTB Plateau & Long Welds** | Standard LTB curve and long-weld reduction $eta_{lw}$ for $l_w > 150 t_t$. | Retains $\lambda_{LT} \le 0.4$ plateau and enforces $eta_{lw} = 1.2 - rac{0.2 l_w}{150 t_t} \ge 0.6$. | Implemented in `cl_8_2_2_lateral_torsional_buckling_strength()` and `cl_10_5_7_fillet_weld_strength()`. |

---

## 4. Major Assumptions & Challenges

* **Consistent Unit System:** All routines operate purely in $	ext{N}$, $	ext{mm}$, and $	ext{MPa}$ without hidden unit scaling.
* **Parameter Centralization:** Because Draft IS 800:2025 is subject to final BIS committee ratification, all safety factors and imperfection factors are stored as class attributes for one-line maintenance.
* **Backward Compatibility:** Preserving Osdag's method signatures allows downstream connection and member design modules to toggle between IS 800:2007 and Draft IS 800:2025 cleanly.
