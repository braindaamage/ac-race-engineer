# Tyre Dynamics

## Physical Principles

Tyres generate lateral and longitudinal forces through rubber deformation at the contact patch. Understanding the underlying physics is essential to interpreting telemetry and making setup decisions.

**Slip Angle and Lateral Force Generation**
Slip angle is the angular difference between the direction a tyre is pointing and the direction it is actually travelling. As slip angle increases from zero, lateral force rises steeply, peaks at the optimal slip angle (typically 6–12 degrees depending on compound and load), then falls as the tyre transitions into a sliding state. The shape of this curve — its peak value, the slip angle at peak, and how quickly it drops off — is a fundamental characteristic of the compound. Operating near the peak of this curve maximises cornering grip; operating significantly beyond it causes sliding and heat buildup.

**Slip Ratio and Longitudinal Force**
Longitudinal grip (traction and braking) is governed by slip ratio: the difference between the tyre's rotational speed and the vehicle's actual ground speed, expressed as a fraction. Like slip angle, there is an optimal slip ratio window (roughly 0.05–0.15 for most compounds) where peak braking or drive force is generated. Exceeding this window causes wheel lockup (braking) or wheelspin (acceleration).

**Traction Circle and Friction Ellipse**
The traction circle (or friction ellipse, since peak lateral and longitudinal forces are rarely equal) represents the total grip budget available to each tyre. A tyre generating maximum lateral force has little remaining capacity for longitudinal force, and vice versa. Combined demands — braking while cornering, or accelerating while unwinding steering — require both axes simultaneously and reduce the available peak in each direction. Trail braking exploits this principle deliberately. The shape of the ellipse is asymmetric: most tyres produce more lateral force than longitudinal, hence the ellipse rather than a perfect circle.

**Thermal Model: Core, Surface, and Lateral Zones**
Tyre temperature operates in two distinct layers. Surface temperature responds immediately to sliding friction and road contact but dissipates quickly. Core temperature builds more slowly through conduction from the surface and internal hysteresis (flex cycles in the sidewall and belt layers). Sustained high surface temps cook the core; sustained low surface temps mean the compound is not activating. Across the tyre's width, three zones are measured: inner (inboard), mid, and outer (outboard). Uniform distribution across these three zones indicates optimal camber and pressure loading. Deviations reveal contact patch distortion.

**Pressure Effects on Contact Patch**
Tyre pressure determines carcass stiffness and the geometry of the contact patch. Low pressure allows the carcass to conform more to the road surface, increasing contact area but reducing structural stiffness, which promotes overheating of the centre and increases the risk of the tread folding under high lateral load. High pressure concentrates load at the centre of the tread, reducing the effective contact area and shifting peak temperatures inward. There is an optimal pressure range for each compound where the contact patch shape is closest to rectangular, maximising the usable grip area.

**Wear Mechanisms**
Tyre wear results from two overlapping processes. Thermal degradation occurs when sustained high surface temperatures chemically alter the rubber compound, causing graining (surface tearing and redeposition) or blistering (subsurface vapour pockets). Mechanical wear is the progressive abrasion of rubber molecules from the tread surface due to sliding friction. Aggressive inputs — hard braking, high slip angles, rapid steering reversals — accelerate both mechanisms. Load sensitivity plays a role too: rubber compounds typically generate less additional grip per unit of additional load as load increases, meaning a heavily loaded tyre is less efficient per kilogram than a lightly loaded one.

---

## Adjustable Parameters and Effects

Several vehicle setup parameters directly influence how tyres behave thermally, mechanically, and in terms of load distribution.

**Tyre Pressures: Cold and Hot Targets**
Tyre pressure is set cold (at ambient temperature, before the session) but the target is a hot operating pressure reached at equilibrium during a lap. Cold pressures are lower than hot targets because tyres gain pressure as they heat up; the increase depends on tyre volume, compound, and operating temperature. Typical hot pressure targets range from 24–28 PSI for road-type tyres on road cars, and down to 20–22 PSI for some racing slick compounds, though this is highly compound-specific. Setting cold pressures too high results in excessive hot pressures, overloading the tyre centre, raising core temps, and reducing lateral grip. Setting cold pressures too low can cause carcass flex-induced overheating at the shoulders and instability under high lateral load. In Assetto Corsa, tyre pressure is set as a cold value; the simulation models thermal expansion dynamically.

**Camber: Contact Patch and Temperature Distribution**
Camber is the angle of the tyre relative to vertical when viewed from the front or rear. Negative camber (top of tyre leaning inward) compensates for the contact patch distortion caused by lateral cornering loads, which tend to roll the tyre onto its outer edge. The goal is to achieve a flat, fully engaged contact patch at the moment of peak cornering load. Too little negative camber leads to high outer-edge temperatures and reduced mid-corner grip. Too much negative camber concentrates load and heat on the inner edge during straight-line travel and reduces the effective contact area during braking. Because camber acts differently on the driving axle versus the non-driving axle, and because front and rear tyres experience different load conditions, front and rear camber are tuned independently. A typical starting range is -1.5 to -3.5 degrees negative for most circuit applications.

**Toe: Scrub and Heat Generation**
Toe describes whether the leading edges of the tyres on an axle point inward (toe-in) or outward (toe-out). Any non-zero toe setting means the tyres on an axle are not both pointing in the direction of travel simultaneously, which causes one tyre to operate at a continuous non-zero slip angle. This generates scrub — mechanical friction and associated heat — even in a straight line. Front toe-out promotes turn-in responsiveness by pre-loading the outer front tyre, but excessive toe-out increases tyre wear and straight-line temperature. Rear toe-in improves straight-line stability and reduces oversteer sensitivity, at the cost of some rear cornering compliance. Aggressive toe settings can generate significant tyre temperature differences between the two tyres on the same axle and accelerate wear on the leading edge.

**Spring and Damper Effects on Tyre Load Variation**
Suspension stiffness directly determines how much tyre load varies as the vehicle traverses bumps, kerbs, and transitions. Stiffer springs reduce body motion but transmit more road irregularity to the tyre, causing rapid fluctuations in normal load. Since tyre grip increases with load but at a diminishing rate, rapid load oscillations are worse for average grip than a steady load of the same mean value — this is load sensitivity at work. Very stiff suspension causes the tyre to skip over surface irregularities rather than conform to them, reducing the time-average contact patch area. Dampers control the rate of load change: too little damping allows the tyre load to oscillate at the suspension's natural frequency; too much damping causes the tyre to be dragged across surface irregularities rather than following them. Optimal damping keeps tyre load variation small and smooth.

**Driving Style Impact on Tyre Life**
Driver inputs have a large and direct effect on tyre thermal and mechanical wear. Late and aggressive braking repeatedly drives the tyre to its slip ratio limit and generates high longitudinal heat. High-slip-angle cornering — induced by excess entry speed or abrupt steering inputs — thermally loads the shoulder zones and mechanically grinds the tread surface. Kerb riding subjects the tyre to sharp, high-magnitude load spikes that can cause carcass damage and tread tearing. Wheelspin on exit concentrates longitudinal heat on the rear drive tyres. Smooth, progressive inputs that keep the tyre operating near but within the peak of its slip curves maximise grip consistency and tyre longevity over a stint.

---

## Telemetry Diagnosis

Tyre telemetry channels, when interpreted correctly, reveal the thermal and mechanical state of each tyre and indicate setup or driving deficiencies.

**Reading Tyre Temperatures: Inner/Mid/Outer Spread**
The three-zone temperature reading (inner, mid, outer) is the primary diagnostic tool for contact patch quality. A well-set-up tyre shows approximately uniform temperatures across all three zones, perhaps with the mid zone 5–10°C higher than the inner and outer due to central carcass flex. Significant deviations from uniformity indicate a contact patch problem. The spread (difference between highest and lowest zone) should ideally be less than 15–20°C. Larger spreads indicate that the contact patch is not uniformly loaded and that not all available rubber is contributing to grip. The absolute temperature level also matters: the compound must reach its operating window (which varies by compound type) to generate peak grip.

**Identifying Over- and Under-Inflation from Temperature Patterns**
Over-inflation raises the centre of the contact patch relative to the edges, concentrating load and heat centrally. This produces a temperature pattern where the mid zone is significantly hotter than the inner and outer zones. Under-inflation allows the centre to deform and the shoulders to carry disproportionate load, producing higher inner and outer readings relative to the mid. In practice, the camber-induced asymmetry (inner typically hotter than outer on a properly set up car) can mask this relationship, so the mid-to-shoulder differential must be evaluated in combination with camber readings and inner-to-outer asymmetry.

**Slip Angle and Slip Ratio Channels**
In Assetto Corsa, estimated slip angle and slip ratio are available as telemetry channels for each tyre. Slip angle channels show how far each tyre is operating from zero throughout a lap. Sustained high slip angles (beyond the compound's optimal peak) are associated with high lateral temperature generation and reduced grip. A front tyre running consistently high slip angles through a particular corner suggests the front is being asked for more than it can provide — either due to excess entry speed, understeer-inducing setup, or insufficient front camber. Comparing front and rear slip angles across a lap section helps identify balance issues. Slip ratio spikes during braking and acceleration zones indicate how close the driver is operating to the traction limit.

**Tyre Wear Rate Analysis**
Wear rate (change in tread depth per unit time or per lap) is typically not directly available in Assetto Corsa telemetry, but the simulation models it internally. A proxy for wear rate can be inferred from sustained high temperature readings, particularly on the inner or outer shoulder. Asymmetric wear between the two tyres on the same axle indicates a toe, camber, or drive balance problem. Wear concentrated at the inner shoulder is consistent with excessive negative camber or high lateral slip angle operation. Outer-edge wear suggests insufficient negative camber or excessive positive camber drift under load.

**Front-Rear Temperature Balance**
The ratio of front to rear tyre temperatures provides a cross-axle grip balance indicator. If the front tyres are consistently hotter than the rear across a range of corner types, the front tyres are working harder relative to the rear — a pattern associated with understeer in steady state or front tyre degradation before the rear. The reverse (rear hotter than front) is associated with oversteer tendency or rear-limited traction. Perfect balance means both axles are close to their optimal operating temperatures simultaneously, which correlates with a neutral, efficient handling balance.

**Core vs Surface Temperature Differential**
If both core and surface temperatures are available (some simulation channels distinguish them), the differential is a diagnostic of thermal state. A large surface-to-core gradient (surface much hotter than core) early in a stint indicates the tyre is not yet fully heated through. A large core-to-surface gradient (core hotter than surface) late in a stint indicates the rubber has been cooked from the inside and may be entering chemical degradation. In steady-state running, surface and core should be within approximately 10–20°C of each other. Sustained inversion (core significantly hotter than surface) is a warning of impending thermal degradation and reduced grip.

---

## Cross-References

The following documents in this knowledge base cover topics directly related to tyre dynamics and should be consulted alongside this document when diagnosing handling problems or evaluating setup changes.

- **vehicle_balance_fundamentals.md** — Covers understeer and oversteer balance, front-rear grip distribution, and the relationship between mechanical balance and tyre loading. Tyre temperature front-rear balance should be interpreted in conjunction with balance metrics.
- **alignment.md** — Covers camber and toe settings in detail, including their interaction with different tyre types and track surfaces. Provides guidelines for interpreting camber-related temperature asymmetry and toe-induced scrub heating.
- **suspension_and_springs.md** — Covers ride height, spring rates, and anti-roll bars and their effects on tyre load variation and contact patch consistency. Explains how suspension geometry changes interact with tyre camber gain in roll.
- **dampers.md** — Covers bump and rebound damping settings and their role in controlling tyre load oscillation over surface irregularities and kerbs. Relevant to understanding why tyre temperatures vary lap-to-lap on rough circuits.
- **braking.md** — Covers brake bias, braking technique, and their effects on longitudinal tyre loading and temperature. Relevant to diagnosing front or rear tyre overheating under braking and the role of brake-induced slip ratio in tyre wear.
