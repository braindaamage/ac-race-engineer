# Telemetry and Diagnosis

## Physical Principles

### Data Structure and Sampling

Telemetry data is a collection of time-series channels recorded at a fixed sample rate during a driving session. In Assetto Corsa, the in-game app captures data at approximately 20–30 Hz, meaning each channel produces 20 to 30 data points per second. Each sample is a scalar value associated with a timestamp, so the complete dataset is a two-dimensional structure: time on one axis and channel value on the other.

Because the sample rate is finite, rapid transients — such as a kerb strike or an abrupt steering correction — may be captured at lower fidelity than they occur in reality. Events shorter than the sampling interval (33–50 ms at 20–30 Hz) cannot be resolved individually and will appear blurred or averaged across adjacent samples. This is an important limitation when diagnosing very brief phenomena such as ABS pulses or single-wheel lock-up events.

All channels share a common time axis for a given session file. Synchronisation across channels is therefore exact within the limits of the logger clock. Lap segmentation is performed by detecting when the car crosses the start/finish line, which introduces a fixed reference point for lap-relative analysis.

### Channel Categories

Telemetry channels fall into four broad categories:

**Driver Inputs** capture the commands the driver sends to the car. These include throttle position (0–1 normalized), brake pressure (0–1 normalized), steering angle (degrees or normalized), and clutch position. These channels represent intent rather than vehicle response and are useful for diagnosing driver technique, consistency, and how the car forces the driver to adapt.

**Vehicle Dynamics** channels describe the car's motion through space. Key channels include longitudinal acceleration (braking and acceleration forces in g), lateral acceleration (cornering force in g), yaw rate (rotation speed around the vertical axis in deg/s), wheel speeds (individual per-corner in km/h or m/s), gear position, and engine RPM. These channels capture the car's actual behaviour in response to driver inputs and road conditions.

**Tyre Data** channels cover the thermal and mechanical state of each tyre. Typical channels include tyre surface temperature (inner, middle, and outer zones), tyre core temperature, tyre pressure, and tyre slip ratio (longitudinal). Some implementations also expose lateral slip angle per wheel. Tyre channels are sampled per-corner and are critical for diagnosing grip levels, thermal degradation, and setup balance.

**Suspension Data** channels describe the mechanical behaviour of the suspension system. These include suspension travel (ride height delta at each corner), ride height (if available), and sometimes damper velocity (rate of suspension movement). These channels connect aerodynamic and mechanical grip to setup parameters more directly than any other category.

### Relationship Between Driver Inputs and Vehicle Response

Driver inputs are the cause; vehicle dynamics channels are the effect. However, the relationship is not one-directional. When a car understeers, the driver is often forced to use more steering angle than the car's geometry can effectively translate into lateral force. This causes driver inputs to carry embedded information about vehicle balance: a driver consistently using large steering angles mid-corner is responding to understeer, not causing it.

Similarly, throttle traces encode traction information. A driver who applies throttle smoothly but experiences wheelspin (detectable via wheel speed differential) is encountering a traction limitation, not a technique failure. Understanding this causal chain — setup affects vehicle response, vehicle response forces driver adaptation, driver adaptation shapes input channels — is essential for correct diagnosis.

### Data Resolution and Comparison Considerations

Meaningful diagnosis requires comparing laps under controlled conditions. Fuel load decreases over a stint, tyre temperatures evolve, and track rubber build-up changes grip levels throughout a session. These factors introduce variation unrelated to setup. When comparing two laps, the most reliable method is to select laps from similar positions within a stint and account for the direction of fuel and tyre evolution.

Spatial alignment — plotting channels against distance around the track rather than elapsed time — removes lap-time variation from the comparison and makes it easier to identify where on track a difference exists. The track is divided into corners with defined entry, apex, and exit points; analysing channels within those zones focuses the diagnosis on specific mechanical phenomena.

---

## Adjustable Parameters and Effects

### How Setup Parameters Influence Telemetry Channels

Each category of setup adjustment leaves a characteristic fingerprint in specific telemetry channels. Understanding these relationships allows the engineer to use telemetry not only to diagnose a problem but also to confirm whether a setup change had the intended effect.

**Springs and Ride Height** affect suspension travel channels. A stiffer spring reduces suspension travel amplitude and increases the rate of change (velocity) of suspension movement. Ride height directly offsets the suspension travel channel. When comparing setups with different spring rates, look for changes in the peak-to-peak amplitude of the suspension travel signal in high-load zones (braking, high-speed corners).

**Dampers (Bump and Rebound)** influence how quickly the suspension moves in response to inputs. High bump damping slows the compression stroke, which manifests as a reduced slope in the suspension travel channel during initial corner entry or kerb strikes. High rebound damping slows extension, visible as a slower return to ride height after compression. Damper effects are most legible in the suspension travel rate-of-change (velocity) derived signal rather than the travel position itself.

**Aerodynamic Balance** shifts the ratio of front-to-rear downforce. This directly affects the lateral acceleration distribution between axles, which appears as a change in the balance of understeer/oversteer in the mid-corner lateral acceleration signal. Front wing angle changes primarily affect entry and mid-corner balance; rear wing angle changes primarily affect high-speed stability and exit traction.

**Differential** settings affect how torque is split between driven wheels under power and overrun. A locked differential on exit produces a characteristic signature: both rear wheel speeds remain synchronised even as the car rotates, causing understeer on exit. A more open differential allows the inside wheel to spin relative to the outside, which can appear as a brief wheel speed divergence in the driven axle channels during corner exit.

**Alignment (Camber and Toe)** affects tyre temperature distribution. Excessive negative camber produces higher inner-zone temperatures; insufficient camber raises outer-zone temperatures. Toe-in at the rear increases stability, visible as reduced yaw rate overshoot at corner entry. Toe changes also affect straight-line pull, detectable as a non-zero steering angle input on a straight where zero input is expected.

**Brake Bias** shifts brake force distribution front-to-rear. A rear bias produces earlier rear wheel lock (rear wheel speed dropping to zero before the front), detectable in the wheel speed channels. A front bias can produce front lock and ABS engagement. Brake bias is one of the most directly readable parameters in telemetry because its effects appear clearly in wheel speed and brake pressure channels.

### Tracking Metric Changes After a Setup Adjustment

When a setup parameter is changed, define in advance which telemetry metrics are expected to change and in which direction. This avoids confirmation bias. For example, when increasing rear wing angle:

- Expected: lower top speed (detectable from peak speed channel on straights)
- Expected: reduced oversteer in high-speed corners (reduced yaw rate overshoot, more neutral lateral acceleration)
- Expected: possibly slower corner exit due to increased drag (throttle-to-apex speed relationship)

Tracking metrics systematically transforms telemetry from a diagnostic tool into an experimental validation tool.

---

## Telemetry Diagnosis

This section provides a comprehensive symptom-to-cause mapping. For each symptom, the table identifies likely mechanical or setup causes and specifies which telemetry channels carry the diagnostic signal.

### Understeer

| Phase | Symptom Description | Possible Causes | Channels to Inspect |
|-------|--------------------|-----------------|--------------------|
| Entry | Car fails to rotate on corner entry; driver adds steering angle without result | Excessive front toe-in, insufficient rear toe-out, front spring too stiff, rear anti-roll too soft, brake bias too far forward, excessive front downforce | Steering angle (high), yaw rate (low onset slope), lateral acceleration (low at entry), suspension travel front vs. rear (front not compressing enough) |
| Mid-corner | Car pushes wide in the sustained phase of the corner | Front camber too low (low front grip), front tyres overheating (check inner/outer temps), front wing too low, rear ride height too low creating rear grip advantage | Steering angle (persistently elevated), front tyre temperatures (inner zone hot), lateral acceleration front-limited, front suspension travel (saturated) |
| Exit | Car understeers when throttle is applied exiting the corner | Differential too locked (equalising driven wheels, creating push), rear toe too positive, too much rear downforce | Rear wheel speed (synchronised under power), steering angle (elevated at throttle application), throttle trace vs. lateral acceleration timeline |

### Oversteer

| Phase | Symptom Description | Possible Causes | Channels to Inspect |
|-------|--------------------|-----------------|--------------------|
| Entry | Rear steps out on corner entry before apex | Rear suspension too stiff (reduces rear mechanical grip), rear camber incorrect, trail braking losing rear grip, brake bias too rearward | Rear wheel speed (lock-up brief), yaw rate (rapid rise at entry), lateral acceleration (rear-limited onset), brake pressure vs. yaw rate timing |
| Mid-corner | Rear slides persistently at sustained lateral load | Rear downforce insufficient for speed, rear tyres overheating, rear spring too stiff preventing load transfer | Rear tyre temperatures (core or surface hot), lateral acceleration (rear saturating), yaw rate (elevated and noisy), rear suspension travel |
| Exit | Snap rotation when throttle is applied | Differential too open (inside wheel spin), rear tyres already at grip limit, too much rear torque relative to grip | Rear wheel speed divergence (inside vs. outside), throttle position vs. yaw rate (spike at throttle), rear tyre temps (already elevated entering exit) |

### Tyre Overheating

**Symptom**: Lap time degradation over stint, driver reports sliding. Tyre surface or core temperature exceeds optimal range.

**Possible Causes**: Camber angle mismatched to track demands, excessive scrubbing (too much toe), tyre pressure too high (stiffens carcass, reduces contact patch), mechanical grip shortage forcing excessive slip angles.

**Channels to Inspect**: Tyre temperature per zone (inner, mid, outer) — uneven distribution indicates camber issue; all zones uniformly high indicates slip angle excess or pressure issue. Compare tyre temp trends lap-over-lap to measure degradation rate. Correlate with steering angle (excessive angle forces high slip).

### Tyre Graining

**Symptom**: Short-term grip loss in first few laps before temperatures stabilise, tyre surface tears.

**Possible Causes**: Tyre pressure too low (carcass flexes excessively), tyre compound too hard for track temperature, aggressive driving on cold tyres.

**Channels to Inspect**: Tyre temperature (slow warm-up rate), tyre pressure (below optimal range), wheel speed vs. lateral acceleration (grip loss before thermal stabilisation). Look for inconsistent lateral acceleration in early stint laps compared to later laps.

### Inconsistent Braking

**Symptom**: Varied brake points or brake distances lap-to-lap; driver reporting difficulty with consistency.

**Possible Causes**: Tyre temperature variation at brake zone entry (inconsistent warm-up), ABS threshold sensitivity, brake bias drift, brake duct temperature affecting pad performance.

**Channels to Inspect**: Brake pressure trace shape lap-over-lap (compare peak pressure and ramp rate), longitudinal deceleration per lap (should be consistent for same brake zone), wheel speed (check for lock-up events — wheel speed dropping sharply to near zero), front vs. rear wheel speed during braking (reveals bias behaviour).

### Poor Traction

**Symptom**: Wheelspin or delayed acceleration on corner exit; car slides sideways rather than accelerating straight.

**Possible Causes**: Differential too open, rear tyre temperature too low at exit, rear downforce too low, too much throttle too early (driver adaptation to car limitation), power delivery characteristic.

**Channels to Inspect**: Rear wheel speed divergence (inside wheel spinning faster than outside), throttle trace vs. wheel speed (spin onset timing), yaw rate at exit (rotation under power), rear tyre temperatures at exit zones.

### High Tyre Wear

**Symptom**: Grip degradation accelerates through stint beyond expected; tyres reach wear limit earlier than baseline.

**Possible Causes**: Excessive camber (inner edge wear), excessive toe (scrubbing), hard braking generating sustained lock-up, sustained high slip angles due to imbalanced setup.

**Channels to Inspect**: Tyre temperatures (inner zone disproportionately hot = camber excess), wheel speed during braking (intermittent lock = flat-spot risk), lateral acceleration sustained near limit (high slip wear), slip ratio channel if available.

### Suspension Bottoming

**Symptom**: Car feels harsh over bumps or on kerbs; ride quality deteriorates; possible grounding noise.

**Possible Causes**: Ride height too low, springs too soft for downforce load, bump stops reached prematurely.

**Channels to Inspect**: Suspension travel (channel saturating at maximum compression limit), ride height (if logged), longitudinal and lateral acceleration spikes at bump zones (sharp high-amplitude spikes indicate bottoming contact).

### Poor Stability Under Braking

**Symptom**: Car moves under braking; rear wants to overtake the front; difficult to maintain straight line.

**Possible Causes**: Brake bias too rearward, rear tyre temperature below front tyre temperature at brake zone entry, rear suspension too stiff (reduces rear stability), rear downforce insufficient at braking speed.

**Channels to Inspect**: Brake pressure vs. yaw rate (yaw onset during braking = rear instability), rear vs. front wheel speed (rear locking before front), steering angle during braking (non-zero = correcting instability), lateral acceleration during braking (should be near zero on a straight).

### Snap Oversteer

**Symptom**: Sudden, abrupt rotation with little warning, difficult to catch.

**Possible Causes**: Rear tyre already at thermal saturation before the corner, rear suspension geometry causing sudden grip loss (bump steer), toe change under compression inducing rotation, differential engagement threshold.

**Channels to Inspect**: Rear tyre temperatures immediately before incident corner (pre-saturated), yaw rate (rate of change is very high — steep slope rather than gradual rise), steering angle (may show driver catch attempt — brief counter-steer), rear suspension travel (if jounce-induced toe is suspected, correlate suspension position with yaw onset).

### Driver Input Pattern Analysis

Beyond the symptom-to-cause table, driver input channels themselves reveal setup interaction patterns:

**Throttle Application Smoothness**: A smooth, monotonically increasing throttle trace from apex to exit indicates the car rewards progressive application. Jagged or stepped throttle traces indicate the driver is modulating to manage wheelspin or oversteer — a sign of traction deficit or differential sensitivity.

**Brake Trace Shape**: The optimal brake trace shows a sharp initial peak followed by a progressive trail-off into the corner (trail braking). A square-wave trace (full pressure held then released abruptly) often means the car is unstable under trail braking, forcing the driver to release early. The slope of brake release and its correlation with steering angle increase are diagnostic of entry behaviour.

**Steering Smoothness**: Smooth steering inputs in the mid-corner indicate the car is generating cornering force without requiring the driver to search for grip. Micro-corrections (small, rapid oscillations in the steering channel) indicate the car is at or near the grip limit and the driver is making constant corrections — often a sign of setup imbalance or tyre degradation.

### Lap Comparison Method

To compare two laps effectively: align both traces spatially (distance-based rather than time-based), then overlay the key channels for each corner zone. The recommended overlay set is: steering angle, lateral acceleration, throttle, brake, and tyre temperatures. Differences in steering angle at the same track position indicate a change in car balance. Differences in throttle application point indicate a change in exit confidence. Differences in lateral acceleration at the same steering input indicate a change in grip level.

---

## Cross-References

The following documents in this knowledge base provide detailed coverage of each topic introduced here. Telemetry diagnosis links directly to all of them, since telemetry is the observational layer through which all setup effects are measured.

- **vehicle_balance_fundamentals.md** — Understeer/oversteer balance, weight transfer mechanics, front-rear load distribution. The foundation for interpreting lateral acceleration and yaw rate patterns.
- **tyre_dynamics.md** — Slip angle theory, tyre temperature windows, pressure effects, graining and blistering mechanisms. Required reading for interpreting all tyre channel data.
- **suspension_and_springs.md** — Spring rates, ride height, anti-roll bar effects on weight transfer. Directly linked to suspension travel channel interpretation.
- **dampers.md** — Bump and rebound damping, transient response, frequency-dependent behaviour. Required for interpreting suspension travel rate-of-change signals.
- **alignment.md** — Camber, toe, caster effects on tyre contact patch and temperature distribution. Central to diagnosing asymmetric tyre temperature patterns.
- **aero_balance.md** — Front and rear downforce, drag, aerodynamic balance at speed. Required for interpreting high-speed corner behaviour and top-speed channels.
- **braking.md** — Brake bias, brake duct cooling, ABS interaction, trail braking physics. Required for interpreting brake pressure, wheel speed lock-up, and braking stability patterns.
- **drivetrain.md** — Differential locking, torque split, gear ratios, traction control interaction. Required for interpreting corner exit wheel speed divergence and traction deficit patterns.
- **setup_methodology.md** — The systematic process for making setup changes, prioritisation framework, and how to use telemetry evidence to guide setup sessions without circular reasoning.
