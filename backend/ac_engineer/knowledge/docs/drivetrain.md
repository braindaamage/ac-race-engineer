# Drivetrain

## Physical Principles

The drivetrain governs how engine torque is distributed to the driven wheels and how those wheels interact with one another during acceleration, braking, and cornering. Understanding its components is fundamental to diagnosing handling problems and optimizing lap time.

**Open Differential**
An open differential splits torque equally between the two driven wheels but allows them to rotate at different speeds. During cornering the outer wheel travels a longer arc than the inner wheel, requiring the differential to accommodate a speed difference. The problem with an open differential under power is that it always routes torque to the wheel with the least traction. If the inside rear unloads during corner exit, the open diff will spin it freely, delivering almost no torque to the outside rear where grip is available. This results in power-on understeer or a complete loss of forward drive.

**Limited-Slip Differential (LSD) — Lock Types**
AC models a clutch-pack LSD with POWER and COAST parameters ranging from 0.0 (fully open) to 1.0 (fully locked/spool). This is a simplified model of a clutch-pack limited-slip differential. Real-world ramp angles and Torsen mechanisms are not directly represented in AC's parametrization. The behavior differs by how POWER and COAST lock percentages are configured:

- **1-way LSD**: COAST near 0.0, POWER > 0. Under coast or braking, behaves like an open differential. The free coast behavior allows the car to rotate without drivetrain interference on turn-in, making this configuration suited to circuits where corner entry rotation is prioritized.
- **1.5-way LSD**: COAST < POWER (typically COAST is 0.4–0.6 times POWER). Offers a compromise between corner entry rotation (less coast lock than a 2-way) and some stability on trailing throttle, providing partial locking during engine braking without fully resisting yaw.
- **2-way LSD**: COAST = POWER. Equal lock percentage in both directions — this does NOT mean fully locked, just equal in both directions. Provides maximum consistency between phases but resists yaw rotation equally under power and coast. Can produce understeer on corner entry when the differential resists the inside wheel slowing relative to the outside.

**Preload**
Preload is a static, always-on locking torque applied by the differential spring pack regardless of throttle or brake input. Even when coasting with zero engine torque, the differential imposes a base resistance to wheel speed differences. Higher preload makes the car feel planted and straight-line stable but increases understeer tendency at low speed, particularly during initial turn-in where yaw rate must build rapidly.

**Power and Coast Lock Behavior**
POWER lock percentage controls how aggressively the differential locks during acceleration. A higher value produces a stronger lockup, forcing both driven wheels toward the same speed and increasing understeer tendency on corner exit. A lower value allows more wheel speed differentiation, preserving rotation deeper into the exit phase. COAST lock percentage controls locking during engine braking: a higher value increases stability under trailing throttle and deceleration but reduces the car's ability to rotate on corner entry. Preload (Nm) is a constant base locking torque independent of throttle or brake input — it provides a minimum resistance to wheel speed differences at all times. POWER and COAST lock are proportional to drivetrain torque, while preload is a fixed base value that acts even when engine torque is negligible.

**Torsen and Helical Differentials**
AC does not model Torsen or helical gear differentials explicitly. The clutch-pack LSD model used in AC generates locking torque based on input torque magnitude (via the POWER and COAST parameters), but it lacks the speed-differential sensitivity that characterizes helical gear differentials in reality. A Torsen diff in the real world generates locking torque proportional to the speed difference between the driven wheels, not the input torque — a fundamentally different behavior. Some cars in AC that use Torsen differentials in reality (such as the Mazda MX-5) are approximated using the clutch-pack model, which captures the general locking tendency but not the detailed response characteristics.

**Gear Ratios and the Power Band**
Each gear ratio defines the multiplication factor between engine RPM and wheel speed. Individual gear ratios set the spacing between gears; the final drive ratio scales the entire gearbox output and shifts the RPM window for every gear simultaneously. The goal of ratio selection is to keep the engine operating inside its peak power band for as much of the lap as possible, while matching gear change points to braking and acceleration zones. A taller ratio (numerically lower) allows higher top speed but delivers less mechanical advantage and slower acceleration. A shorter ratio (numerically higher) sacrifices top speed for stronger acceleration and keeps the engine in its rev range more effectively through slower corners.

**Final Drive Ratio Trade-offs**
Changing the final drive ratio affects every gear simultaneously. Shortening the final drive (raising the numerical value) multiplies acceleration potential across the entire gearbox but reduces maximum speed in the highest gear. Lengthening the final drive sacrifices low-gear responsiveness in favor of top speed. This is typically the first ratio adjustment made when adapting to a circuit, with individual gear ratios refined afterward to optimize corner-specific performance.

**Gear Ratio Optimization Guidance**
When optimizing gear ratios, the primary goal is to minimize the RPM drop between gears while keeping the engine in its peak power band for as much of the lap as possible. The final drive ratio should be the first adjustment when moving to a new circuit, as it scales all gears simultaneously — set it so that the highest gear reaches maximum speed at the end of the longest straight just before the braking zone. Individual gear ratios are then refined to match specific corner exit speeds. A useful heuristic: if the RPM drops more than 1500–2000 RPM on an upshift, the gears are spaced too far apart for that part of the rev range. Conversely, if the engine sits at the limiter for an extended period before the next braking zone, the gear or final drive is too short.

---

## Adjustable Parameters and Effects

**Differential Lock Percentage (Power)**
Controls the fraction of available locking torque applied during acceleration. At 0% the differential is fully open under power; at 100% it is fully locked. Increasing power lock improves traction on corner exit by reducing inside wheel spin and forcing both wheels to contribute to forward drive. The trade-off is an increased tendency toward understeer on exit: the locked rear axle resists the yaw needed to complete the corner. Lower power lock settings allow more rotation and exit oversteer but sacrifice traction where grip is marginal.

**Differential Lock Percentage (Coast)**
Controls locking during engine braking and trailing throttle. Increasing coast lock stabilizes the rear under braking and on corner entry by preventing the inside rear from decelerating faster than the outside. However, higher coast lock reduces the car's ability to rotate under braking, producing understeer or a wide entry line. Cars that require aggressive rotation on entry (e.g., high-downforce cars relying on rotation for apexing) generally run lower coast lock. Cars driven with a more passive entry style benefit from the stability higher coast lock provides.

**Preload Torque**
Sets the baseline locking force present at all times. Expressed in Newton-meters or as a numerical index depending on the simulation. Higher preload values make the differential resist wheel speed differences even when the engine delivers minimal torque, which helps the car track straight during coasting and light throttle phases. Excessive preload causes the car to push (understeer) on slow turn-in, particularly in hairpins and chicanes where speed is low and yaw demand is high.

**Individual Gear Ratios**
Each gear's ratio can be adjusted to optimize the RPM range available when exiting specific corners. Tightening a lower gear ratio places the RPM peak closer to the redline at the corner exit, improving acceleration out of that corner type. Spacing gears evenly avoids large RPM drops on upshifts but may not match the circuit's speed range. On circuits with a single dominant long straight, final drive calibration and the highest gear ratio are set together to reach maximum speed just before braking.

**Final Drive Ratio**
Scales all gears proportionally. Shortening the final drive (increasing the numerical ratio) raises torque at the wheel for a given engine torque, improving acceleration but lowering maximum speed. Lengthening the final drive favors top speed. This parameter is circuit-specific and is adjusted before individual gear ratios when moving between circuits of different character (high-speed vs. technical).

**Differential Type Selection**
Some titles and car configurations allow selecting between clutch-pack LSD, torque-sensing (Torsen-type), or locking differentials. Clutch-pack LSDs allow independent adjustment of power and coast lock; Torsen-type units generate lock proportional to torque difference automatically without ramp tuning. The selection affects which parameters are available for tuning and how the differential responds to transient load changes.

---

## Telemetry Diagnosis

**Inside vs. Outside Driven Wheel Speed Differential**
When logging individual wheel speeds on a driven axle, the speed difference between inside and outside wheels during cornering reveals differential behavior. In a correctly functioning LSD under power, the speed differential should be limited and both wheels should remain close to the reference speed of the chassis. An excessively large speed differential on corner exit (inside wheel spinning significantly faster than outside) indicates insufficient power lock or low preload — the inside wheel is unloaded and free to spin. Conversely, if both rear wheels show identical speed throughout the corner regardless of phase, the differential may be excessively locked, and the car will be pushing on exit.

**Throttle-On Wheel Spin Detection**
Overlaying throttle position against driven wheel slip ratio identifies power-on oversteer or wheelspin. If the inside driven wheel shows a sharp spike in slip ratio coinciding with throttle application in a corner, this confirms the differential is not locking sufficiently to transfer torque to the outside wheel. The correction is to increase power lock percentage or preload. If both driven wheels show elevated slip simultaneously on a straight, the issue is engine torque exceeding overall rear grip and requires either torque reduction or aerodynamic/suspension changes.

**Wheel Speed Ratio as Differential Diagnostic**
Beyond the absolute speed difference between driven wheels, the ratio of inside to outside wheel speed during cornering provides a more normalized diagnostic of differential locking state. The geometric speed ratio (determined by corner radius and track width) serves as the baseline — deviations from this theoretical ratio indicate differential intervention. A ratio closer to 1.0 than the geometric prediction means the differential is locking and preventing the natural speed difference. Monitoring how this ratio changes with throttle application rate reveals the differential's dynamic response: a sudden jump toward 1.0 coinciding with throttle application confirms power-lock engagement. Correlating the rate of throttle application with the onset of wheelspin helps characterize differential sensitivity — aggressive throttle inputs that cause immediate spin indicate either insufficient power lock or excessive torque relative to grip.

**Coast-Phase Instability Identification**
During corner entry under trailing throttle or engine braking, instability (rear steps out or car oversteers) can originate from the differential. If telemetry shows the inside rear wheel decelerating faster than the outside rear (large speed differential under coast), the differential is behaving open on coast and the inside wheel is effectively locking relative to the outside. This creates a yaw moment. Increasing coast lock stabilizes this behavior. If the car understeers on entry, the differential may already have excessive coast lock and resistance to rotation is occurring before the driver expects it.

**Gear Usage Distribution**
Logging gear position against track position across multiple laps allows identification of gears that are either rarely used or only briefly engaged. A gear that is selected for fewer than two seconds before requiring an immediate upshift or downshift indicates a ratio gap or a mismatch between the gear range and the circuit's speed profile. Individual gear ratios can be tightened or widened to eliminate short-dwell gears. Laps with clean sector times can be compared against gear traces to identify where ratio changes would allow longer time in the peak power band.

**RPM Traces for Gear Ratio Optimization**
Plotting engine RPM against time or track position highlights how well the current ratios keep the engine in its power band. Ideally RPM should remain within the upper portion of the power band between shifts, dropping briefly after each upshift but recovering quickly. If RPM drops far below the power band on upshifts, gears are spaced too wide (numerically too far apart). If RPM approaches the limiter and stays there across long straights, the final drive or top gear ratio is too short. If the engine enters the overrev zone before a corner without a gear being available, an additional gear may be needed or the final drive should be lengthened.

---

## Cross-References

- **vehicle_balance_fundamentals.md** — Understeer and oversteer balance, weight transfer mechanics, and how differential locking interacts with overall chassis balance at different corner phases.
- **braking.md** — Brake bias and its interaction with coast differential lock; how rear engine braking torque combines with mechanical braking to affect entry stability.
- **tyre_dynamics.md** — Slip ratio and slip angle theory; understanding how driven wheel spin relates to tyre load sensitivity and the grip envelope that differential settings must operate within.
