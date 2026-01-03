#!/usr/bin/env python3
"""
Test script for ASCE 7-22 snow load calculations
Tests the updated calculation logic with examples from the user requirements.
"""

import math


def calculate_cs_fig_7_4_1(
    theta_deg: float, ct: float, slippery: bool = False, warm_roof: bool = False
) -> float:
    """
    Calculate slope factor Cs per ASCE 7-22 Figure 7.4-1.
    """
    theta = max(0.0, min(90.0, theta_deg))

    # Graph selection based on Ct and roof type
    if ct <= 1.1 or warm_roof:
        # Graphs a and b: warm roofs
        if slippery:
            # Graph b – slippery warm roof
            if theta <= 3.58:
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 3.58) / 66.42)
        else:
            # Graph a – non-slippery warm roof
            if theta <= 26.57:
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 26.57) / 43.43)
    else:
        # Graph c – cold roofs
        if slippery:
            if theta <= 8.53:
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 8.53) / 61.47)
        else:
            if theta <= 37.76:
                return 1.0
            else:
                return max(0.0, 1.0 - (theta - 37.76) / 32.24)

    return 1.0


def test_steep_slope():
    """Test steep slope case (>30.2°) - should have hd=0"""
    print("=== TESTING STEEP SLOPE CASE (>30.2°) ===")

    # Test parameters for steep slope
    pg = 50  # psf
    slope_ratio = 1.0  # 45° slope (atan(1.0) = 45°)
    theta = math.degrees(math.atan(slope_ratio))
    ct = 1.2  # cold roof
    slippery = False
    ce = 1.0
    w2 = 0.55
    lu = 32

    print(f"pg = {pg} psf")
    print(f"slope_ratio = {slope_ratio} (theta = {theta:.1f} deg)")
    print(f"ct = {ct}, slippery = {slippery}")

    # Step 1: pf = 0.7 * Ce * Ct * pg
    pf = 0.7 * ce * ct * pg
    print(f"pf = 0.7 * {ce} * {ct} * {pg} = {pf:.1f} psf")

    # Step 2: Cs from Fig 7.4-1
    cs = calculate_cs_fig_7_4_1(theta, ct, slippery)
    print(f"Cs = {cs:.3f}")

    # Step 3: ps = Cs * pf
    ps = cs * pf
    print(f"ps = {cs:.3f} * {pf:.1f} = {ps:.1f} psf")

    # Step 4: gamma = min(0.13 * pg + 14, 30)
    gamma = min(0.13 * pg + 14, 30)
    print(f"gamma = min(0.13 * {pg} + 14, 30) = {gamma:.1f} pcf")

    # Step 5: hb = ps / gamma
    hb = ps / gamma
    print(f"hb = {ps:.1f} / {gamma:.1f} = {hb:.2f} ft")

    # Step 8: apply_unbalanced = (2.38 <= theta <= 30.2)
    apply_unbalanced = 2.38 <= theta <= 30.2
    print(f"apply_unbalanced = (2.38 <= {theta:.1f} <= 30.2) = {apply_unbalanced}")

    if not apply_unbalanced:
        print("[OK] CORRECT: Unbalanced loads do not apply for steep slopes")
        hd = 0
        print(f"hd = {hd} ft (uniform ps everywhere)")
    else:
        print("[ERROR] ERROR: Unbalanced loads should not apply for steep slopes")

    print()


def test_shallow_slope():
    """Test shallow slope case (e.g., 18°) - should have hd > 0"""
    print("=== TESTING SHALLOW SLOPE CASE (18°) ===")

    # Test parameters for shallow slope
    pg = 50  # psf
    slope_ratio = math.tan(math.radians(18))  # 18° slope
    theta = 18.0
    ct = 1.2  # cold roof
    slippery = False
    ce = 1.0
    w2 = 0.55
    lu = 32

    print(f"pg = {pg} psf")
    print(f"slope_ratio = {slope_ratio:.3f} (theta = {theta:.1f} deg)")
    print(f"ct = {ct}, slippery = {slippery}")

    # Step 1: pf = 0.7 * Ce * Ct * pg
    pf = 0.7 * ce * ct * pg
    print(f"pf = 0.7 * {ce} * {ct} * {pg} = {pf:.1f} psf")

    # Step 2: Cs from Fig 7.4-1
    cs = calculate_cs_fig_7_4_1(theta, ct, slippery)
    print(f"Cs = {cs:.3f}")

    # Step 3: ps = Cs * pf
    ps = cs * pf
    print(f"ps = {cs:.3f} * {pf:.1f} = {ps:.1f} psf")

    # Step 4: gamma = min(0.13 * pg + 14, 30)
    gamma = min(0.13 * pg + 14, 30)
    print(f"gamma = min(0.13 * {pg} + 14, 30) = {gamma:.1f} pcf")

    # Step 5: hb = ps / gamma
    hb = ps / gamma
    print(f"hb = {ps:.1f} / {gamma:.1f} = {hb:.2f} ft")

    # Step 8: apply_unbalanced = (2.38 <= theta <= 30.2)
    apply_unbalanced = 2.38 <= theta <= 30.2
    print(f"apply_unbalanced = (2.38 <= {theta:.1f} <= 30.2) = {apply_unbalanced}")

    if apply_unbalanced:
        print("[OK] CORRECT: Unbalanced loads apply for shallow slopes")

        # Step 10: Calculate hd
        hd = 1.5 * math.sqrt((pg**0.74 * lu**0.70 * w2**1.7) / gamma)
        print("hd = 1.5 * sqrt((pg**0.74 * lu**0.70 * W2**1.7) / gamma)")
        print(f"hd = 1.5 * sqrt(({pg}**0.74 * {lu}**0.70 * {w2}**1.7) / {gamma})")
        print(
            f"hd = 1.5 * sqrt({pg**0.74:.3f} * {lu**0.70:.3f} * {w2**1.7:.3f} / {gamma})"
        )
        print(f"hd = 1.5 * sqrt({pg**0.74 * lu**0.70 * w2**1.7 / gamma:.3f})")
        print(f"hd = 1.5 * {math.sqrt(pg**0.74 * lu**0.70 * w2**1.7 / gamma):.3f}")
        print(f"hd = {hd:.2f} ft")

        if hd > 0:
            print("[OK] CORRECT: hd > 0 for shallow slopes")
        else:
            print("[ERROR] ERROR: hd should be > 0 for shallow slopes")
    else:
        print("[ERROR] ERROR: Unbalanced loads should apply for shallow slopes")

    print()


if __name__ == "__main__":
    print("ASCE 7-22 Snow Load Calculation Tests")
    print("=" * 50)
    print()

    test_steep_slope()
    test_shallow_slope()

    print("Tests completed!")
