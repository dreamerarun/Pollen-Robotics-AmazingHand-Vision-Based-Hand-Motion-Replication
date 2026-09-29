# Pollen Robotics AmazingHand — Vision-Based Hand Motion Replication

A Raspberry Pi 4 based Physical AI project for replicating human hand/finger motion on the **Pollen Robotics AmazingHand** using camera-based hand tracking and MG servos.

The system uses **MediaPipe + OpenCV** to detect human hand landmarks, converts the observed finger motion into normalized flexion/abduction values, applies servo-specific calibration, and drives the hand through a **PCA9685 PWM controller**.

> **Project goal:** understand and implement the complete pipeline from human motion perception to robotic actuation.

## Demo

The project can reproduce individual finger movements and predefined hand gestures such as:

- Open hand
- Closed hand / fist
- Pointing
- Peace sign
- Thumbs up
- Individual finger open/close/neutral control

The manual controller also provides an interactive command interface for testing the calibrated hand.

## Hardware

- [Pollen Robotics AmazingHand](https://github.com/pollen-robotics/AmazingHand)
- Raspberry Pi 4 Model B
- MG servos
- PCA9685 16-channel PWM servo driver
- USB/camera module for human-hand tracking
- Appropriate external servo power supply

### Servo channel mapping

| Finger | Flexion | Abduction |
|---|---:|---:|
| Thumb | PCA9685 CH0 | CH1 |
| Index | PCA9685 CH2 | CH3 |
| Middle | PCA9685 CH4 | CH5 |
| Ring | PCA9685 CH6 | CH7 |

The current software controls four fingers and two motion components per finger.

## System Architecture

```text
              Human Hand
                   │
                   ▼
             Camera / USB
                   │
                   ▼
          OpenCV image capture
                   │
                   ▼
        MediaPipe Hand Landmarks
                   │
          ┌────────┴────────┐
          ▼                 ▼
      Flexion            Abduction
     estimation          estimation
          │                 │
          └────────┬────────┘
                   ▼
        Calibration / Mapping
       offset + multiplier
                   │
                   ▼
        0–1 normalized motion
                   │
                   ▼
        Servo PWM conversion
                   │
                   ▼
             PCA9685
                   │
                   ▼
             MG Servos
                   │
                   ▼
          AmazingHand motion
```

## Software

- Python 3
- OpenCV
- MediaPipe
- NumPy
- Adafruit PCA9685 Python library
- JSON calibration data

## Repository Structure

```text
AmazingHand/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── train.py
├── finger_training.py
├── manual_hand_control.py
│
├── finger_training_data.json
├── servo_training_angles.json
│
└── media/
    └── demo/
```

### Main programs

#### `finger_training.py`

Camera-based real-time hand tracking and servo calibration.

It:

1. Captures the camera image.
2. Detects one human hand using MediaPipe.
3. Extracts hand landmarks.
4. Estimates flexion and abduction.
5. Applies per-finger calibration.
6. Smooths the motion.
7. Converts the normalized value into servo PWM.
8. Sends commands to the PCA9685.

The calibration interface supports selecting:

```text
1 → Thumb
2 → Index
3 → Middle
4 → Ring
```

Then:

```text
F → Flexion
A → Abduction
W/S → Increase/decrease offset
E/D → Increase/decrease multiplier
R → Reset
Space → Save
Q → Quit
```

#### `train.py`

Use this program for the servo-position training/calibration workflow used by the manual controller.

The resulting calibrated servo values are stored in:

```text
servo_training_angles.json
```

#### `manual_hand_control.py`

Provides a text-based interface for testing the calibrated hand.

Example:

```text
hand> open
hand> close
hand> neutral

hand> thumb open
hand> index close
hand> middle neutral

hand> fist
hand> peace
hand> point
hand> thumbsup

hand> demo
hand> stop
hand> quit
```

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/AmazingHand.git
cd AmazingHand
```

Create a virtual environment if desired:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Make sure I2C is enabled on the Raspberry Pi.

Check that the PCA9685 is visible:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

The PCA9685 is commonly detected at address `0x40`, depending on the board configuration.

## Calibration Workflow

### 1. Check the hardware

Before running the camera tracker, verify:

- PCA9685 is connected correctly.
- Servo power is connected separately and safely.
- Raspberry Pi ground and servo-driver ground are common.
- Servo channels match the configured mapping.
- The hand can move freely without mechanical obstruction.

### 2. Run the calibration/training program

```bash
python3 train.py
```

Follow the prompts used by your training program and save the resulting calibration data.

### 3. Run vision-based finger training

```bash
python3 finger_training.py
```

Select a finger and adjust its flexion or abduction response until the robotic motion follows the human hand comfortably.

Press `Space` to save:

```text
finger_training_data.json
```

### 4. Test manually

```bash
python3 manual_hand_control.py
```

Start with:

```text
hand> neutral
```

Then test:

```text
hand> open
hand> close
```

Only after confirming the servo limits are safe should you test gestures.

## Calibration Data

The calibration format stores independent parameters for each finger and motor:

```json
{
  "thumb": {
    "flex": {
      "min": 150,
      "max": 600,
      "neutral": 375,
      "offset": 0,
      "multiplier": 1.0
    },
    "abd": {
      "min": 200,
      "max": 550,
      "neutral": 375,
      "offset": 0,
      "multiplier": 1.0
    }
  }
}
```

The project uses:

- `min` — lower servo pulse limit
- `max` — upper servo pulse limit
- `neutral` — center position
- `offset` — motion correction
- `multiplier` — motion scaling

The calibration file is merged with default values so missing parameters can fall back to safe software defaults.

## Motion Mapping

The human hand motion is normalized to a `0–1` representation.

For flexion, the current implementation uses distances between relevant MediaPipe landmarks. The resulting value is constrained to the valid range before calibration is applied.

For abduction:

- Thumb uses thumb-tip to index-MCP distance.
- Middle finger is kept at neutral abduction.
- Index and ring use lateral deviation relative to the middle finger.

The normalized value is then mapped around the configured neutral pulse:

```text
0.0 ───────── 0.5 ───────── 1.0
min          neutral         max
```

A smoothing factor is also applied before sending the command to the servos to reduce sudden motion.

## Safety

**Servo limits must be calibrated for the physical hand before running unrestricted motion.**

Do not assume the example PWM values are safe for every AmazingHand build or MG servo.

Recommended procedure:

1. Remove mechanical load where possible.
2. Start with a conservative PWM range.
3. Test one servo at a time.
4. Verify the physical end stops.
5. Increase the range gradually.
6. Keep an emergency power disconnect available.
7. Never leave the system running unattended during initial calibration.

If a servo starts buzzing heavily, stalls, overheats, or pushes against a mechanical limit, stop immediately.

## Current Limitations

This implementation is intentionally lightweight and experimental.

- It tracks one human hand.
- The current implementation covers four fingers.
- Middle-finger abduction is kept neutral.
- The mapping is geometric rather than a full anatomical inverse-kinematics model.
- Camera viewpoint and hand orientation can affect tracking.
- MediaPipe landmark noise can introduce small servo movements.
- Calibration is specific to the mechanical setup and servo installation.
- No force/torque feedback is used.
- The system is position-driven rather than closed-loop force control.

## Why This Project?

I initially started this work while revisiting inverse kinematics. It evolved into a practical Physical AI experiment focused on a different question:

> **Can human hand motion be perceived, represented, calibrated, and reproduced directly on a physical robot?**

This project helped connect several layers of robotics:

**Perception → Motion Representation → Calibration → Control → Physical Actuation**

It also provides a foundation for future work involving:

- Better kinematic retargeting
- Multi-camera hand tracking
- 3D pose estimation
- Teleoperation
- Demonstration-data collection
- Imitation learning
- Vision-to-action policies
- Learning-based robotic hand control

## Reference

Original AmazingHand project:

https://github.com/pollen-robotics/AmazingHand

## Author

**Arun M**

Robotics & Physical AI

GitHub: https://github.com/dreamerarun
