# Vehicle Balance Fundamentals

## Physical Principles

Vehicle balance describes the distribution of grip utilization between the front and rear axles at any given moment during a corner. A balanced car uses the available friction at both ends proportionally, while an imbalanced car overloads one axle before the other reaches its traction limit.

**Weight Transfer**

Weight transfer is the dynamic redistribution of vertical load across the tyres as the vehicle accelerates, brakes, or corners. It does not change the total mass of the car, but it changes how much load each tyre carries, which directly affects each tyre's grip potential.

Lateral weight transfer occurs during cornering and is proportional to lateral acceleration, centre-of-gravity height, and track width. The wider the track and lower the centre of gravity, the less weight is transferred per unit of lateral acceleration. Longitudinal weight transfer occurs under braking and acceleration, shifting load toward the front axle under deceleration and toward the rear under acceleration.

**Understeer and Oversteer Gradient**

Understeer and oversteer are defined by the relationship between front and rear slip angles. A slip angle is the angular difference between the direction a tyre is pointing and the direction it is actually travelling. When the front slip angles are larger than the rear slip angles for a given lateral acceleration, the car exhibits understeer — it requires more steering input than the theoretical neutral-steer angle. When the rear slip angles exceed the front, the car oversteers — the rear tends to rotate faster than commanded by steering input.

The understeer gradient is a measure of how rapidly the required steering angle increases with lateral acceleration. A neutral-steer car has a gradient of zero; understeering cars have a positive gradient; oversteering cars have a negative gradient.

**Balance by Corner Phase**

Balance is not a single static condition — it varies through each corner phase. At entry (trail-braking phase), longitudinal deceleration loads the front axle heavily while unloading the rear, which can promote oversteer at the rear or understeer if the front is saturated. At mid-corner (steady-state phase), the balance is dominated by the lateral load transfer distribution between axles. At exit (power application phase), longitudinal acceleration shifts load rearward, potentially inducing understeer at the front or oversteer at the rear depending on rear grip and differential behaviour.

**Neutral Steer and Load Sensitivity**

A neutrally steering car tracks a corner radius exactly consistent with the steering angle applied, requiring no correction under increasing speed. In practice, all production and race cars deviate from this ideal due to suspension geometry effects, aerodynamic contributions, and tyre load sensitivity. Load sensitivity refers to the non-linear relationship between vertical load and lateral grip — as load on a tyre increases, its grip increases, but at a diminishing rate. This means a tyre carrying double the load does not produce double the lateral force. This non-linearity is the fundamental reason why reducing weight transfer at one axle relative to the other changes balance: the more evenly load is distributed across a pair of tyres, the more total lateral force that axle can generate.

Tire load sensitivity is THE mechanism by which weight transfer distribution affects vehicle balance. The Fy-Fz relationship is concave — the effective friction coefficient (mu_eff = Fy/Fz) decreases with increasing vertical load. When lateral load transfer is biased toward one axle (via stiffer springs, stiffer ARB, or higher roll center at that end), the more heavily loaded tyre on that axle operates at a lower effective friction coefficient. The result is that axle saturates sooner, producing either understeer (if the front is more heavily loaded) or oversteer (if the rear is). Without understanding this mechanism, the rule "the stiffer end loses grip" is merely a memorised heuristic without physical foundation. In a hypothetical tire with a perfectly linear Fy-Fz response, redistributing lateral load would not affect balance at all.

**Weight Transfer Decomposition**
Total lateral load transfer at each axle is the sum of three distinct components. The geometric component acts through the roll center — it is instantaneous and proportional to the roll center height at each axle. The elastic component acts through springs and anti-roll bars — it is proportional to the roll stiffness distribution between front and rear axles and is the primary tuning target for balance. The unsprung mass component transfers load directly through the wheel and tyre without passing through the suspension. Ride height is a powerful tuning lever because it directly affects roll center position: lowering one end of the car shifts its roll center, altering the geometric component of load transfer at that axle and therefore the total lateral load transfer distribution. This geometric effect is separate from and additional to the aerodynamic effects of ride height.

**Total Lateral Load Transfer Distribution (TLLTD)**
TLLTD is the operational metric that unifies the effects of springs, anti-roll bars, and suspension geometry on balance. It expresses the fraction of total lateral load transfer that occurs at the front axle. A higher front TLLTD means more load transfer at the front, which (through load sensitivity) produces understeer. As an approximate starting rule, TLLTD front is roughly equal to the static front weight distribution plus approximately 5 percentage points — so a car with 47% front static weight typically has a TLLTD front around 52%. This approximation accounts for the typical roll center height distribution and roll stiffness split in most racing cars. TLLTD is the single most useful number for characterizing and comparing the steady-state balance potential of different setups.

**Transient vs Steady-State Balance**
The distinction between transient and steady-state balance is critical for correct diagnosis and tuning. Steady-state balance describes the car's behavior once the chassis has settled into a constant roll angle during sustained cornering — it is determined by the lateral load transfer distribution, which is a function of springs, ARBs, and suspension geometry (roll center heights). Transient balance describes the car's behavior during the dynamic phase when the chassis is still rolling, pitching, or yawing — turn-in, initial braking, throttle application. Transient balance is controlled primarily by dampers, which govern the rate at which load transfers between axles. These are fundamentally different phenomena requiring different tuning approaches: a car that understeers in steady-state mid-corner needs spring/ARB/geometry changes, while a car that understeers only during the initial turn-in phase may need damper revalving. Conflating the two leads to incorrect corrections — changing springs to fix a transient problem or changing dampers to fix a steady-state problem.


## Adjustable Parameters and Effects

Many setup parameters influence balance, and most act by changing the load transfer distribution between axles, altering tyre operating conditions, or modifying the mechanical or aerodynamic restoring forces available.

**Spring Rates**

Spring stiffness controls how much body roll occurs at a given lateral G and contributes to the roll stiffness distribution between front and rear axles. Stiffer springs resist body roll more effectively, keeping tyre camber angles closer to their static values. A stiffer front spring increases front roll stiffness, which shifts the lateral load transfer distribution (LLTD) toward the front axle, tending to increase understeer. A stiffer rear spring has the opposite directional effect. It is important to distinguish between two separate effects: springs (and ARBs) determine the magnitude and distribution of steady-state lateral load transfer — how much load ultimately transfers to each axle once the chassis has settled. Dampers control the transient rate at which that transfer occurs — how quickly the chassis reaches its final roll angle. Body roll rate (how fast the car rolls) and load transfer rate (how fast tyre loads change) are related but distinct: stiffer springs reduce the total amount of body roll and shift the steady-state LLTD, but they do not control the speed of load transfer during transient manoeuvres. Springs also interact with longitudinal weight transfer: stiffer springs resist pitch, which can affect brake balance feel and traction at the driven axle.

**Anti-Roll Bars**

Anti-roll bars (ARBs) resist differential compression between the inner and outer suspension on the same axle. Unlike springs, ARBs only generate force when there is a difference in suspension travel between the two sides — they have no effect in pure bump or rebound. Increasing front ARB stiffness raises the lateral load transfer at the front axle relative to the rear, which increases understeer tendency. Increasing rear ARB stiffness has the opposite effect. ARBs allow the engineer to separate roll stiffness from ride stiffness, enabling a soft ride (springs) while maintaining a stiff roll response (ARBs), or vice versa. This is a key tuning degree of freedom for balance adjustment without compromising mechanical grip over bumps.

**Ride Height**

Ride height affects the centre of gravity height and therefore the total magnitude of weight transfer at both axles. A lower ride height reduces the lever arm through which lateral acceleration acts to transfer load, reducing total weight transfer. Ride height also affects aerodynamic ground effect on cars with underbody downforce, altering the aerodynamic balance between front and rear. Changes in front vs rear ride height alter static rake angle, which shifts the aerodynamic pitch balance and may also change front-to-rear mechanical spring preload distribution.

**Weight Distribution**

The static fore-aft weight distribution — how much of the car's total weight rests on the front axle versus the rear — determines the baseline lateral load transfer split at each axle before any roll stiffness tuning. Moving weight forward biases the car toward understeer in steady-state; moving weight rearward biases it toward oversteer. Weight distribution interacts with moment of inertia: a car with its mass concentrated near the centre of the wheelbase rotates more easily than one with mass spread toward the ends.

**Aerodynamic Balance**

Downforce-generating devices (wings, splitters, diffusers, dive planes) generate vertical load proportional to the square of velocity. The ratio of front-to-rear aerodynamic downforce determines the aero balance, which acts additively to the mechanical balance. More front downforce increases effective front tyre load at high speed, tending to reduce high-speed understeer. More rear downforce increases rear tyre load and stability. Because aerodynamic forces scale with speed squared, the aero balance has increasing importance relative to mechanical balance as corner speed rises.

**Differential Settings**

The differential controls how torque is distributed between the driven wheels and how much rotational speed difference is permitted between them. Under power at corner exit, a locked or high lock percentage differential applies torque more equally to both driven wheels. On a rear-wheel-drive car, this resists the inner wheel spinning freely and can create an oversteering moment if the outer wheel is near its traction limit. A more open differential allows the inner wheel to spin with less resistance, which can reduce corner exit oversteer. In Assetto Corsa, the differential is modeled as a clutch-pack LSD with POWER and COAST lock percentages (0.0 = fully open, 1.0 = fully locked). Preload (in Nm) sets the baseline locking torque present at all times, affecting low-speed turn-in behavior. The POWER lock percentage governs locking under acceleration; the COAST lock percentage governs locking under engine braking and trailing throttle. On front-wheel-drive cars the interactions are reversed, with locking effects contributing to understeer.

**Brake Bias**

Brake bias controls the proportion of total braking force applied at the front versus the rear axle. A more forward bias increases front braking force, which increases longitudinal load transfer to the front and can generate more trail-brake understeer or, at the limit, front lock. A more rearward bias loads the rear less under braking, which can cause rear lock under heavy braking. Brake bias interacts with corner entry balance: engineers often adjust bias to balance the car's tendency to push or rotate during the trail-brake phase of entry.


## Telemetry Diagnosis

Telemetry channels provide the quantitative basis for identifying and characterizing balance conditions. The following channels and derived metrics are most relevant to balance analysis.

**Slip Angle Channels**

Front and rear slip angles, when available from simulation or estimated from vehicle state, are the most direct measure of balance. The ratio of front-to-rear slip angle magnitude at a given lateral acceleration indicates the balance gradient. A ratio above 1.0 (front slip exceeding rear slip) corresponds to understeer; a ratio below 1.0 corresponds to oversteer. Even without direct slip angle channels, the relationship between lateral acceleration and required steering input encodes this information.

**Understeer Ratio (Derived Metric)**

A common derived metric is the understeer ratio: the actual steering angle used divided by the theoretical Ackermann steering angle required for the vehicle's speed and corner radius. Values above 1.0 indicate understeer; values below 1.0 indicate oversteer. This metric is best computed at mid-corner under quasi-steady-state conditions (minimal longitudinal acceleration) to isolate the steady-state balance from transient effects.

**Yaw Rate**

Yaw rate measures the vehicle's rotation rate about its vertical axis. Comparing the measured yaw rate to the yaw rate predicted by the vehicle's speed and steering angle reveals whether the car is rotating more or less than commanded. A measured yaw rate below the predicted value is consistent with understeer; above it is consistent with oversteer. Yaw rate response lag (the time from steering input to yaw rate response) characterizes transient handling response.

**Lateral G and Steering Angle Patterns**

Plotting lateral acceleration versus steering angle across a corner lap-by-lap reveals how much steering correction the driver applies. A progressive increase in steering angle without a corresponding increase in lateral G is a signature of understeer — the front tyres are saturated. An abrupt increase in lateral G at low steering angle, or steering corrections opposite to corner direction, indicate oversteer. Corner phase segmentation is important here: entry, mid, and exit phases may show different balance characteristics that would be obscured by averaging over the full corner.

**Throttle and Brake Traces During Cornering**

Driver input traces contextualize the balance measurements. Early throttle application at corner exit indicates confidence in rear stability; late or hesitant throttle can indicate oversteer sensitivity. Brake trace shape at corner entry — particularly the presence of trail braking and its duration — correlates with corner entry rotation. A sharp brake-off before corner entry (box braking) versus a graduated trail-brake release will produce different corner entry balance signatures in the yaw rate and lateral G channels.

**Front vs Rear Tyre Temperature Distributions**

Tyre temperature distribution across the contact patch (inner, middle, outer) indicates loading and camber efficiency, while the front-to-rear temperature differential at matched grip utilization indicates which axle is working harder. If the front tyres consistently run hotter than the rear in steady-state cornering, the front axle is carrying a disproportionate share of the lateral load, which is consistent with understeer tendency. The reverse pattern is consistent with oversteer tendency. Temperature data is most useful when correlated with slip angle or lateral G to distinguish load-driven heating from camber- or alignment-driven effects.


## Cross-References

The following documents in this knowledge base contain detailed treatment of the subsystems and parameters that interact with vehicle balance:

- **suspension_and_springs.md** — Spring rate selection, spring rate effects on roll stiffness, anti-roll bar mechanisms, ride height geometry, and their interaction with weight transfer distribution.
- **alignment.md** — Static camber, toe, and caster settings; how alignment parameters shift the tyre's operating slip angle range and directional grip characteristics; camber effects on load sensitivity.
- **aero_balance.md** — Front and rear downforce generation mechanisms, aerodynamic balance adjustment via wing angles and splitter/diffuser trim, speed sensitivity of aero balance relative to mechanical balance.
- **tyre_dynamics.md** — Tyre friction circles, slip angle versus lateral force curves, load sensitivity coefficient, operating temperature windows, and how tyre compound selection interacts with balance sensitivity.
- **dampers.md** — Damper (shock absorber) effects on transient weight transfer, bump and rebound tuning for corner entry and exit stability, and platform control over kerbs and road irregularities.
- **braking.md** — Brake bias adjustment, brake force distribution, ABS interaction (where applicable), and the influence of braking on longitudinal load transfer and corner entry balance.
- **drivetrain.md** — Differential types and settings (open, limited-slip, locking), lock percentages and preload, torque vectoring where applicable, and their effects on driven-axle traction and corner exit balance.
