"""Knowledge base index and signal-to-document mapping."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# KNOWLEDGE_INDEX: document → section → tags
# ---------------------------------------------------------------------------

KNOWLEDGE_INDEX: dict[str, dict[str, list[str]]] = {
    "vehicle_balance_fundamentals.md": {
        "Physical Principles": [
            "weight transfer", "understeer", "oversteer", "balance",
            "corner phase", "load", "gradient", "neutral steer",
            "load sensitivity", "lateral", "longitudinal",
        ],
        "Adjustable Parameters and Effects": [
            "spring rate", "anti-roll bar", "ride height",
            "weight distribution", "aero balance", "differential",
            "brake bias", "roll stiffness",
        ],
        "Telemetry Diagnosis": [
            "understeer ratio", "slip angle", "yaw rate",
            "lateral g", "steering angle", "throttle trace",
            "brake trace",
        ],
        "Cross-References": [
            "suspension_and_springs", "alignment", "aero_balance",
            "tyre_dynamics", "dampers", "braking", "drivetrain",
        ],
    },
    "tyre_dynamics.md": {
        "Physical Principles": [
            "slip angle", "traction circle", "friction ellipse",
            "thermal model", "core temperature", "surface temperature",
            "inner", "mid", "outer", "pressure", "contact patch",
            "wear", "degradation", "load sensitivity",
        ],
        "Adjustable Parameters and Effects": [
            "tyre pressure", "camber", "toe", "spring rate",
            "damper", "driving style", "contact patch",
            "temperature distribution",
        ],
        "Telemetry Diagnosis": [
            "tyre temperature", "temp spread", "inner mid outer",
            "slip angle", "slip ratio", "wear rate",
            "front rear balance", "core surface differential",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "alignment",
            "suspension_and_springs", "dampers", "braking",
        ],
    },
    "suspension_and_springs.md": {
        "Physical Principles": [
            "spring rate", "load transfer", "ride height",
            "anti-roll bar", "roll stiffness", "natural frequency",
            "motion ratio", "geometry",
        ],
        "Adjustable Parameters and Effects": [
            "front spring", "rear spring", "anti-roll bar",
            "ride height", "bump stop", "packer", "preload",
            "roll stiffness distribution",
        ],
        "Telemetry Diagnosis": [
            "suspension travel", "bottoming out", "ride height",
            "wheel load variation", "roll stiffness",
            "travel peak", "travel range",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "dampers",
            "alignment", "aero_balance",
        ],
    },
    "dampers.md": {
        "Physical Principles": [
            "bump", "rebound", "slow speed", "fast speed",
            "damper velocity", "transient", "steady state",
            "load transfer", "contact patch", "critical damping",
        ],
        "Adjustable Parameters and Effects": [
            "bump damping", "rebound damping", "front rear balance",
            "compression", "extension", "damper curve",
            "slow speed bump", "fast speed bump",
        ],
        "Telemetry Diagnosis": [
            "suspension velocity", "damper histogram",
            "wheel load fluctuation", "oscillation",
            "settling time", "ride quality",
        ],
        "Cross-References": [
            "suspension_and_springs", "vehicle_balance_fundamentals",
            "tyre_dynamics",
        ],
    },
    "alignment.md": {
        "Physical Principles": [
            "camber", "contact patch", "toe", "stability",
            "turn-in", "caster", "mechanical trail",
            "kingpin", "scrub radius", "tyre wear",
        ],
        "Adjustable Parameters and Effects": [
            "front camber", "rear camber", "front toe", "rear toe",
            "caster angle", "cornering grip", "straight-line stability",
            "turn-in response", "wear pattern",
        ],
        "Telemetry Diagnosis": [
            "tyre temperature", "inner mid outer", "wear pattern",
            "slip angle", "steering angle", "lateral g",
            "camber diagnostic", "temp spread",
        ],
        "Cross-References": [
            "tyre_dynamics", "suspension_and_springs",
            "vehicle_balance_fundamentals",
        ],
    },
    "aero_balance.md": {
        "Physical Principles": [
            "downforce", "drag", "wing", "diffuser",
            "ground effect", "aero balance", "ride height",
            "speed dependent", "aero map",
        ],
        "Adjustable Parameters and Effects": [
            "front wing", "rear wing", "splitter", "diffuser",
            "ride height", "gurney flap", "top speed",
            "cornering grip", "aero balance",
        ],
        "Telemetry Diagnosis": [
            "speed dependent balance", "high speed cornering",
            "low speed cornering", "drag", "speed trace",
            "ride height variation",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "suspension_and_springs",
            "setup_methodology",
        ],
    },
    "braking.md": {
        "Physical Principles": [
            "brake bias", "engine braking", "brake temperature",
            "fade", "trail braking", "weight transfer",
            "abs", "longitudinal", "deceleration",
        ],
        "Adjustable Parameters and Effects": [
            "brake bias", "brake duct", "pad compound",
            "engine brake", "brake pressure", "cooling",
        ],
        "Telemetry Diagnosis": [
            "brake trace", "lock-up", "wheel speed",
            "brake temperature", "deceleration", "trail braking",
            "steering angle",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "tyre_dynamics",
            "drivetrain",
        ],
    },
    "drivetrain.md": {
        "Physical Principles": [
            "differential", "lsd", "preload", "power ramp",
            "coast ramp", "gear ratio", "final drive",
            "open differential", "lock",
        ],
        "Adjustable Parameters and Effects": [
            "differential lock", "preload", "gear ratio",
            "final drive", "power lock", "coast lock",
            "acceleration", "top speed",
        ],
        "Telemetry Diagnosis": [
            "wheel speed differential", "wheelspin",
            "throttle", "coast instability",
            "gear distribution", "rpm",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "braking",
            "tyre_dynamics",
        ],
    },
    "telemetry_and_diagnosis.md": {
        "Physical Principles": [
            "telemetry", "time series", "channel", "sample rate",
            "driver input", "vehicle dynamics", "tyre data",
            "suspension data",
        ],
        "Adjustable Parameters and Effects": [
            "setup comparison", "telemetry comparison",
            "metric tracking", "parameter effect",
        ],
        "Telemetry Diagnosis": [
            "understeer", "oversteer", "tyre overheating",
            "graining", "braking", "traction", "tyre wear",
            "suspension bottoming", "stability", "snap oversteer",
            "symptom", "diagnosis", "throttle", "brake trace",
            "steering",
        ],
        "Cross-References": [
            "vehicle_balance_fundamentals", "tyre_dynamics",
            "suspension_and_springs", "dampers", "alignment",
            "aero_balance", "braking", "drivetrain",
            "setup_methodology",
        ],
    },
    "setup_methodology.md": {
        "Physical Principles": [
            "baseline", "one variable", "session planning",
            "change validation", "iterative refinement",
            "sensitivity analysis",
        ],
        "Adjustable Parameters and Effects": [
            "priority order", "parameter interaction",
            "change magnitude", "documentation",
            "safety", "balance", "grip", "fine-tuning",
        ],
        "Telemetry Diagnosis": [
            "before after comparison", "overlay", "sector analysis",
            "corner comparison", "statistical significance",
            "controlling variables", "improvement vs noise",
        ],
        "Cross-References": [
            "telemetry_and_diagnosis", "vehicle_balance_fundamentals",
        ],
    },
}


# ---------------------------------------------------------------------------
# SIGNAL_MAP: signal name → list of (document, section) tuples
# ---------------------------------------------------------------------------

SIGNAL_MAP: dict[str, list[tuple[str, str]]] = {
    "high_understeer": [
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
        ("vehicle_balance_fundamentals.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("aero_balance.md", "Adjustable Parameters and Effects"),
    ],
    "high_oversteer": [
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
        ("vehicle_balance_fundamentals.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("drivetrain.md", "Adjustable Parameters and Effects"),
    ],
    "tyre_temp_spread_high": [
        ("tyre_dynamics.md", "Telemetry Diagnosis"),
        ("tyre_dynamics.md", "Physical Principles"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
    ],
    "tyre_temp_imbalance": [
        ("tyre_dynamics.md", "Telemetry Diagnosis"),
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
    ],
    "lap_time_degradation": [
        ("tyre_dynamics.md", "Physical Principles"),
        ("tyre_dynamics.md", "Telemetry Diagnosis"),
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
        ("setup_methodology.md", "Telemetry Diagnosis"),
    ],
    "high_slip_angle": [
        ("tyre_dynamics.md", "Physical Principles"),
        ("tyre_dynamics.md", "Telemetry Diagnosis"),
        ("alignment.md", "Adjustable Parameters and Effects"),
    ],
    "suspension_bottoming": [
        ("suspension_and_springs.md", "Physical Principles"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Telemetry Diagnosis"),
    ],
    "low_consistency": [
        ("setup_methodology.md", "Physical Principles"),
        ("setup_methodology.md", "Telemetry Diagnosis"),
        ("telemetry_and_diagnosis.md", "Telemetry Diagnosis"),
    ],
    "brake_balance_issue": [
        ("braking.md", "Physical Principles"),
        ("braking.md", "Adjustable Parameters and Effects"),
        ("braking.md", "Telemetry Diagnosis"),
        ("vehicle_balance_fundamentals.md", "Physical Principles"),
    ],
    "tyre_wear_rapid": [
        ("tyre_dynamics.md", "Physical Principles"),
        ("tyre_dynamics.md", "Adjustable Parameters and Effects"),
        ("alignment.md", "Adjustable Parameters and Effects"),
        ("suspension_and_springs.md", "Adjustable Parameters and Effects"),
    ],
}
