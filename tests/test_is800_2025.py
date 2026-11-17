"""
Comprehensive Unit Test Suite for Draft IS 800:2025 Implementation (`is800_2025.py`).
Covers all 22 clauses, lookup tables, and design checks across Sections 2, 3, 6, 7, 8, 9, and 10.
Run using: python -m pytest -v
"""

import math
import pytest
from src.osdag_core.utils.common.is800_2025 import IS800_2025


def test_materials_and_slenderness_limits():
    assert math.isclose(IS800_2025.cl_3_7_epsilon(250.0), 1.0, rel_tol=1e-6)
    assert math.isclose(IS800_2025.cl_3_7_epsilon(350.0), math.sqrt(250.0 / 350.0), rel_tol=1e-6)
    assert IS800_2025.cl_3_8_max_slenderness_ratio("compression_dead_live") == 180.0
    assert IS800_2025.cl_3_8_max_slenderness_ratio("tie_or_bracing") == 400.0
    with pytest.raises(ValueError):
        IS800_2025.cl_3_7_epsilon(0.0)


def test_section_classification():
    cls_res = IS800_2025.cl_3_7_classify_section(
        b=75.0, tf=10.0, d=250.0, tw=7.0, fy=250.0, section_type="rolled", loading="bending"
    )
    assert cls_res == "Plastic"

    cls_hs = IS800_2025.cl_3_7_classify_section(
        b=75.0, tf=10.0, d=250.0, tw=7.0, fy=550.0, section_type="rolled", loading="bending"
    )
    assert cls_hs in ("Compact", "Semi-compact")


def test_tension_members():
    tdg = IS800_2025.cl_6_2_tension_yielding(Ag=2000.0, fy=250.0)
    assert math.isclose(tdg, 454545.4545, rel_tol=1e-4)

    tdn_std = IS800_2025.cl_6_3_1_tension_rupture_plate(An=1600.0, fu=410.0, fy=250.0)
    tdn_hs = IS800_2025.cl_6_3_1_tension_rupture_plate(An=1600.0, fu=650.0, fy=550.0)
    assert math.isclose(tdn_std, 0.90 * 1600.0 * 410.0 / 1.25, rel_tol=1e-5)
    assert math.isclose(tdn_hs, 0.85 * 1600.0 * 650.0 / 1.25, rel_tol=1e-5)

    tdn_angle = IS800_2025.cl_6_3_3_tension_rupture_angle(
        Anc=400.0, Ago=350.0, fy=250.0, fu=410.0, w=65.0, t=6.0, bs=65.0, Lc=180.0
    )
    assert tdn_angle > 0

    tdb = IS800_2025.cl_6_4_1_block_shear(
        Avg=1200.0, Avn=840.0, Atg=500.0, Atn=320.0, fy=250.0, fu=410.0
    )
    assert tdb > 0


def test_compression_and_angle_struts():
    fcd_a0 = IS800_2025.cl_7_1_2_design_compressive_stress(fy=350.0, kl_r=80.0, buckling_curve="a0")
    fcd_b = IS800_2025.cl_7_1_2_design_compressive_stress(fy=350.0, kl_r=80.0, buckling_curve="b")
    fcd_c = IS800_2025.cl_7_1_2_design_compressive_stress(fy=350.0, kl_r=80.0, buckling_curve="c")
    assert fcd_a0 > fcd_b > fcd_c

    lambda_e = IS800_2025.cl_7_5_1_2_single_angle_strut_equivalent_slenderness(
        l=1500.0, rvv=12.5, b1=65.0, b2=65.0, t=6.0, fy=250.0, k1=0.75, k2=0.35, k3=20.0
    )
    assert lambda_e > 0


def test_bending_ltb_shear_and_web_bearing():
    md = IS800_2025.cl_8_2_1_2_bending_strength(
        Zp=600e3, Ze=450e3, fy=250.0, section_class="Plastic", is_cantilever=False
    )
    assert math.isclose(md, 1.2 * 450e3 * 250.0 / 1.10, rel_tol=1e-5)

    md_ltb = IS800_2025.cl_8_2_2_lateral_torsional_buckling_strength(
        Zp=600e3, Ze=450e3, fy=250.0, Mcr=180e6, section_class="Plastic", is_welded=False
    )
    assert 0 < md_ltb <= (600e3 * 250.0 / 1.10)

    vd = IS800_2025.cl_8_4_1_shear_capacity(Av=2400.0, fyw=250.0)
    assert math.isclose(vd, (2400.0 * 250.0) / (math.sqrt(3.0) * 1.10), rel_tol=1e-5)
    fw = IS800_2025.cl_8_7_4_web_bearing_capacity(b1=75.0, n2=50.0, tw=8.0, fyw=250.0)
    assert fw > 0


def test_combined_axial_and_biaxial_bending():
    ratio, is_safe = IS800_2025.cl_9_3_1_1_section_strength_interaction(
        N=200e3, Nd=1200e3, My=80e6, Mdy=200e6, Mz=20e6, Mdz=80e6, section_type="I_H"
    )
    assert is_safe is True
    assert ratio <= 1.0


def test_bolted_hsfg_and_welded_connections():
    assert IS800_2025.cl_10_2_1_bolt_hole_diameter(20.0) == 22.0
    assert IS800_2025.cl_10_3_3_1_long_joint_factor(lj=400.0, d=20.0) < 1.0

    vdsb = IS800_2025.cl_10_3_3_bolt_shear_capacity(fub=800.0, nn=1, ns=0, Anb=245.0, Asb=314.0)
    vdpb = IS800_2025.cl_10_3_4_bolt_bearing_capacity(d=20.0, t=10.0, fu=410.0, fub=800.0, e=35.0, p=60.0, d0=22.0)
    tdb = IS800_2025.cl_10_3_5_bolt_tension_capacity(fub=800.0, fyb=640.0, Anb=245.0, Asb=314.0)
    ratio, ok = IS800_2025.cl_10_3_6_bolt_combined_shear_tension(Vsb=30e3, Vdsb=vdsb, Tb=40e3, Tdb=tdb)
    assert vdsb > 0 and vdpb > 0 and tdb > 0 and ok is True

    vdsf_uls = IS800_2025.cl_10_4_3_hsfg_slip_resistance(mu_f=0.5, ne=1, Kh=1.0, fub=800.0, Anb=245.0, is_ultimate_limit_state=True)
    vdsf_sls = IS800_2025.cl_10_4_3_hsfg_slip_resistance(mu_f=0.5, ne=1, Kh=1.0, fub=800.0, Anb=245.0, is_ultimate_limit_state=False)
    assert vdsf_sls > vdsf_uls

    pdw_shop = IS800_2025.cl_10_5_7_fillet_weld_strength(s=6.0, lw=200.0, fu=410.0, is_field_weld=False)
    pdw_field = IS800_2025.cl_10_5_7_fillet_weld_strength(s=6.0, lw=200.0, fu=410.0, is_field_weld=True)
    assert math.isclose(pdw_shop / pdw_field, 1.50 / 1.25, rel_tol=1e-5)

    fe, weld_ok = IS800_2025.cl_10_5_10_1_weld_combined_stresses(fa=80.0, q=90.0, fu=410.0)
    assert weld_ok is True
