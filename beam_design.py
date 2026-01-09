# beam_design.py - Complete ASCE 7-22 Valley Snow Load Calculator with Beam Design
# Tkinter GUI application with full snow load analysis and valley beam design

import math
import tkinter as tk
from tkinter import ttk, messagebox


class ValleyBeamInputs:
    def __init__(
        self,
        tributary_width=4.0,
        beam_width_b=5.125,
        beam_depth_d=11.875,
        Fb=2400.0,
        Fv=265.0,
        E=1800000.0,
        deflection_limit_n=240,
        rafter_sloped_length_ft=None,
        jack_spacing_inches=None,
        # New parameter names for compatibility
        tributary_perp_ft=None,
        beam_width_in=None,
        beam_depth_trial_in=None,
        fb_allowable_psi=None,
        fv_allowable_psi=None,
        modulus_e_psi=None,
        deflection_snow_limit=None,
        deflection_total_limit=None,
        ps_balanced_psf=None,
        governing_pd_max_psf=None,
        roof_dead_psf=None,
        governing_drift_width_ft=None,
        **kwargs,
    ):
        # Use new parameter names if provided, otherwise fall back to old ones
        self.tributary_width = float(tributary_perp_ft or tributary_width or 4.0)
        self.tributary_perp_ft = (
            self.tributary_width
        )  # Also set new name for consistency

        self.beam_width_b = float(beam_width_in or beam_width_b or 5.125)
        self.beam_width_in = self.beam_width_b  # Also set new name

        self.beam_depth_d = float(beam_depth_trial_in or beam_depth_d or 11.875)
        self.beam_depth_trial_in = self.beam_depth_d  # Also set new name

        self.Fb = float(fb_allowable_psi or Fb or 2400.0)
        self.fb_allowable_psi = self.Fb  # Also set new name

        self.Fv = float(fv_allowable_psi or Fv or 265.0)
        self.fv_allowable_psi = self.Fv  # Also set new name

        self.E = float(modulus_e_psi or E or 1800000.0)
        self.modulus_e_psi = self.E  # Also set new name

        self.deflection_limit_n = int(
            deflection_snow_limit or deflection_limit_n or 240
        )
        self.deflection_snow_limit = self.deflection_limit_n  # Also set new name
        self.deflection_total_limit = int(
            deflection_total_limit or 360
        )  # Default 360 for total deflection

        self.rafter_sloped_length_ft = rafter_sloped_length_ft
        self.jack_spacing_inches = jack_spacing_inches

        # Additional attributes from dataclass
        self.ps_balanced_psf = ps_balanced_psf
        self.governing_pd_max_psf = governing_pd_max_psf
        self.roof_dead_psf = roof_dead_psf or 15.0
        self.governing_drift_width_ft = governing_drift_width_ft or 20.0


class ValleyBeamDesigner:
    def __init__(self, inputs: ValleyBeamInputs):
        self.inputs = inputs
        self.results = None

    def _calculate_beam_self_weight_plf(self, beam_length_ft):
        """
        Calculate beam self-weight as distributed load in pounds per linear foot (plf).
        Uses wood density of 35 pcf (pounds per cubic foot) for softwood lumber.

        Args:
            beam_length_ft: Length of beam in feet (for reference, not used in calculation)

        Returns:
            Self-weight in plf (pounds per linear foot)
        """
        # Wood density: 35 pcf (typical for softwood lumber)
        wood_density_pcf = 35.0

        # Cross-sectional area in square feet
        # Convert inches to feet: (width_in * depth_in) / 144
        area_sqft = (
            self.inputs.beam_width_in * self.inputs.beam_depth_trial_in
        ) / 144.0

        # Weight per linear foot = density × area
        self_weight_plf = wood_density_pcf * area_sqft

        return self_weight_plf

    def design_with_point_loads(
        self, snow_point_loads, dead_point_loads, lv, valley_rafter_length
    ):
        """
        Design valley beam with separate snow and dead point loads from jack rafters.
        snow_point_loads: list of (position_from_eave_ft, snow_load_lb) tuples
        dead_point_loads: list of (position_from_eave_ft, dead_load_lb) tuples
        lv: valley beam horizontal length (used for moment, shear, deflection)
        valley_rafter_length: sloped length (used for self-weight calculation only)
        """
        try:
            # Convert point load positions from sloped to horizontal coordinates if needed
            # Check if positions exceed horizontal length (indicating they're sloped)
            max_pos = (
                max(
                    [pos for pos, _ in snow_point_loads]
                    + [pos for pos, _ in dead_point_loads]
                )
                if snow_point_loads and dead_point_loads
                else 0
            )
            if (
                max_pos > lv * 1.1 and valley_rafter_length > lv
            ):  # Positions appear to be sloped
                # Convert sloped positions to horizontal positions
                conversion_factor = (
                    lv / valley_rafter_length if valley_rafter_length > 0 else 1.0
                )
                snow_point_loads_horizontal = [
                    (pos * conversion_factor, load) for pos, load in snow_point_loads
                ]
                dead_point_loads_horizontal = [
                    (pos * conversion_factor, load) for pos, load in dead_point_loads
                ]
            else:
                # Positions are already in horizontal coordinates
                snow_point_loads_horizontal = snow_point_loads
                dead_point_loads_horizontal = dead_point_loads

            # Sort point loads by position (from eave to ridge)
            snow_point_loads_sorted = sorted(
                snow_point_loads_horizontal, key=lambda x: x[0]
            )
            dead_point_loads_sorted = sorted(
                dead_point_loads_horizontal, key=lambda x: x[0]
            )

            # Combine loads for structural analysis (ASD: D + 0.7S for stresses)
            point_loads_sorted = []
            for i, ((pos_s, load_s), (pos_d, load_d)) in enumerate(
                zip(snow_point_loads_sorted, dead_point_loads_sorted)
            ):
                combined_load = load_d + 0.7 * load_s  # ASD loads for stress analysis
                point_loads_sorted.append((pos_s, combined_load))

            # Calculate beam self-weight as distributed load (plf) using SLOPED length
            self_weight_plf_sloped = self._calculate_beam_self_weight_plf(
                valley_rafter_length
            )

            # Convert to equivalent distributed load per horizontal foot for moment/shear calculations
            # Since beam is longer along slope, weight per horizontal foot = weight_per_sloped_foot * (sloped_length / horizontal_length)
            if lv > 0 and valley_rafter_length > 0:
                self_weight_plf = self_weight_plf_sloped * (valley_rafter_length / lv)
            else:
                self_weight_plf = self_weight_plf_sloped

            # Calculate reactions for simply supported beam
            # Point loads
            total_point_load = sum(load for _, load in point_loads_sorted)

            # Reaction at eave (x=0): sum of moments about ridge (x=L)
            reaction_eave_point = 0
            for pos, load in point_loads_sorted:
                reaction_eave_point += load * (lv - pos) / lv

            reaction_ridge_point = total_point_load - reaction_eave_point

            # Add self-weight distributed load reactions (w*L/2 at each end)
            # Self-weight distributed load is now per horizontal foot, so use horizontal length
            self_weight_total = (
                self_weight_plf * lv
            )  # Total weight distributed along horizontal span
            reaction_eave_self_weight = self_weight_total / 2.0
            reaction_ridge_self_weight = self_weight_total / 2.0

            # Total reactions including self-weight
            reaction_eave = reaction_eave_point + reaction_eave_self_weight
            reaction_ridge = reaction_ridge_point + reaction_ridge_self_weight

            # Calculate moments at multiple points along the beam for exact maximum
            # Use 0.1 ft intervals for precise calculation
            num_points = max(
                50, int(lv / 0.1)
            )  # At least 50 points or 10 points per foot
            positions = [i * lv / (num_points - 1) for i in range(num_points)]
            moments = []

            for x in positions:
                # Moment from point loads: reaction_eave_point * x minus moments of loads to the left
                moment = reaction_eave_point * x
                for pos, load in point_loads_sorted:
                    if pos < x:
                        moment -= load * (x - pos)

                # Add moment from self-weight distributed load: w*x*(L-x)/2
                moment_self_weight = self_weight_plf * x * (lv - x) / 2.0
                moment += moment_self_weight

                moments.append(abs(moment))

            max_moment = max(moments) if moments else 0

            # Find location of max moment (approximate)
            max_moment_idx = moments.index(max_moment)
            max_moment_location = positions[max_moment_idx]

            # Calculate max shear at supports and load points
            shear_positions = [0] + [pos for pos, _ in point_loads_sorted] + [lv]
            shears = []

            for x in shear_positions:
                # Shear from point loads
                shear = reaction_eave_point
                for pos, load in point_loads_sorted:
                    if pos < x:
                        shear -= load

                # Add shear from self-weight distributed load: reaction - w*x
                shear_self_weight = reaction_eave_self_weight - self_weight_plf * x
                shear += shear_self_weight

                shears.append(abs(shear))

            max_shear = max(shears) if shears else 0

            # Total load including self-weight
            total_load_with_self_weight = total_point_load + self_weight_total

            forces = {
                "total_load_kips": total_load_with_self_weight / 1000,
                "reaction_eave_lb": reaction_eave,
                "reaction_ridge_lb": reaction_ridge,
                "max_moment_ft_kip": max_moment / 1000,  # Convert to ft-kip
                "max_shear_kip": max_shear / 1000,  # Convert to kip
                "moment_location_ft_from_eave": max_moment_location,
            }

            # Perform design checks
            # Pass horizontal length (lv) for deflection calculations, sloped length for self-weight reference
            self.results = self._perform_point_load_design_checks(
                forces,
                lv,  # Horizontal length for deflection calculations and limits
                valley_rafter_length,  # Sloped length for self-weight calculation
                point_loads_sorted,
                snow_point_loads_sorted,
                dead_point_loads_sorted,
            )
            return self.results

        except Exception as e:
            return {"error": f"Beam design error: {str(e)}"}

    def _calculate_reactions(self, point_loads, lv):
        """Calculate support reactions for simply supported beam"""
        total_load = sum(load for _, load in point_loads)
        # For simply supported beam, reactions are equal if supports at ends
        reaction = total_load / 2
        return [reaction, reaction]

    def _calculate_moments(self, point_loads, lv):
        """Calculate moments at key points for simply supported beam"""
        moments = []
        # Sample moments at load locations and midpoints
        positions = sorted(set([0] + [pos for pos, _ in point_loads] + [lv]))

        total_load = sum(load for _, load in point_loads)
        reaction_left = total_load / 2

        for x in positions:
            moment = reaction_left * x  # Moment from left reaction

            # Subtract moments from point loads to the left of x
            for pos, load in point_loads:
                if pos < x:
                    moment -= load * (x - pos)

            moments.append(moment)

        return moments

    def _calculate_shears(self, point_loads, lv):
        """Calculate shears at key points for simply supported beam"""
        shears = []
        positions = sorted(set([0] + [pos for pos, _ in point_loads] + [lv]))

        total_load = sum(load for _, load in point_loads)
        reaction_left = total_load / 2

        for x in positions:
            shear = reaction_left  # Start with left reaction

            # Subtract point loads to the left of x
            for pos, load in point_loads:
                if pos < x:
                    shear -= load

            shears.append(shear)

        return shears

    def _find_max_moment_location(self, point_loads, lv):
        """Find location of maximum moment"""
        # Simplified - return position of largest load
        if point_loads:
            return max(point_loads, key=lambda x: x[1])[0]
        return lv / 2

    def _perform_point_load_design_checks(
        self,
        forces,
        horizontal_length,
        sloped_length,
        point_loads,
        snow_point_loads,
        dead_point_loads,
    ):
        """Perform design checks for beam with point loads

        Args:
            horizontal_length: Horizontal span length (used for deflection calculations and limits)
            sloped_length: Actual sloped beam length (used for self-weight calculation only)
        """
        try:
            # Use horizontal length for deflection calculations and limits
            L_ft = horizontal_length or self.inputs.rafter_sloped_length_ft or 70.0
            if L_ft <= 0:
                L_ft = 70.0
            L_in = L_ft * 12

            # Use the calculated forces
            Mu_ftlb = forces["max_moment_ft_kip"] * 1000  # Convert back to ft-lb
            Vu_lb = forces["max_shear_kip"] * 1000  # Convert back to lb

            # Calculate deflections for serviceability checks (IBC Table 1604.3 footnote)
            moment_of_inertia = (
                self.inputs.beam_width_in * self.inputs.beam_depth_trial_in**3 / 12
            )

            # Calculate beam self-weight as distributed load (plf) using SLOPED length
            sloped_L_ft = sloped_length if sloped_length and sloped_length > 0 else L_ft
            self_weight_plf = self._calculate_beam_self_weight_plf(sloped_L_ft)
            # Convert self-weight to equivalent distributed load along horizontal span for deflection
            # Self-weight per horizontal foot = (self-weight per sloped foot) * (sloped_length / horizontal_length)
            if horizontal_length > 0 and sloped_length > 0:
                self_weight_plf_horizontal = self_weight_plf * (
                    sloped_length / horizontal_length
                )
            else:
                self_weight_plf_horizontal = self_weight_plf
            self_weight_pli = self_weight_plf_horizontal / 12.0  # Convert to lb/in

            # Snow deflection: 0.7 * snow loads only (no self-weight for snow-only check)
            snow_load_total = sum(load for _, load in snow_point_loads)
            snow_load_plf = snow_load_total / L_ft  # lb/ft
            w_snow_pli = (
                0.7 * snow_load_plf
            ) / 12  # lb/in (0.7 factor for serviceability)
            delta_snow_in = (
                5
                * w_snow_pli
                * L_in**4
                / (384 * self.inputs.modulus_e_psi * moment_of_inertia)
                if moment_of_inertia > 0 and self.inputs.modulus_e_psi > 0
                else 0
            )

            # Total deflection: dead loads + 0.7 * snow loads + self-weight
            dead_load_total = sum(load for _, load in dead_point_loads)
            total_service_load_plf = (
                dead_load_total + 0.7 * snow_load_total
            )  # lb/ft (point loads only)
            w_total_pli = total_service_load_plf / L_ft / 12  # lb/in (point loads only)
            # Add self-weight to total deflection
            w_total_with_self_weight_pli = w_total_pli + self_weight_pli
            delta_total_in = (
                5
                * w_total_with_self_weight_pli
                * L_in**4
                / (384 * self.inputs.modulus_e_psi * moment_of_inertia)
                if moment_of_inertia > 0 and self.inputs.modulus_e_psi > 0
                else 0
            )

            Fb_prime = self.inputs.fb_allowable_psi * 1.15
            Fv_prime = self.inputs.fv_allowable_psi * 1.15
            S = self.inputs.beam_width_in * self.inputs.beam_depth_trial_in**2 / 6
            A = self.inputs.beam_width_in * self.inputs.beam_depth_trial_in

            fb = (Mu_ftlb * 12 / S) if S > 0 else 0
            fv = 1.5 * Vu_lb / A if A > 0 else 0

            ratio_bending = fb / Fb_prime if Fb_prime > 0 else 0
            ratio_shear = fv / Fv_prime if Fv_prime > 0 else 0
            delta_limit_snow = L_in / self.inputs.deflection_snow_limit
            delta_limit_total = L_in / self.inputs.deflection_total_limit
            ratio_deflection_snow = (
                delta_snow_in / delta_limit_snow if delta_limit_snow > 0 else 0
            )
            ratio_deflection_total = (
                delta_total_in / delta_limit_total if delta_limit_total > 0 else 0
            )

            passes = all(
                r <= 1.0
                for r in [
                    ratio_bending,
                    ratio_shear,
                    ratio_deflection_snow,
                    ratio_deflection_total,
                ]
            )

            # Determine pass/fail for each check
            bending_status = "PASS" if ratio_bending <= 1.0 else "FAIL"
            shear_status = "PASS" if ratio_shear <= 1.0 else "FAIL"
            deflection_snow_status = "PASS" if ratio_deflection_snow <= 1.0 else "FAIL"
            deflection_total_status = (
                "PASS" if ratio_deflection_total <= 1.0 else "FAIL"
            )

            results = {
                "L_sloped_ft": L_ft,
                "total_point_loads": len(point_loads),
                "reactions_lb": f"{forces['reaction_eave_lb']:.0f} @ eave, {forces['reaction_ridge_lb']:.0f} @ ridge",
                "Mu_ftlb": Mu_ftlb,
                "Vu_lb": Vu_lb,
                "delta_snow_in": delta_snow_in,
                "delta_total_in": delta_total_in,
                "delta_limit_snow_in": delta_limit_snow,
                "delta_limit_total_in": delta_limit_total,
                "fb_actual_psi": fb,
                "fb_allowable_psi": Fb_prime,
                "fv_actual_psi": fv,
                "fv_allowable_psi": Fv_prime,
                "ratio_bending": ratio_bending,
                "ratio_shear": ratio_shear,
                "ratio_deflection_snow": ratio_deflection_snow,
                "ratio_deflection_total": ratio_deflection_total,
                "bending_status": bending_status,
                "shear_status": shear_status,
                "deflection_snow_status": deflection_snow_status,
                "deflection_total_status": deflection_total_status,
                "passes": passes,
                "section": f"{self.inputs.beam_width_in:.3f} x {self.inputs.beam_depth_trial_in:.3f} inches",
            }

        except Exception as e:
            results = {"error": f"Point load design check error: {str(e)}"}

        return results

    def design(
        self, ps, pd_max_n, w_n, pd_max_w, w_w, lv, valley_rafter_length, phi_rad
    ):
        try:
            trib = self.inputs.tributary_width
            w_uniform_plf = ps * trib if ps else 0

            # Debug: ensure inputs are valid
            if not valley_rafter_length or valley_rafter_length <= 0:
                raise ValueError(
                    f"Invalid valley_rafter_length: {valley_rafter_length}"
                )
            if trib <= 0:
                raise ValueError(f"Invalid tributary width: {trib}")

            # Envelope surcharge
            steps = 100
            x_vals = [i * lv / steps for i in range(steps + 1)] if lv > 0 else [0]
            surcharge_psf = []
            bisector = phi_rad / 2 if phi_rad else math.radians(90) / 2
            for x in x_vals:
                d_n = x * math.sin(bisector)
                d_w = x * math.cos(bisector)
                s_n = pd_max_n * (1 - d_n / w_n) if d_n <= w_n and w_n > 0 else 0
                s_w = pd_max_w * (1 - d_w / w_w) if d_w <= w_w and w_w > 0 else 0
                surcharge_psf.append(max(s_n, s_w))

            w_variable_plf = [s * trib for s in surcharge_psf]
            max_var_plf = max(w_variable_plf) if w_variable_plf else 0
            w_max_total_plf = w_uniform_plf + max_var_plf

            L_ft = valley_rafter_length or self.inputs.rafter_sloped_length_ft or 70.0
            if L_ft <= 0:
                L_ft = 70.0
            L_in = L_ft * 12

            Mu_ftlb = (w_uniform_plf * L_ft**2 / 8) + (max_var_plf * L_ft**2 / 12)
            Vu_lb = (w_uniform_plf + max_var_plf / 2) * L_ft

            w_eq_plf = w_uniform_plf + 0.5 * max_var_plf
            w_eq_pli = w_eq_plf / 12
            moment_of_inertia = (
                self.inputs.beam_width_in * self.inputs.beam_depth_trial_in**3 / 12
            )
            delta_in = (
                5
                * w_eq_pli
                * L_in**4
                / (384 * self.inputs.modulus_e_psi * moment_of_inertia)
                if moment_of_inertia > 0 and self.inputs.modulus_e_psi > 0
                else 0
            )

            Fb_prime = self.inputs.fb_allowable_psi * 1.15
            Fv_prime = self.inputs.fv_allowable_psi * 1.15
            S = self.inputs.beam_width_in * self.inputs.beam_depth_trial_in**2 / 6
            A = self.inputs.beam_width_in * self.inputs.beam_depth_trial_in

            fb = (Mu_ftlb * 12 / S) if S > 0 else 0
            fv = 1.5 * Vu_lb / A if A > 0 else 0

            ratio_bending = fb / Fb_prime if Fb_prime > 0 else 0
            ratio_shear = fv / Fv_prime if Fv_prime > 0 else 0
            delta_limit = L_in / self.inputs.deflection_snow_limit
            ratio_deflection = delta_in / delta_limit if delta_limit > 0 else 0

            passes = all(
                r <= 1.0 for r in [ratio_bending, ratio_shear, ratio_deflection]
            )

            self.results = {
                "L_sloped_ft": L_ft,
                "w_uniform_plf": w_uniform_plf,
                "w_max_total_plf": w_max_total_plf,
                "Mu_ftlb": Mu_ftlb,
                "Vu_lb": Vu_lb,
                "delta_in": delta_in,
                "delta_limit_in": delta_limit,
                "ratio_bending": ratio_bending,
                "ratio_shear": ratio_shear,
                "ratio_deflection": ratio_deflection,
                "passes": passes,
                "section": f"{self.inputs.beam_width_in:.3f} x {self.inputs.beam_depth_trial_in:.3f} inches",
            }
        except Exception as e:
            self.results = {"error": f"Beam calculation error: {str(e)}"}
        return self.results

    def design_summary(self):
        if not self.results:
            return "Beam design not calculated (no data)."

        if "error" in self.results:
            return f"ERROR in beam design: {self.results['error']}"

        r = self.results
        status = (
            "PASSES" if r["passes"] else "FAILS - Increase section or material grade"
        )
        summary = f"""
=== VALLEY BEAM DESIGN RESULTS ===
Section: {r['section']}
Sloped Length: {r['L_sloped_ft']:.2f} ft
Uniform Load (balanced ps): {r['w_uniform_plf']:.1f} plf
Max Total Load (with drift envelope): {r['w_max_total_plf']:.1f} plf

Maximum Moment: {r['Mu_ftlb']:.0f} ft-lb
Maximum Shear: {r['Vu_lb']:.0f} lb
Maximum Deflection: {r['delta_in']:.3f} in (limit: {r['delta_limit_in']:.2f} in)

Bending Stress Ratio: {r['ratio_bending']:.3f}
Shear Stress Ratio: {r['ratio_shear']:.3f}
Deflection Ratio: {r['ratio_deflection']:.3f}

Overall Status: {status}

Note: Simply supported assumption. Snow load duration factor CD=1.15 applied.
Verify connections, lateral bracing, and actual supports with licensed engineer.
        """
        return summary.strip()


def create_beam_summary(results, beam_inputs):
    """Create beam design summary from results dict"""
    if "error" in results:
        return f"ERROR in beam design: {results['error']}"

    r = results
    status = "PASSES" if r["passes"] else "FAILS - Increase section or material grade"
    summary = f"""
{'='*60}
VALLEY RAFTER BEAM DESIGN ANALYSIS
{'-'*60}
Section: {r['section']}
Sloped Length: {r['L_sloped_ft']:.2f} ft
Point Loads: {r.get('total_point_loads', 'N/A')} locations
Reactions: {r.get('reactions_lb', 'N/A')}

Maximum Moment: {r['Mu_ftlb']:.0f} ft-lb
Maximum Shear: {r['Vu_lb']:.0f} lb

Snow Deflection (0.7S): {r['delta_snow_in']:.3f} in (limit: {r['delta_limit_snow_in']:.2f} in) ({r['ratio_deflection_snow']:.3f}) ({r['deflection_snow_status']})
Total Load Deflection (D + 0.7S): {r['delta_total_in']:.3f} in (limit: {r['delta_limit_total_in']:.2f} in) ({r['ratio_deflection_total']:.3f}) ({r['deflection_total_status']})

Bending Stress: {r['fb_actual_psi']:.0f} / {r['fb_allowable_psi']:.0f} psi ({r['ratio_bending']:.3f}) ({r['bending_status']})
Shear Stress: {r['fv_actual_psi']:.0f} / {r['fv_allowable_psi']:.0f} psi ({r['ratio_shear']:.3f}) ({r['shear_status']})

Overall Status: {status}

Note: Exact point load analysis from jack rafters. Simply supported assumption.
CD=1.15 applied for snow duration (NDS) - factored into allowable stresses.
Total deflection limit L/240 (default); Snow deflection limit L/360 (default) per typical roof serviceability practice.
Deflection per IBC Table 1604.3 footnote: snow reduced 0.7 for serviceability.
Point loads include combined snow + dead load reactions from jack rafters.
Verify connections, lateral bracing, and actual supports with licensed engineer.
    """
    return summary.strip()


class ValleySnowCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCE 7-22 Valley Snow Load Calculator with Beam Design")
        self.root.geometry("1200x900")

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="ASCE 7-22 Valley Snow Load Calculator",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Create input frame
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding="10")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # Create results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Results text area
        self.results_text = tk.Text(results_frame, height=40, width=80, wrap=tk.WORD)
        results_scrollbar = ttk.Scrollbar(
            results_frame, orient=tk.VERTICAL, command=self.results_text.yview
        )
        self.results_text.configure(yscrollcommand=results_scrollbar.set)

        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        # Input variables - Snow loads
        self.pg = tk.DoubleVar(value=50.0)
        self.lu_north = tk.DoubleVar(value=16.0)
        self.lu_west = tk.DoubleVar(value=42.5)
        self.w2 = tk.DoubleVar(value=0.5)
        self.ce = tk.DoubleVar(value=1.0)
        self.ct = tk.DoubleVar(value=1.2)
        self.is_factor = tk.DoubleVar(value=1.0)
        self.pitch_north = tk.DoubleVar(value=10.0)
        self.pitch_west = tk.DoubleVar(value=10.0)
        self.de_north = tk.DoubleVar(value=20.0)
        self.de_west = tk.DoubleVar(value=20.0)
        self.valley_angle = tk.DoubleVar(value=90.0)
        self.slippery = tk.BooleanVar(value=False)

        # Input variables - Beam design
        self.tributary_width = tk.DoubleVar(value=8.0)
        self.beam_width = tk.DoubleVar(value=5.125)
        self.beam_depth = tk.DoubleVar(value=11.875)
        self.fb_allowable = tk.DoubleVar(value=2400.0)
        self.fv_allowable = tk.DoubleVar(value=265.0)
        self.modulus_e = tk.DoubleVar(value=1800000.0)
        self.deflection_limit = tk.DoubleVar(value=240.0)

        # Create input widgets
        self.create_input_widgets(input_frame)

        # Calculate button
        calc_button = ttk.Button(
            main_frame,
            text="CALCULATE SNOW LOADS & BEAM DESIGN",
            command=self.calculate,
        )
        calc_button.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=(5, 0))

    def create_input_widgets(self, parent):
        """Create all input widgets organized by section"""
        row = 0

        # Snow Load Inputs
        ttk.Label(
            parent, text="GROUND SNOW LOAD (psf)", font=("Arial", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1

        ttk.Label(parent, text="pg (Ground snow load):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.pg, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="lu_north (North upwind fetch, ft):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.lu_north, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="lu_west (West upwind fetch, ft):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.lu_west, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="W2 (Winter wind parameter):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.w2, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Ce (Exposure factor):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.ce, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Ct (Thermal factor):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.ct, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Is (Importance factor):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.is_factor, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        # Geometry
        ttk.Label(parent, text="ROOF GEOMETRY", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        row += 1

        ttk.Label(parent, text="Pitch North (X/12):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.pitch_north, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Pitch West (X/12):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.pitch_west, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="de_north (North eave distance, ft):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.de_north, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="de_west (West eave distance, ft):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.de_west, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Valley angle (degrees):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.valley_angle, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Checkbutton(parent, text="Slippery surface", variable=self.slippery).grid(
            row=row, column=0, columnspan=2, sticky=tk.W
        )
        row += 1

        # Beam Design
        ttk.Label(parent, text="BEAM DESIGN", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
        )
        row += 1

        ttk.Label(parent, text="Tributary width (ft):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.tributary_width, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Beam width (in):").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(parent, textvariable=self.beam_width, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Beam depth (in):").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(parent, textvariable=self.beam_depth, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Fb allowable (psi):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.fb_allowable, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Fv allowable (psi):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.fv_allowable, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="E (psi):").grid(row=row, column=0, sticky=tk.W)
        ttk.Entry(parent, textvariable=self.modulus_e, width=15).grid(
            row=row, column=1, sticky=tk.W
        )
        row += 1

        ttk.Label(parent, text="Deflection limit (L/n):").grid(
            row=row, column=0, sticky=tk.W
        )
        ttk.Entry(parent, textvariable=self.deflection_limit, width=15).grid(
            row=row, column=1, sticky=tk.W
        )

    def calculate_slope_factor(self, theta_deg, ct, slippery=False):
        """Calculate slope factor Cs per ASCE 7-22 Figure 7.4-1"""
        theta = max(0.0, min(90.0, theta_deg))

        if ct <= 1.1:
            # Warm roofs
            if slippery:
                if theta <= 3.58:
                    return 1.0
                else:
                    return max(0.0, 1.0 - (theta - 3.58) / 66.42)
            else:
                if theta <= 26.57:
                    return 1.0
                else:
                    return max(0.0, 1.0 - (theta - 26.57) / 43.43)
        else:
            # Cold roofs
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

    def calculate_drift(self, pg, lu, w2, pitch):
        """Calculate drift height and surcharge"""
        # Simplified drift calculation
        gamma = min(0.13 * pg + 14, 30)  # Snow density

        # Drift height (simplified)
        hd = min(1.5 * (pg**0.74 * lu**0.7 * w2**1.7 / gamma) ** 0.5, lu * pitch / 12)

        # Drift surcharge
        s = pitch / 12.0
        if hd > 0 and s > 0:
            pd_max = 2 * hd * gamma / math.sqrt(s)
        else:
            pd_max = 0.0

        return hd, pd_max

    def calculate(self):
        """Main calculation function"""
        try:
            self.status_label.config(text="Calculating...")
            self.root.update()

            # Get input values
            pg = self.pg.get()
            lu_north = self.lu_north.get()
            lu_west = self.lu_west.get()
            w2 = self.w2.get()
            ce = self.ce.get()
            ct = self.ct.get()
            is_factor = self.is_factor.get()
            pitch_n = self.pitch_north.get()
            pitch_w = self.pitch_west.get()
            de_n = self.de_north.get()
            de_w = self.de_west.get()
            valley_angle = self.valley_angle.get()
            slippery = self.slippery.get()

            # Beam inputs
            tributary_width = self.tributary_width.get()
            beam_width = self.beam_width.get()
            beam_depth = self.beam_depth.get()
            fb_allowable = self.fb_allowable.get()
            fv_allowable = self.fv_allowable.get()
            modulus_e = self.modulus_e.get()
            deflection_limit = self.deflection_limit.get()

            # Clear results
            self.results_text.delete(1.0, tk.END)

            # Calculate flat roof snow load
            pf = 0.7 * ce * ct * is_factor * pg

            # Calculate slope factors
            theta_n = math.degrees(math.atan(pitch_n / 12))
            theta_w = math.degrees(math.atan(pitch_w / 12))
            cs_n = self.calculate_slope_factor(theta_n, ct, slippery)
            cs_w = self.calculate_slope_factor(theta_w, ct, slippery)
            cs_governing = min(cs_n, cs_w)

            # Calculate balanced loads
            ps_n = pf * cs_n
            ps_w = pf * cs_w
            ps_governing = pf * cs_governing

            # Calculate drifts
            hd_n, pd_max_n = self.calculate_drift(pg, lu_north, w2, pitch_n)
            hd_w, pd_max_w = self.calculate_drift(pg, lu_west, w2, pitch_w)

            # Valley governing drift
            pd_max_governing = max(pd_max_n, pd_max_w)
            hd_governing = max(hd_n, hd_w)

            # Valley geometry
            lv = math.sqrt(
                de_n**2
                + de_w**2
                - 2 * de_n * de_w * math.cos(math.radians(valley_angle))
            )
            phi_rad = math.radians(valley_angle)
            valley_rafter_length = math.sqrt(
                lv**2 + ((de_n * pitch_n + de_w * pitch_w) / 24) ** 2
            )

            # Total load at valley corner
            total_load_corner = ps_governing + pd_max_governing

            # Beam design calculations
            beam_inputs = ValleyBeamInputs(
                rafter_sloped_length_ft=valley_rafter_length,
                ps_balanced_psf=ps_governing,
                governing_pd_max_psf=pd_max_governing,
                tributary_perp_ft=tributary_width,
                beam_width_in=beam_width,
                beam_depth_trial_in=beam_depth,
                fb_allowable_psi=fb_allowable,
                fv_allowable_psi=fv_allowable,
                modulus_e_psi=modulus_e,
                deflection_snow_limit=int(deflection_limit),
            )

            beam_designer = ValleyBeamDesigner(beam_inputs)

            # Calculate beam design with all required parameters
            ps = ps_governing  # Use governing balanced load
            pd_max_n_val = pd_max_n  # North drift surcharge
            w_n = lu_north if hd_n > 0 else 0  # North drift width approximation
            pd_max_w_val = pd_max_w  # West drift surcharge
            w_w = lu_west if hd_w > 0 else 0  # West drift width approximation

            beam_results = beam_designer.design(
                ps,
                pd_max_n_val,
                w_n,
                pd_max_w_val,
                w_w,
                lv,
                valley_rafter_length,
                phi_rad,
            )

            # Output results
            result = f"""
ASCE 7-22 VALLEY SNOW LOAD CALCULATION RESULTS
{'='*60}

GROUND SNOW LOAD
Ground snow load (pg): {pg:.1f} psf

THERMAL FACTOR Ct
Ct: {ct:.2f}

EXPOSURE & IMPORTANCE
Ce: {ce:.2f}
Is: {is_factor:.2f}

FLAT ROOF SNOW LOAD
pf = 0.7 × Ce × Ct × Is × pg = {pf:.1f} psf

SLOPE FACTORS (Figure 7.4-1)
North roof: θ = {theta_n:.1f}°, Cs = {cs_n:.3f}
West roof: θ = {theta_w:.1f}°, Cs = {cs_w:.3f}
Governing Cs: {cs_governing:.3f}

BALANCED SNOW LOADS
North balanced (ps_n): {ps_n:.1f} psf
West balanced (ps_w): {ps_w:.1f} psf
Governing balanced (ps): {ps_governing:.1f} psf

DRIFT LOADS
North drift: hd = {hd_n:.1f} ft, pd_max = {pd_max_n:.1f} psf, w ≈ {w_n:.1f} ft
West drift: hd = {hd_w:.1f} ft, pd_max = {pd_max_w:.1f} psf, w ≈ {w_w:.1f} ft
Governing drift: hd = {hd_governing:.1f} ft, pd_max = {pd_max_governing:.1f} psf

VALLEY GEOMETRY
Horizontal valley length (lv): {lv:.2f} ft
Sloped rafter length: {valley_rafter_length:.2f} ft
Valley angle: {valley_angle:.0f}° (φ = {phi_rad:.3f} rad)

MAXIMUM TOTAL SNOW LOAD AT VALLEY CORNER
ps + pd_max = {total_load_corner:.1f} psf

{'='*60}
VALLEY RAFTER BEAM DESIGN ANALYSIS
{'-'*60}
"""

            # Add beam design results
            if beam_results and "error" not in beam_results:
                beam_summary = create_beam_summary(beam_results, beam_inputs)
                result += "\n" + beam_summary
            elif beam_results and "error" in beam_results:
                result += f"\nBEAM DESIGN ERROR: {beam_results['error']}"
            else:
                result += f"\nBEAM DESIGN: No results returned (beam_results = {beam_results})"

            result += """

LIFE-SAFETY CRITICAL: Service-level loads only. Verify with ASCE 7-22 & local codes.
Consult licensed structural engineer for final design.
"""

            self.results_text.insert(tk.END, result)
            self.status_label.config(text="Calculation complete", foreground="green")

        except Exception as e:
            messagebox.showerror(
                "Calculation Error", f"An error occurred during calculation:\n{str(e)}"
            )
            self.status_label.config(text="Error in calculation", foreground="red")


def main():
    root = tk.Tk()
    ValleySnowCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
