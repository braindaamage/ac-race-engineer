# Dampers

## Physical Principles

Dampers (also called shock absorbers) are velocity-sensitive devices that resist suspension motion by converting kinetic energy into heat through hydraulic fluid passing through calibrated orifices. Unlike springs, which react to displacement, dampers react to the rate of change of displacement — their force output is a function of suspension velocity, not position.

**Bump vs Rebound**

Bump (compression) damping resists the suspension moving upward relative to the chassis — that is, the wheel being pushed toward the body by a road input. Rebound (extension) damping resists the suspension moving downward — the wheel dropping away from the body under spring force after compression. Both directions are present in every suspension cycle; their ratio fundamentally shapes how the car transfers load and recovers from disturbances.

**Slow-Speed vs Fast-Speed Damping**

Damper velocity refers to the speed at which the suspension shaft moves, not the road speed of the vehicle. Slow-speed damping (typically below 25–75 mm/s shaft velocity) governs body motions driven by aerodynamic loads, steady-state cornering, braking, and acceleration — events where suspension moves slowly. Fast-speed damping (above that threshold) governs the response to sharp road inputs such as kerbs, bumps, and surface irregularities, where the shaft moves rapidly.

These two operating regimes are physically independent in a two-way adjustable damper that uses separate shim stacks or bypass circuits. A damper that is correct in slow-speed but wrong in fast-speed will be comfortable on smooth circuits and brutal on bumpy ones — and vice versa.

**AC's Bilineal Damping Model**

Assetto Corsa models dampers using a bilineal (two-slope) force-velocity curve with the following parameters per corner: DAMP_BUMP (slow-speed compression damping), DAMP_FAST_BUMP (fast-speed compression damping), DAMP_FAST_BUMPTHRESHOLD (the knee-point velocity where the curve transitions from slow to fast slope), and the rebound equivalents DAMP_REBOUND, DAMP_FAST_REBOUND, and DAMP_FAST_REBOUNDTHRESHOLD. Below the threshold velocity, damper force increases at the slow-speed rate; above it, force increases at the lower fast-speed rate. This two-slope model approximates the digressive damper curves used in motorsport, where stiff low-speed damping provides body control while softer high-speed damping prevents harshness over bumps. All damper values in AC are expressed at the wheel (consistent with spring wheel rates), not at the damper shaft — the motion ratio conversion is already applied. Custom Shaders Patch (CSP) with "cosmic suspension" extends this model to support full lookup-table (LUT) damper curves for even more realistic response.

**Velocity Domain Framework**

Damper behavior can be understood through three velocity domains that correspond to different driving events. Low-speed damping (0–50 mm/s at the wheel) governs body motions: roll, pitch, and heave driven by aerodynamic loads, steady-state cornering, braking, and acceleration. This is the most critical domain for driver feel and balance — it is where the damper's influence on transient weight transfer is most apparent and where front-rear damper balance shapes the character of turn-in, mid-corner transitions, and corner exit. Mid-speed damping (50–200 mm/s) covers transitions: directional changes, kerb rides at moderate speed, and surface undulations. High-speed damping (200+ mm/s) addresses sharp impacts: aggressive kerb strikes, sudden surface changes, and large bumps. High-speed damping must be soft enough to allow the wheel to absorb these inputs without losing contact with the road surface — excessive high-speed damping transmits the impact energy into the chassis and can momentarily unload the tyre.

**Critical Damping and Damping Ratio**

The critical damping coefficient is the value at which the spring-mass system returns to equilibrium in the shortest time without oscillation. The damping ratio (zeta) is the ratio of actual damping to critical damping. Values below 1.0 produce underdamping (oscillation), values above 1.0 produce overdamping (sluggish return), and exactly 1.0 produces critical damping. Race cars typically run 0.25–0.60 in bump and 0.50–0.80 in rebound, prioritising quick transient response over complete oscillation elimination.

**Damping Ratio Targets**

For most race cars, the optimal damping ratio target is approximately zeta = 0.65–0.7. This value minimizes settling time after a disturbance (the suspension returns to equilibrium faster than at any other damping ratio) while allowing only minimal overshoot — typically one small oscillation before settling. At zeta = 1.0 (critical damping), there is zero overshoot but the return to equilibrium is actually slower than at 0.7. Street cars typically run zeta = 0.2–0.5, prioritizing ride comfort over transient response speed. The damping ratio can be calculated from the damper coefficient and the spring rate: zeta = c / (2 x sqrt(K_wheel x m_corner)), where c is the damping coefficient at the wheel, K_wheel is the wheel rate, and m_corner is the sprung corner mass. When springs are changed, the damping ratio changes automatically — stiffer springs with the same damper setting produce a lower damping ratio, potentially introducing unwanted oscillation.

**Rebound-to-Compression Ratio**

The ratio of rebound damping to compression damping is a fundamental damper setup parameter. Typical competition ratios range from 1.5:1 to 3:1 (rebound firmer than bump). The physical justification: rebound controls the rate at which load is released from a compressed wheel — how quickly the chassis rises after a compression event. Firmer rebound keeps the chassis low longer, maintaining aerodynamic consistency and preventing the chassis from "bouncing" off the springs. However, excessive rebound causes packing down — the suspension fails to fully extend between consecutive compression events, causing a progressive reduction in ride height over a bumpy section. Packing down degrades handling because the suspension starts each new compression event from a partially compressed position, reducing available travel and potentially engaging bump stops prematurely. The opposite pathology — jacking up — occurs when rebound is too soft relative to bump, allowing the chassis to rise progressively.

**Transient vs Steady-State Load Transfer**

During a transient manoeuvre (turn-in, initial braking, throttle application), the chassis is accelerating rotationally. Damping forces resist that rotation, slowing load transfer to a rate proportional to the damping magnitude. In steady-state cornering, the chassis is no longer rotating and damping contributes nothing; all load transfer is determined by spring rates, anti-roll bars, and geometry. Dampers therefore have no effect on the final, steady-state balance of a car — they control only how quickly that balance is reached and how the tyres are loaded during the transition.

**Tyre Contact Patch Loading**

A key function of dampers is keeping the tyre contact patch in consistent contact with the road. Underdamped suspension allows the wheel to oscillate after a disturbance, causing intermittent loss of contact pressure and therefore intermittent loss of grip. Overdamped suspension transmits more of the road input directly into the chassis, reducing the wheel's ability to follow the road surface. Optimal damping keeps the wheel moving smoothly and tracking the road without bouncing or being held rigid.

---

## Adjustable Parameters and Effects

**Bump Damping (Slow-Speed)**

Slow-speed bump controls how quickly the chassis dives under braking, squats under acceleration, and rolls into corners. Higher slow-speed bump on the front delays front dive under braking and slows the load transfer toward the front axle, making initial turn-in feel more progressive but potentially reducing peak braking grip if overdone. Higher slow-speed bump on the rear delays squat under acceleration and slows rear load transfer, which can tighten the car under power by keeping the rear planted longer. Excessive slow-speed bump makes the car feel stiff and unresponsive to driver inputs; insufficient bump makes the car feel wallowy and difficult to position consistently.

**Bump Damping (Fast-Speed)**

Fast-speed bump controls the wheel's ability to absorb sharp road inputs — kerbs, bumps, surface changes — without transmitting the impact into the chassis or losing contact with the road. Low fast-speed bump allows the wheel to rise quickly over a kerb, keeping the tyre loaded but potentially causing chassis movement. High fast-speed bump transmits the impact energy directly through to the chassis, degrading ride and potentially unsettling the car. Fast-speed bump should generally be kept low enough to absorb inputs but high enough to limit excessive wheel travel on heavy hits.

**Rebound Damping (Slow-Speed)**

Slow-speed rebound controls how quickly the suspension extends after being compressed — how fast the car returns from a roll, dive, or squat. High rebound damping slows the return, keeping the chassis low after a compression event. On a bumpy track this can cause the suspension to fail to fully extend between bumps, leading to a progressive reduction in ride height (pack-down), which degrades handling. Insufficient rebound allows the chassis to oscillate after disturbances. Rebound is typically set higher than bump to maintain body control during recovery, with ratios of 1.5:1 to 3:1 rebound-to-bump being common.

**Rebound Damping (Fast-Speed)**

Fast-speed rebound governs how quickly the wheel drops into a depression after being pushed upward by a bump. High fast-speed rebound keeps the wheel from dropping rapidly, which can cause the tyre to lose contact with the road on the far side of a bump. This is particularly important on circuits with compression bumps at high speed. Low fast-speed rebound allows the wheel to extend freely and follow the road surface.

**Front-Rear Damper Balance**

The ratio of front to rear damping directly influences transient handling balance. More front bump relative to rear slows front load transfer, making the car initially more understeer during turn-in as the front loads more slowly. More rear bump relative to front does the opposite. More front rebound relative to rear keeps the front chassis elevated longer after a corner, which can reduce front roll and shift balance toward oversteer on exit. Engineers adjust the front-rear damper balance to tune the character of transitions without changing the car's steady-state mechanical balance.

**Wheel Load Variation as Performance Metric**

The primary function of dampers in pure performance terms is minimizing the variation of vertical load at each tyre contact patch. Through tire load sensitivity (the concave Fy-Fz relationship), a tyre with steady load generates more average grip than one with fluctuating load of the same mean value. Dampers that allow excessive load oscillation sacrifice grip even if the driver cannot feel the difference. Wheel load coefficient of variation (standard deviation divided by mean, per wheel) is the quantitative metric: lower is better. On aero cars, dampers also serve a platform control function — maintaining consistent ride height across the speed range so that the aerodynamic balance remains stable. Stiffer low-speed damping in both bump and rebound resists ride height changes driven by aero load variation, at the cost of reduced compliance over surface irregularities.

**Damper Curve Shape**

Many modern dampers have a digressive curve — steep force rise at low velocities (for good slow-speed body control) that flattens progressively at higher velocities (for absorption of fast inputs without harshness). A linear curve produces proportional force at all velocities. A progressive curve increases stiffness with velocity. The shape affects whether the damper feels well-controlled at low shaft speeds while still compliant on kerbs, or whether it trades one operating regime for another. When available as an adjustment (via shim stack tuning in motorsport dampers), curve shape is as important as absolute magnitude settings.

---

## Telemetry Diagnosis

**Suspension Velocity Analysis**

Raw suspension position data from telemetry can be differentiated with respect to time to produce suspension velocity channels. Plotting these velocity signals reveals which operating regime — slow or fast — is dominant for a given circuit and driving style. A track with predominantly smooth tarmac and gentle undulations will show most suspension activity below 50 mm/s; a bumpy or kerb-heavy circuit will show significant energy above 100 mm/s. This information directly informs whether slow-speed or fast-speed damping adjustments will have the most impact.

**Damper Histograms**

A damper velocity histogram plots the frequency distribution of suspension shaft velocities, separated by bump and rebound directions. The histogram is the primary diagnostic tool for damper setup. A well-set damper shows a smooth distribution centred around low velocities with a gradual tail toward high velocities. Key patterns to identify: a peak at zero velocity indicates the damper may be too stiff (suspension is being locked at ride height); excessive population at high velocities suggests the damper is underworked in that range; asymmetry between bump and rebound reveals imbalance in the compression-extension cycle. Comparing histograms between front and rear helps diagnose whether handling issues arise from a specific axle's damper behaviour.

**Damper Velocity Domain Distribution**

Beyond the standard histogram, analyzing the time distribution across the three velocity domains (low: 0–50 mm/s, mid: 50–200 mm/s, high: 200+ mm/s) per corner reveals the damper's operational profile for a specific circuit. A smooth circuit with gentle undulations might show 70% of time in the low-speed domain, while a bumpy street circuit might show 40% in mid and high-speed domains. This distribution directly informs which damper adjustments will have the most impact: if the majority of time is spent in the low-speed domain, fast-speed adjustments will have minimal effect, and vice versa.

**Wheel Load Coefficient of Variation**

The coefficient of variation of wheel load (standard deviation / mean) per wheel is the most direct metric of damper effectiveness. Lower values indicate more consistent tyre loading and better average grip utilization. Comparing this metric between setup configurations quantifies whether a damper change improved tyre contact quality, even when lap time differences are within noise. Comparing front versus rear values reveals which axle has more load variation — typically the stiffer axle shows higher variation on bumpy surfaces, suggesting the dampers at that end may benefit from softer fast-speed settings.

**Wheel Load Fluctuation Frequency**

Tyre load (normal force) can be estimated from suspension travel combined with spring rate and damper force data. Fluctuations in wheel load at frequencies above approximately 4–8 Hz indicate the damper is failing to prevent wheel hop — the tyre is oscillating on its contact patch rather than maintaining steady pressure. Frequencies in the 1–4 Hz range correspond to chassis body motion. Isolating the frequency content of wheel load variation allows the engineer to determine whether the damper issue is in the slow-speed range (body motion frequencies) or fast-speed range (wheel hop frequencies).

**Post-Bump Oscillation Settling Time**

On circuits with identifiable discrete bumps or kerbs, the settling time of the suspension after an impact can be measured directly from telemetry. After the initial compression and rebound, a correctly damped suspension should settle to within 10% of ride height within 1–2 suspension cycles. More than 3–4 oscillations before settling indicates underdamping (low rebound in particular). Immediate cessation of motion after a bump with no return oscillation may indicate overdamping, but may also indicate the car simply has stiff springs with adequate damping.

**Ride Quality Assessment from Suspension Travel**

Suspension travel channels — the absolute position of each corner's suspension relative to full droop — reveal average ride height, dynamic range of motion used, and whether the car is consistently using its full travel or hitting bump stops. A corner that consistently shows very little travel variation on a rough track is either overdamped or running on a bump stop. Travel data across a full session can reveal progressive pack-down (damper fluid fade or excessive rebound stiffness causing the chassis to drop over a stint), progressive rise (unusual, may indicate a loose component), or asymmetries between left and right that point to damper seal failure or damper-specific mechanical issues. Coupling suspension travel with ride height derived from aero maps (where available) further contextualises whether suspension motion is within the intended operating range.

---

## Cross-References

- **suspension_and_springs.md** — Spring rates, ride height, and bump stop interaction with damper behaviour; the spring-damper system as a unit; natural frequency and its relationship to damping ratio.
- **vehicle_balance_fundamentals.md** — How transient load transfer (governed by dampers) versus steady-state load transfer (governed by springs and anti-roll bars) affects overall handling balance; the role of dampers in understeer/oversteer behaviour during turn-in and exit.
- **tyre_dynamics.md** — Contact patch loading and its sensitivity to wheel load fluctuations; tyre natural frequency and its interaction with suspension oscillation frequencies; how inconsistent wheel load from underdamping reduces time-average grip.
