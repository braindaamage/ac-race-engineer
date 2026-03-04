# Suspension and Springs

## Physical Principles

Springs are the primary element governing how a car's sprung mass (chassis and body) moves relative to its unsprung mass (wheels, hubs, and uprights). Their core function is to support the vehicle's weight while allowing the wheels to follow road surface variations independently of the chassis.

**Spring rate and load transfer speed.** When a car corners, brakes, or accelerates, weight transfers between axles and between left and right sides. The spring rate determines how quickly and how much the chassis rolls or pitches in response to those forces. A stiffer spring resists body motion more strongly, so load transfer through the chassis happens faster and with less body displacement. However, the total steady-state lateral load transfer at each axle is a function of geometry and weight distribution, not spring rate alone — springs govern the transient rate of transfer, not the final magnitude.

**Ride height and its mechanical effects.** Ride height affects the car's centre of gravity height, which scales all load transfer magnitudes. Lower ride height reduces CG height and therefore reduces the total load transfer for a given lateral acceleration, improving overall grip potential. Ride height also directly controls suspension geometry: as the car sits lower, roll centres shift, camber curves change, and anti-squat or anti-dive characteristics are altered. These geometry changes can affect tyre contact patch orientation and therefore effective grip at the limit.

**Anti-roll bars.** Anti-roll bars (ARBs) connect the left and right suspension on each axle and resist differential vertical movement — i.e., they resist roll without affecting single-wheel bump compliance. A stiffer front ARB relative to the rear transfers a greater share of total lateral load to the front axle, which increases front tyre load variation and typically produces understeer. Adjusting the front-to-rear roll stiffness ratio is the primary tool for tuning steady-state cornering balance without altering spring rates. The total roll stiffness (front + rear ARB combined with spring contribution) determines the overall roll angle at a given lateral acceleration.

**Natural frequency.** Each axle has a natural frequency of oscillation determined by the spring rate and the sprung mass supported by that axle. Expressed in Hz, typical values range from roughly 1–3 Hz for road-biased cars up to 4–8 Hz or more for high-downforce race cars. A lower natural frequency produces a softer, more compliant ride that keeps the tyre in contact with bumpy surfaces. Mismatched front and rear natural frequencies can cause pitch coupling — the car rocks fore-aft in a rocking-horse motion over successive bumps.

**Motion ratio.** Springs are rarely mounted directly at the wheel. The motion ratio is the ratio of spring displacement to wheel displacement. A motion ratio of 0.8 means the spring moves 0.8 mm for every 1 mm of wheel travel. Because spring force at the wheel scales with the square of the motion ratio (for a given spring rate), the effective wheel rate differs significantly from the spring rate. All spring rate discussions in an engineering context should clarify whether the value refers to spring rate at the spring or effective wheel rate at the contact patch.


## Adjustable Parameters and Effects

**Front and rear spring rates.** Spring rate is the fundamental stiffness of the coil or torsion bar spring, measured in N/mm or lb/in. Increasing front spring rate raises the front natural frequency, reduces front roll contribution from springs, and speeds up load transfer to the front axle during lateral events. It also reduces front body pitch under braking. Increasing rear spring rate similarly stiffens the rear platform, reducing squat under acceleration and rear roll. The balance between front and rear spring rates influences pitch behaviour and, through their interaction with ARBs, the overall roll stiffness distribution.

**Anti-roll bar stiffness — front and rear.** ARB stiffness is adjusted either by changing bar diameter, bar length, or the lever arm setting (on cars with adjustable blade or lever ARBs). Increasing front ARB stiffness increases the share of roll resistance provided by the front axle, which increases the lateral load variation on the front tyres and tends to produce understeer. Softening the front ARB (or stiffening the rear) shifts the balance toward oversteer. ARBs allow the engineer to tune cornering balance independently of single-wheel bump compliance, which is their primary advantage over adjusting spring rates alone.

**Ride height adjustment.** Ride height is typically adjusted via spring perch position (threaded collars on coilover units) or via packers/shims in fixed-seat configurations. Lowering the car reduces CG height and may improve aerodynamic efficiency if the car produces meaningful underbody or diffuser-dependent downforce. However, lowering the car also reduces available suspension travel, changes geometry, and risks bottoming out on kerbs or bumps. Front and rear ride heights are often adjusted independently to set the rake angle, which influences aerodynamic balance.

**Bump stop engagement.** Bump stops (also called jounce bumpers) are rubber or cellular foam elements that engage near the end of suspension travel and provide a sharply rising rate that prevents metal-to-metal contact. Their engagement point is critical: if they engage mid-corner, the effective spring rate increases suddenly, producing an abrupt change in handling balance. Bump stop engagement range and stiffness can sometimes be tuned by changing bump stop length or material.

**Packers and shims.** Packers are rigid spacers inserted into the damper or spring assembly to limit suspension travel in one direction. They effectively raise the bump stop engagement point without changing the spring rate in the free travel range. In high-downforce cars, packers are used at high-speed circuits to prevent excessive ride height drop under aerodynamic load while keeping the car compliant over low-speed bumps.

**Spring preload.** Preload is the initial compression applied to the spring before the car's weight is applied. In most setups, preload is adjusted to achieve the desired ride height without leaving a gap in the spring seat. Excessive preload on bump stops or springs can introduce asymmetric behaviour on kerbs. Preload does not change the spring rate — it shifts the operating range on the spring's travel.


## Telemetry Diagnosis

**Suspension travel channels.** Dedicated suspension potentiometers or string pots record the displacement of each corner's suspension in millimetres throughout the lap. From these channels, three key statistics are useful: the mean travel (how far the suspension is compressed on average, related to ride height under load), the peak travel (the maximum compression seen at any point), and the range (peak minus minimum, indicating total working travel used). Mean travel should be compared between similar-speed sections to assess ride height loss under aerodynamic load or fuel weight changes.

**Identifying bottoming out.** Bottoming out is indicated when the suspension travel channel reaches or holds at a hard limit for a sustained period, or when the damper velocity channel shows a sharp spike followed by an abrupt velocity reversal. On cars with bump stop telemetry, a step change in effective spring rate will appear as a slope change in the force-displacement relationship. Bottoming out on a fast corner is serious — it momentarily locks the wheel geometry and can cause a sudden loss of grip.

**Ride height changes during a stint.** As fuel is burned, the car becomes lighter and the springs extend slightly, raising ride height. For cars with aerodynamic sensitivity to ride height, this produces a progressive shift in downforce balance across the stint. Suspension travel data can be averaged lap-by-lap to track this drift. Conversely, on street circuits with significant tyre wear, the loss of tyre radius (blistering) can appear as a ride height change in the telemetry.

**Wheel load variation as an indicator of spring rate suitability.** If vertical load per wheel (derived from tyre model data or inferred from suspension force sensors) shows high variation on bumpy sections, the spring rate may be too stiff to absorb road inputs effectively. This manifests as high-frequency oscillation in the suspension travel channel. Comparing the amplitude of travel oscillations across axles can reveal which end of the car is struggling more with surface compliance.

**Roll stiffness distribution from lateral load transfer.** During a steady-state corner (constant radius, constant speed), the ratio of lateral load transfer at the front axle to total lateral load transfer reflects the roll stiffness distribution. If telemetry channels for individual tyre vertical loads are available, the inside/outside load difference can be compared front vs. rear. A front axle carrying a disproportionately high share of lateral load transfer will show high load variation on the front tyres, consistent with a front-biased roll stiffness distribution and likely understeer.


## Cross-References

- **vehicle_balance_fundamentals.md** — load transfer theory, understeer/oversteer definitions, and the relationship between roll stiffness distribution and steady-state balance.
- **dampers.md** — damper rates interact directly with spring rates to govern transient load transfer; spring and damper tuning must be done together to set natural frequency and damping ratio correctly.
- **alignment.md** — ride height changes alter camber and toe through the suspension geometry; any ride height adjustment should be followed by a geometry check to confirm camber and toe remain within target.
- **aero_balance.md** — on cars with meaningful aerodynamic downforce, ride height strongly influences front and rear downforce levels; spring rate and packer selection must account for the aerodynamic platform, not only mechanical grip targets.
