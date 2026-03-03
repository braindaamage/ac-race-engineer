"""Mock acsys module for testing.

Defines CS class with all channel constants per research.md R-002.
"""


class CS:
    SpeedMS = 0
    Gas = 1
    Brake = 2
    Clutch = 3
    Gear = 4
    Steer = 5
    RPM = 6
    SpeedKMH = 7
    AccG = 8
    LocalVelocity = 9
    LocalAngularVelocity = 10
    NormalizedSplinePosition = 11
    LapCount = 12
    LapTime = 13
    CurrentTyresCoreTemp = 14
    DynamicPressure = 15
    SlipAngle = 16
    SlipRatio = 17
    TyreDirtyLevel = 18
    WheelAngularSpeed = 19
    SuspensionTravel = 20
    WorldPosition = 21
    TurboBoost = 22
    RideHeight = 23
    LapInvalidated = 24
    CamberDeg = 25
    LastLap = 26
    BestLap = 27
    DriveTrainSpeed = 28
    CGHeight = 29
    Caster = 30
    ToeInDeg = 31
    DriftBestLap = 32
    DriftLastLap = 33
    DriftPoints = 34
    SpeedTotal = 35
    Aero = 36
    TyreRadius = 37
    RollAngle = 38
    PitchAngle = 39
    Mz = 40
    Fy = 41
    SlipAngleContactPatch = 42
    Load = 43
    TyreLoadedRadius = 44
    Dy = 45
    NDSlip = 46
    TyreSurfaceDef = 47
    BrakeBias = 48
    TurboMaxBoost = 49
    ERSDelivery = 50
    ERSRecoveryLevel = 51
    ERSPowerLevel = 52
    ERSHeatCharging = 53
    ERSCurrentKJ = 54
    DRSAvailable = 55
    DRSEnabled = 56
    BrakeTemps = 57
    KersInput = 58
    CurrentTime = 59


class WHEELS:
    FL = 0
    FR = 1
    RL = 2
    RR = 3
