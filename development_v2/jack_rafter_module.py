# jack_rafter_module.py - Jack rafter calculations for valley snow drift loads

import math

def calculate_jack_rafters(
    de_north,
    de_west,
    pitch_north,
    pitch_west,
    valley_angle_deg=90,
    jack_spacing_in=24,
    ps_psf=30.0,
    pd_max_psf=50.0,
    w_drift_ft=20.0,
    dead_load_psf_horizontal=20.0
):
    """Calculate jack rafters starting from eave (longest) to ridge (shortest).
    Returns separate point loads for north and west sides at each location.
    """
    # Spacing is measured along ridges, convert to spacing along sloped valley
    valley_angle_rad = math.radians(valley_angle_deg)
    spacing_along_ridge_ft = jack_spacing_in / 12.0
    # Spacing along valley beam = spacing along ridge / cos(valley_angle/2)
    bisector_rad = valley_angle_rad / 2
    jack_spacing_ft = spacing_along_ridge_ft / math.cos(bisector_rad)

    lv = math.sqrt(de_north**2 + de_west**2 - 2 * de_north * de_west * math.cos(valley_angle_rad))

    # Number of spaces along valley
    num_spaces = math.floor(lv / jack_spacing_ft)
    if num_spaces < 1:
        num_spaces = 1  # at least one

    # Positions from ridge (0 to lv)
    positions_from_ridge = [i * jack_spacing_ft for i in range(1, num_spaces + 1)]
    if positions_from_ridge[-1] > lv:
        positions_from_ridge[-1] = lv  # adjust last

    trib_width_ft = jack_spacing_ft
    bisector_rad = valley_angle_rad / 2

    jacks_north = []
    jacks_west = []

    for pos_from_ridge in positions_from_ridge:
        # Jack rafters span from valley beam to ridge
        # Horizontal tributary length proportional to building dimension
        horiz_length_n = pos_from_ridge * (de_north / lv)
        horiz_length_w = pos_from_ridge * (de_west / lv)

        # Sloped length for structural calculations
        sloped_length_n = horiz_length_n / math.cos(math.atan(pitch_north / 12)) if pitch_north > 0 else horiz_length_n
        sloped_length_w = horiz_length_w / math.cos(math.atan(pitch_west / 12)) if pitch_west > 0 else horiz_length_w

        # Average pd over jack span (use north span for simplicity)
        start_d = pos_from_ridge
        end_d = pos_from_ridge + horiz_length_n
        if end_d <= w_drift_ft:
            # Fully within drift zone
            avg_pd = pd_max_psf * (1 - (start_d + end_d) / (2 * w_drift_ft))
        elif start_d >= w_drift_ft:
            # Fully outside drift zone
            avg_pd = 0
        else:
            # Partial overlap with drift zone
            overlap_length = w_drift_ft - start_d
            avg_pd = pd_max_psf * (overlap_length / (end_d - start_d)) * (1 - (start_d + min(end_d, w_drift_ft)) / (2 * w_drift_ft))

        # Load calculations using horizontal projection
        P_balanced_n = ps_psf * horiz_length_n * trib_width_ft
        P_balanced_w = ps_psf * horiz_length_w * trib_width_ft

        P_drift_n = avg_pd * horiz_length_n * trib_width_ft
        P_drift_w = avg_pd * horiz_length_w * trib_width_ft

        P_total_snow_n = P_balanced_n + P_drift_n
        P_total_snow_w = P_balanced_w + P_drift_w

        # Dead load using horizontal projection
        P_dead_n = dead_load_psf_horizontal * horiz_length_n * trib_width_ft
        P_dead_w = dead_load_psf_horizontal * horiz_length_w * trib_width_ft

        # Full load on jack rafter (total load carried by the rafter)
        full_load_on_jack_n = P_total_snow_n + P_dead_n
        full_load_on_jack_w = P_total_snow_w + P_dead_w

        # Point load to valley beam = reaction (half of full load, assuming simply supported at ridge)
        P_total_n = full_load_on_jack_n / 2
        P_total_w = full_load_on_jack_w / 2

        jacks_north.append({
            'sloped_length_ft': sloped_length_n,
            'horiz_length_ft': horiz_length_n,
            'trib_width_ft': trib_width_ft,
            'balanced_snow_lb': P_balanced_n,
            'drift_load_lb': P_drift_n,
            'total_snow_lb': P_total_snow_n,
            'dead_load_lb': P_dead_n,
            'full_load_on_jack_lb': full_load_on_jack_n,
            'point_load_lb': P_total_n,  # Reaction to valley beam
            'location_from_ridge_ft': pos_from_ridge
        })
        jacks_west.append({
            'sloped_length_ft': sloped_length_w,
            'horiz_length_ft': horiz_length_w,
            'trib_width_ft': trib_width_ft,
            'balanced_snow_lb': P_balanced_w,
            'drift_load_lb': P_drift_w,
            'total_snow_lb': P_total_snow_w,
            'dead_load_lb': P_dead_w,
            'full_load_on_jack_lb': full_load_on_jack_w,
            'point_load_lb': P_total_w,  # Reaction to valley beam
            'location_from_ridge_ft': pos_from_ridge
        })

    # Reverse for eave-first (longest to shortest)
    jacks_north.reverse()
    jacks_west.reverse()

    # Update locations to from eave (optional, or keep from ridge)
    for j in jacks_north + jacks_west:
        j['location_from_eave_ft'] = lv - j['location_from_ridge_ft']

    return {
        'num_per_side': len(jacks_north),
        'spacing_along_ridge_in': jack_spacing_in,
        'spacing_along_valley_ft': jack_spacing_ft,
        'jacks': {'north_side': jacks_north, 'west_side': jacks_west}
    }