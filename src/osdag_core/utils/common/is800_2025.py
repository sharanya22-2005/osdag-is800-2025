"""
Module: is800_2025.py
Description: Comprehensive Python implementation of structural steel design
             provisions as per Draft IS 800:2025 (Fourth Revision of IS 800 -
             General Construction in Steel - Code of Practice).
Reference:   Existing Osdag module `src/osdag_core/utils/common/is800_2007.py`
             and Draft IS 800:2025 (CED 7).

Conventions:
- Consistent SI Base Units: Forces in N, Dimensions in mm, Stresses in MPa (N/mm^2),
  Moments in N-mm.
- Clause-mapped method names (`cl_<clause_number>_<descriptive_name>`) matching
  Osdag's `IS800_2007` architectural conventions for seamless interoperability.
- Explicit docstrings documenting equations, parameter units, and Draft IS 800:2025
  revisions/assumptions relative to IS 800:2007.
"""

import math
from typing import Dict, List, Optional, Tuple


class IS800_2025:
    """
    Encapsulates Limit State Design (LSD) provisions for structural steel
    elements and connections conforming to Draft IS 800:2025.
    """

    # =========================================================================
    # SECTION 2 & TABLE 1 / TABLE 5: MATERIALS & PARTIAL SAFETY FACTORS
    # =========================================================================

    # Partial Safety Factors for Materials (Table 5, Draft IS 800:2025)
    GAMMA_M0: float = 1.10          # Resistance governed by yielding / buckling
    GAMMA_M1: float = 1.25          # Resistance governed by ultimate stress (fracture)
    GAMMA_MB_BEARING: float = 1.25  # Bolts - bearing type (shop & field)
    GAMMA_MB_HSFG: float = 1.25     # HSFG bolts - slip resistance at ultimate load
    GAMMA_MB_HSFG_SLS: float = 1.10 # HSFG bolts - slip resistance at serviceability load
    GAMMA_MW_SHOP: float = 1.25     # Shop welds
    GAMMA_MW_FIELD: float = 1.50    # Field / site welds

    # Standard Elastic Constants (Clause 2.2.4.1)
    MODULUS_OF_ELASTICITY: float = 200000.0  # E = 2.0 x 10^5 MPa
    POISSON_RATIO: float = 0.30              # mu = 0.30 (elastic range)
    SHEAR_MODULUS: float = 76923.08          # G = E / [2 * (1 + mu)] MPa
    THERMAL_EXPANSION: float = 12e-6         # alpha_t = 12 x 10^-6 / deg C

    # Imperfection Factors (alpha) for Buckling Curves (Table 7, Draft IS 800:2025)
    IMPERFECTION_FACTORS: Dict[str, float] = {
        "a0": 0.13,  # New in Draft IS 800:2025 for hot-finished hollow sections & high-strength grades
        "a": 0.21,
        "b": 0.34,
        "c": 0.49,
        "d": 0.76,
    }

    # Structural Steel Grades per IS 2062 / Draft IS 800:2025 Table 1
    STEEL_GRADES: Dict[str, Dict[str, float]] = {
        "E250": {"fy": 250.0, "fu": 410.0, "E": 200000.0},
        "E300": {"fy": 300.0, "fu": 440.0, "E": 200000.0},
        "E350": {"fy": 350.0, "fu": 490.0, "E": 200000.0},
        "E410": {"fy": 410.0, "fu": 540.0, "E": 200000.0},
        "E450": {"fy": 450.0, "fu": 570.0, "E": 200000.0},
        "E550": {"fy": 550.0, "fu": 650.0, "E": 200000.0},  # High-strength steel added in 2025 Draft
        "E650": {"fy": 650.0, "fu": 750.0, "E": 200000.0},  # High-strength steel added in 2025 Draft
    }

    # Bolt Property Classes (IS 1367 / Draft IS 800:2025 Table 11)
    BOLT_GRADES: Dict[str, Dict[str, float]] = {
        "4.6":  {"fyb": 240.0, "fub": 400.0},
        "4.8":  {"fyb": 320.0, "fub": 400.0},
        "5.6":  {"fyb": 300.0, "fub": 500.0},
        "5.8":  {"fyb": 400.0, "fub": 500.0},
        "6.8":  {"fyb": 480.0, "fub": 600.0},
        "8.8":  {"fyb": 640.0, "fub": 800.0},
        "10.9": {"fyb": 900.0, "fub": 1000.0},
        "12.9": {"fyb": 1080.0, "fub": 1200.0},  # Ultra-high-strength bolt class
    }

    # =========================================================================
    # SECTION 3: GENERAL DESIGN REQUIREMENTS & SECTION CLASSIFICATION
    # =========================================================================

    @staticmethod
    def cl_3_7_epsilon(fy: float) -> float:
        """
        Yield stress ratio parameter epsilon (Table 2, Draft IS 800:2025).

        Formula:
            epsilon = sqrt(250 / fy)

        Args:
            fy (float): Characteristic yield stress of steel (MPa).

        Returns:
            float: Dimensionless yield stress ratio epsilon.
        """
        if fy <= 0:
            raise ValueError("Yield stress fy must be greater than zero.")
        return math.sqrt(250.0 / fy)

    @classmethod
    def cl_3_7_classify_section(
        cls,
        b: float,
        tf: float,
        d: float,
        tw: float,
        fy: float,
        section_type: str = "rolled",
        loading: str = "bending",
    ) -> str:
        """
        Classify cross-section into Class 1 (Plastic), Class 2 (Compact),
        Class 3 (Semi-compact), or Class 4 (Slender) per Table 2, Draft IS 800:2025.

        Draft IS 800:2025 Update:
        Harmonizes welded outstand flange limits (8.4*eps, 9.4*eps, 13.6*eps) and
        internal web compression limits (33*eps, 38*eps, 42*eps) to safely accommodate
        high-strength steels up to E650.

        Args:
            b (float): Outstand width of compression flange (mm).
            tf (float): Flange thickness (mm).
            d (float): Clear depth of web between fillets/welds (mm).
            tw (float): Web thickness (mm).
            fy (float): Yield stress (MPa).
            section_type (str): 'rolled' or 'welded'.
            loading (str): 'bending' or 'compression'.

        Returns:
            str: Section classification ('Plastic', 'Compact', 'Semi-compact', or 'Slender').
        """
        if min(b, tf, d, tw) <= 0:
            raise ValueError("Section dimensions must be strictly positive.")

        eps = cls.cl_3_7_epsilon(fy)
        flange_ratio = b / tf
        web_ratio = d / tw

        if section_type.lower() == "rolled":
            f_limits = (9.4 * eps, 10.5 * eps, 15.7 * eps)
        elif section_type.lower() == "welded":
            f_limits = (8.4 * eps, 9.4 * eps, 13.6 * eps)
        else:
            raise ValueError("section_type must be 'rolled' or 'welded'.")

        if loading.lower() == "bending":
            w_limits = (84.0 * eps, 105.0 * eps, 126.0 * eps)
        elif loading.lower() == "compression":
            w_limits = (33.0 * eps, 38.0 * eps, 42.0 * eps)
        else:
            raise ValueError("loading must be 'bending' or 'compression'.")

        def _classify_element(ratio: float, limits: Tuple[float, float, float]) -> int:
            if ratio <= limits[0]:
                return 1
            if ratio <= limits[1]:
                return 2
            if ratio <= limits[2]:
                return 3
            return 4

        governing = max(
            _classify_element(flange_ratio, f_limits),
            _classify_element(web_ratio, w_limits),
        )
        return {1: "Plastic", 2: "Compact", 3: "Semi-compact", 4: "Slender"}[governing]

    @staticmethod
    def cl_3_8_max_slenderness_ratio(member_type: str) -> float:
        """
        Maximum permissible effective slenderness ratios (KL/r) per Table 3,
        Draft IS 800:2025.
        """
        limits = {
            "compression_dead_live": 180.0,
            "compression_wind_only": 250.0,
            "compression_flange_restrained": 300.0,
            "tension_reversal_wind": 350.0,
            "tie_or_bracing": 400.0,
        }
        key = member_type.lower()
        if key not in limits:
            raise ValueError(f"Unknown member_type '{member_type}'. Valid keys: {list(limits.keys())}")
        return limits[key]

    # =========================================================================
    # SECTION 6: DESIGN OF TENSION MEMBERS
    # =========================================================================

    @classmethod
    def cl_6_2_tension_yielding(
        cls,
        Ag: float,
        fy: float,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design strength due to yielding of gross section (Clause 6.2)."""
        return (Ag * fy) / gamma_m0

    @classmethod
    def cl_6_3_1_tension_rupture_plate(
        cls,
        An: float,
        fu: float,
        fy: float,
        gamma_m1: float = GAMMA_M1,
        is_high_strength: bool = False,
    ) -> float:
        """
        Design strength due to rupture of critical section for plates (Clause 6.3.1).
        Uses alpha_r = 0.85 for high-strength steels (fy > 450 MPa) and 0.90 otherwise.
        """
        alpha_r = 0.85 if (fy > 450.0 or is_high_strength) else 0.90
        return (alpha_r * An * fu) / gamma_m1

    @classmethod
    def cl_6_3_3_tension_rupture_angle(
        cls,
        Anc: float,
        Ago: float,
        fy: float,
        fu: float,
        w: float,
        t: float,
        bs: float,
        Lc: float,
        gamma_m0: float = GAMMA_M0,
        gamma_m1: float = GAMMA_M1,
    ) -> float:
        """Design strength due to rupture of single angle connected through one leg (Clause 6.3.3)."""
        if Lc <= 0 or t <= 0:
            raise ValueError("Connection length Lc and leg thickness t must be positive.")

        beta_raw = 1.4 - 0.076 * (w / t) * (fy / fu) * (bs / Lc)
        beta_max = (fu * gamma_m0) / (fy * gamma_m1)
        beta = max(0.7, min(beta_raw, beta_max))

        return (0.9 * Anc * fu) / gamma_m1 + (beta * Ago * fy) / gamma_m0

    @classmethod
    def cl_6_4_1_block_shear(
        cls,
        Avg: float,
        Avn: float,
        Atg: float,
        Atn: float,
        fy: float,
        fu: float,
        gamma_m0: float = GAMMA_M0,
        gamma_m1: float = GAMMA_M1,
    ) -> float:
        """Design block shear strength (Clause 6.4.1, Draft IS 800:2025)."""
        tdb1 = (Avg * fy) / (math.sqrt(3.0) * gamma_m0) + (0.9 * Atn * fu) / gamma_m1
        tdb2 = (0.9 * Avn * fu) / (math.sqrt(3.0) * gamma_m1) + (Atg * fy) / gamma_m0
        return min(tdb1, tdb2)

    # =========================================================================
    # SECTION 7: DESIGN OF COMPRESSION MEMBERS
    # =========================================================================

    @classmethod
    def cl_7_1_2_design_compressive_stress(
        cls,
        fy: float,
        kl_r: float,
        buckling_curve: str = "b",
        E: float = MODULUS_OF_ELASTICITY,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """
        Design compressive stress fcd (Clause 7.1.2.1 & Table 7, Draft IS 800:2025).
        Supports buckling curves 'a0' (0.13), 'a' (0.21), 'b' (0.34), 'c' (0.49), 'd' (0.76).
        """
        if kl_r <= 0:
            raise ValueError("Slenderness ratio KL/r must be greater than zero.")
        curve_key = buckling_curve.lower()
        if curve_key not in cls.IMPERFECTION_FACTORS:
            raise ValueError(
                f"Invalid buckling curve '{buckling_curve}'. Valid options: {list(cls.IMPERFECTION_FACTORS.keys())}"
            )

        alpha = cls.IMPERFECTION_FACTORS[curve_key]
        fcc = (math.pi ** 2 * E) / (kl_r ** 2)
        lambda_bar = math.sqrt(fy / fcc)

        if lambda_bar <= 0.2:
            chi = 1.0
        else:
            phi = 0.5 * (1.0 + alpha * (lambda_bar - 0.2) + lambda_bar ** 2)
            chi = 1.0 / (phi + math.sqrt(max(0.0, phi ** 2 - lambda_bar ** 2)))
            chi = min(chi, 1.0)

        return (fy / gamma_m0) * chi

    @classmethod
    def cl_7_1_2_compression_resistance(
        cls,
        Ae: float,
        fy: float,
        kl_r: float,
        buckling_curve: str = "b",
        E: float = MODULUS_OF_ELASTICITY,
    ) -> float:
        """Design axial compressive resistance Pd = Ae * fcd (Clause 7.1.2)."""
        fcd = cls.cl_7_1_2_design_compressive_stress(fy, kl_r, buckling_curve, E)
        return Ae * fcd

    @classmethod
    def cl_7_5_1_2_single_angle_strut_equivalent_slenderness(
        cls,
        l: float,
        rvv: float,
        b1: float,
        b2: float,
        t: float,
        fy: float,
        k1: float,
        k2: float,
        k3: float,
        E: float = MODULUS_OF_ELASTICITY,
    ) -> float:
        """Equivalent slenderness ratio lambda_e for single angle struts (Clause 7.5.1.2)."""
        eps = cls.cl_3_7_epsilon(fy)
        denom = eps * math.sqrt((math.pi ** 2 * E) / 250.0)
        lambda_vv = (l / rvv) / denom
        lambda_phi = ((b1 + b2) / (2.0 * t)) / denom
        return math.sqrt(k1 + k2 * (lambda_vv ** 2) + k3 * (lambda_phi ** 2))

    # =========================================================================
    # SECTION 8: DESIGN OF MEMBERS SUBJECTED TO BENDING & SHEAR
    # =========================================================================

    @classmethod
    def cl_8_2_1_2_bending_strength(
        cls,
        Zp: float,
        Ze: float,
        fy: float,
        section_class: str,
        is_cantilever: bool = False,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design bending strength Md of laterally supported beams (Clause 8.2.1.2)."""
        s_class = section_class.lower()
        if s_class in ("plastic", "compact"):
            beta_b = 1.0
        elif s_class == "semi-compact":
            beta_b = Ze / Zp
        else:
            raise ValueError("Slender (Class 4) sections require effective section modulus calculation.")

        md_raw = (beta_b * Zp * fy) / gamma_m0
        limit_factor = 1.5 if is_cantilever else 1.2
        md_limit = (limit_factor * Ze * fy) / gamma_m0
        return min(md_raw, md_limit)

    @classmethod
    def cl_8_2_2_lateral_torsional_buckling_strength(
        cls,
        Zp: float,
        Ze: float,
        fy: float,
        Mcr: float,
        section_class: str,
        is_welded: bool = False,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design bending strength Md of laterally unsupported beams (Clause 8.2.2)."""
        if Mcr <= 0:
            raise ValueError("Elastic critical moment Mcr must be positive.")

        s_class = section_class.lower()
        if s_class in ("plastic", "compact"):
            beta_b = 1.0
        elif s_class == "semi-compact":
            beta_b = Ze / Zp
        else:
            raise ValueError("Slender (Class 4) sections require effective section modulus calculation.")

        alpha_lt = 0.49 if is_welded else 0.21
        lambda_lt = math.sqrt((beta_b * Zp * fy) / Mcr)

        if lambda_lt <= 0.4:
            chi_lt = 1.0
        else:
            phi_lt = 0.5 * (1.0 + alpha_lt * (lambda_lt - 0.2) + lambda_lt ** 2)
            chi_lt = 1.0 / (phi_lt + math.sqrt(max(0.0, phi_lt ** 2 - lambda_lt ** 2)))
            chi_lt = min(chi_lt, 1.0)

        fbd = (chi_lt * fy) / gamma_m0
        return beta_b * Zp * fbd

    @classmethod
    def cl_8_4_1_shear_capacity(
        cls,
        Av: float,
        fyw: float,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design plastic shear resistance Vd (Clause 8.4.1, Draft IS 800:2025)."""
        return (Av * fyw) / (math.sqrt(3.0) * gamma_m0)

    @classmethod
    def cl_8_7_4_web_bearing_capacity(
        cls,
        b1: float,
        n2: float,
        tw: float,
        fyw: float,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design local bearing strength of web against concentrated loads (Clause 8.7.4)."""
        return ((b1 + n2) * tw * fyw) / gamma_m0

    # =========================================================================
    # SECTION 9: COMBINED AXIAL FORCE AND BENDING MOMENT
    # =========================================================================

    @staticmethod
    def cl_9_3_1_1_section_strength_interaction(
        N: float,
        Nd: float,
        My: float,
        Mdy: float,
        Mz: float,
        Mdz: float,
        section_type: str = "I_H",
    ) -> Tuple[float, bool]:
        """Combined axial force and biaxial bending section strength check (Clause 9.3.1.1)."""
        n = abs(N) / Nd if Nd > 0 else 0.0
        if n >= 1.0:
            return (float("inf"), False)

        s_type = section_type.upper()
        if s_type == "I_H":
            alpha1 = max(1.0, 5.0 * n)
            alpha2 = 2.0
        elif s_type == "RHS":
            val = 1.66 / (1.0 - 1.13 * (n ** 2))
            alpha1 = min(6.0, val)
            alpha2 = min(6.0, val)
        else:
            alpha1, alpha2 = 1.0, 1.0

        ratio_y = (abs(My) / Mdy) ** alpha1 if Mdy > 0 else 0.0
        ratio_z = (abs(Mz) / Mdz) ** alpha2 if Mdz > 0 else 0.0
        interaction = ratio_y + ratio_z
        return (interaction, interaction <= 1.0)

    # =========================================================================
    # SECTION 10: CONNECTIONS (BOLTED, HSFG, & WELDED)
    # =========================================================================

    @staticmethod
    def cl_10_2_1_bolt_hole_diameter(d: float, hole_type: str = "standard") -> float:
        """Standard clearance bolt hole diameter d0 per Table 19, Draft IS 800:2025."""
        if d <= 14.0:
            clearance = 1.0 if hole_type == "standard" else 3.0
        elif d <= 24.0:
            clearance = 2.0 if hole_type == "standard" else 4.0
        else:
            clearance = 3.0 if hole_type == "standard" else 6.0
        return d + clearance

    @classmethod
    def cl_10_3_3_bolt_shear_capacity(
        cls,
        fub: float,
        nn: int,
        ns: int,
        Anb: float,
        Asb: float,
        beta_lj: float = 1.0,
        beta_lg: float = 1.0,
        beta_pk: float = 1.0,
        gamma_mb: float = GAMMA_MB_BEARING,
    ) -> float:
        """Design shear capacity of a bearing-type bolt Vdsb (Clause 10.3.3)."""
        vnsb = (fub / math.sqrt(3.0)) * (nn * Anb + ns * Asb)
        return (vnsb / gamma_mb) * beta_lj * beta_lg * beta_pk

    @staticmethod
    def cl_10_3_3_1_long_joint_factor(lj: float, d: float) -> float:
        """Reduction factor beta_lj for long bolted joints when lj > 15 * d (Clause 10.3.3.1)."""
        if lj <= 15.0 * d:
            return 1.0
        beta = 1.075 - (lj / (200.0 * d))
        return max(0.75, min(1.0, beta))

    @classmethod
    def cl_10_3_4_bolt_bearing_capacity(
        cls,
        d: float,
        t: float,
        fu: float,
        fub: float,
        e: float,
        p: float,
        d0: float,
        gamma_mb: float = GAMMA_MB_BEARING,
    ) -> float:
        """Design bearing capacity of a bolt Vdpb (Clause 10.3.4, Draft IS 800:2025)."""
        kb_terms = [e / (3.0 * d0), fub / fu, 1.0]
        if p > 0:
            kb_terms.append((p / (3.0 * d0)) - 0.25)
        kb = min(kb_terms)

        vnpb = 2.5 * kb * d * t * fu
        return vnpb / gamma_mb

    @classmethod
    def cl_10_3_5_bolt_tension_capacity(
        cls,
        fub: float,
        fyb: float,
        Anb: float,
        Asb: float,
        gamma_mb: float = GAMMA_MB_BEARING,
        gamma_m0: float = GAMMA_M0,
    ) -> float:
        """Design tensile capacity of a bolt Tdb (Clause 10.3.5, Draft IS 800:2025)."""
        tnb_rupture = 0.90 * fub * Anb
        tnb_yield_cap = fyb * Asb * (gamma_mb / gamma_m0)
        tnb = min(tnb_rupture, tnb_yield_cap)
        return tnb / gamma_mb

    @staticmethod
    def cl_10_3_6_bolt_combined_shear_tension(
        Vsb: float,
        Vdsb: float,
        Tb: float,
        Tdb: float,
    ) -> Tuple[float, bool]:
        """Interaction check for bearing bolts under combined shear & tension (Clause 10.3.6)."""
        ratio = (Vsb / Vdsb) ** 2 + (Tb / Tdb) ** 2
        return (ratio, ratio <= 1.0)

    @classmethod
    def cl_10_4_3_hsfg_slip_resistance(
        cls,
        mu_f: float,
        ne: int,
        Kh: float,
        fub: float,
        Anb: float,
        is_ultimate_limit_state: bool = True,
    ) -> float:
        """Design slip resistance Vdsf of HSFG bolts (Clause 10.4.3, Draft IS 800:2025)."""
        fo = 0.70 * fub * Anb
        vnsf = mu_f * ne * Kh * fo
        gamma_mf = cls.GAMMA_MB_HSFG if is_ultimate_limit_state else cls.GAMMA_MB_HSFG_SLS
        return vnsf / gamma_mf

    @classmethod
    def cl_10_5_7_fillet_weld_strength(
        cls,
        s: float,
        lw: float,
        fu: float,
        K: float = 0.70,
        is_field_weld: bool = False,
        beta_lw: float = 1.0,
    ) -> float:
        """Design strength of a fillet weld Pdw (Clause 10.5.7.1 & 10.5.7.3)."""
        tt = K * s
        gamma_mw = cls.GAMMA_MW_FIELD if is_field_weld else cls.GAMMA_MW_SHOP

        if beta_lw == 1.0 and lw > 150.0 * tt:
            beta_lw = max(0.6, 1.2 - (0.2 * lw) / (150.0 * tt))

        fwd = fu / (math.sqrt(3.0) * gamma_mw)
        return lw * tt * fwd * beta_lw

    @staticmethod
    def cl_10_5_10_1_weld_combined_stresses(
        fa: float,
        q: float,
        fu: float,
        gamma_mw: float = GAMMA_MW_SHOP,
    ) -> Tuple[float, bool]:
        """Equivalent stress check for fillet welds under combined stresses (Clause 10.5.10.1.1)."""
        fe = math.sqrt((fa ** 2) + 3.0 * (q ** 2))
        fwd = fu / (math.sqrt(3.0) * gamma_mw)
        return (fe, fe <= fwd)
