#!/usr/bin/env python3
"""
Interactive Finger Training Tool
Train each finger individually with real-time adjustment
"""

import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cv2
import mediapipe as mp
import Adafruit_PCA9685
import numpy as np
import json
import time

class FingerTrainer:
    def __init__(self):
        """Initialize hardware and tracking"""
        print("\n🎯 FINGER TRAINING TOOL 🎯\n")
        
        # Initialize PCA9685
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pwm.set_pwm_freq(50)
        
        # Finger channels
        self.fingers = {
            'thumb': {'flex': 0, 'abd': 1},
            'index': {'flex': 2, 'abd': 3},
            'middle': {'flex': 4, 'abd': 5},
            'ring': {'flex': 6, 'abd': 7}
        }
        
        # Load or create calibration
        self.calibration_file = "finger_training_data.json"
        self.calibration = self.load_calibration()
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Landmarks
        self.finger_landmarks = {
            'thumb': {'tip': 4, 'ip': 3, 'mcp': 2, 'cmc': 1},
            'index': {'tip': 8, 'pip': 6, 'mcp': 5},
            'middle': {'tip': 12, 'pip': 10, 'mcp': 9},
            'ring': {'tip': 16, 'pip': 14, 'mcp': 13}
        }
        self.wrist = 0
        
        # Training state
        self.current_finger = None
        self.training_mode = None  # 'flex' or 'abd'
        self.training_stage = 0
        self.samples = {'open': [], 'closed': []}
        
        # Manual adjustment values
        self.manual_flex_offset = 0
        self.manual_abd_offset = 0
        self.flex_multiplier = 1.0
        self.abd_multiplier = 1.0
        
        # Smoothing
        self.current_values = {
            'thumb': {'flex': 0.5, 'abd': 0.5},
            'index': {'flex': 0.5, 'abd': 0.5},
            'middle': {'flex': 0.5, 'abd': 0.5},
            'ring': {'flex': 0.5, 'abd': 0.5}
        }
        
        print("✓ Hardware initialized")
    
    def load_calibration(self):
        """Load calibration data"""
        default = {
            'thumb': {
                'flex': {'min': 150, 'max': 600, 'neutral': 375, 'offset': 0, 'multiplier': 1.0},
                'abd': {'min': 200, 'max': 550, 'neutral': 375, 'offset': 0, 'multiplier': 1.0}
            },
            'index': {
                'flex': {'min': 150, 'max': 600, 'neutral': 375, 'offset': 0, 'multiplier': 1.0},
                'abd': {'min': 200, 'max': 550, 'neutral': 375, 'offset': 0, 'multiplier': 1.0}
            },
            'middle': {
                'flex': {'min': 150, 'max': 600, 'neutral': 375, 'offset': 0, 'multiplier': 1.0},
                'abd': {'min': 200, 'max': 550, 'neutral': 375, 'offset': 0, 'multiplier': 1.0}
            },
            'ring': {
                'flex': {'min': 150, 'max': 600, 'neutral': 375, 'offset': 0, 'multiplier': 1.0},
                'abd': {'min': 200, 'max': 550, 'neutral': 375, 'offset': 0, 'multiplier': 1.0}
            }
        }
        
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for finger in default:
                        if finger in loaded:
                            for motor in ['flex', 'abd']:
                                if motor in loaded[finger]:
                                    default[finger][motor].update(loaded[finger][motor])
                    print(f"✓ Loaded training data from {self.calibration_file}")
                    return default
            except:
                print("Using default calibration")
        return default
    
    def save_calibration(self):
        """Save calibration data"""
        try:
            with open(self.calibration_file, 'w') as f:
                json.dump(self.calibration, f, indent=2)
            print(f"✓ Saved training data to {self.calibration_file}")
        except Exception as e:
            print(f"Error saving: {e}")
    
    def calculate_distance(self, p1, p2):
        """Calculate distance between points"""
        return np.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2)
    
    def calculate_finger_flexion(self, landmarks, finger_name):
        """Calculate flexion with adjustments"""
        finger_lm = self.finger_landmarks[finger_name]
        tip = landmarks[finger_lm['tip']]
        
        if finger_name == 'thumb':
            base = landmarks[finger_lm['cmc']]
            mid = landmarks[finger_lm['ip']]
        else:
            base = landmarks[finger_lm['mcp']]
            mid = landmarks[finger_lm['pip']]
        
        tip_to_base = self.calculate_distance(tip, base)
        mid_to_base = self.calculate_distance(mid, base)
        
        if mid_to_base > 0:
            flex = 1 - (tip_to_base / (mid_to_base * 2.5))
            flex = max(0, min(1, flex))
            
            # Apply calibration adjustments
            offset = self.calibration[finger_name]['flex'].get('offset', 0)
            multiplier = self.calibration[finger_name]['flex'].get('multiplier', 1.0)
            
            flex = (flex * multiplier) + offset
            return max(0, min(1, flex))
        return 0
    
    def calculate_finger_abduction(self, landmarks, finger_name):
        """Calculate abduction with adjustments"""
        if finger_name == 'thumb':
            thumb_tip = landmarks[self.finger_landmarks['thumb']['tip']]
            index_mcp = landmarks[self.finger_landmarks['index']['mcp']]
            distance = self.calculate_distance(thumb_tip, index_mcp)
            abd = 1 - min(distance / 0.15, 1)
        elif finger_name == 'middle':
            abd = 0.5  # Middle stays neutral
        else:
            finger_tip = landmarks[self.finger_landmarks[finger_name]['tip']]
            middle_mcp = landmarks[self.finger_landmarks['middle']['mcp']]
            x_deviation = finger_tip.x - middle_mcp.x
            
            if finger_name == 'index':
                abd = 0.5 + (x_deviation * 2)
            else:  # ring
                abd = 0.5 - (x_deviation * 2)
            
            abd = max(0, min(1, abd))
        
        # Apply calibration adjustments
        offset = self.calibration[finger_name]['abd'].get('offset', 0)
        multiplier = self.calibration[finger_name]['abd'].get('multiplier', 1.0)
        
        abd = (abd * multiplier) + offset
        return max(0, min(1, abd))
    
    def map_to_pulse(self, finger, motor_type, value):
        """Map 0-1 value to pulse"""
        cal = self.calibration[finger][motor_type]
        
        if value <= 0.5:
            pulse = cal['min'] + (cal['neutral'] - cal['min']) * (value * 2)
        else:
            pulse = cal['neutral'] + (cal['max'] - cal['neutral']) * ((value - 0.5) * 2)
        
        return int(pulse)
    
    def set_finger(self, finger, flex_value, abd_value):
        """Set finger position with smoothing"""
        smoothing = 0.3
        
        self.current_values[finger]['flex'] += \
            (flex_value - self.current_values[finger]['flex']) * smoothing
        self.current_values[finger]['abd'] += \
            (abd_value - self.current_values[finger]['abd']) * smoothing
        
        flex_pulse = self.map_to_pulse(finger, 'flex', self.current_values[finger]['flex'])
        abd_pulse = self.map_to_pulse(finger, 'abd', self.current_values[finger]['abd'])
        
        self.pwm.set_pwm(self.fingers[finger]['flex'], 0, flex_pulse)
        self.pwm.set_pwm(self.fingers[finger]['abd'], 0, abd_pulse)
    
    def draw_ui(self, image, landmarks=None):
        """Draw training UI"""
        h, w = image.shape[:2]
        
        # Dark overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        if self.current_finger:
            # Training mode indicator
            finger_name = self.current_finger.upper()
            mode = self.training_mode.upper() if self.training_mode else "SELECT"
            
            cv2.putText(image, f"Training: {finger_name} - {mode}", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
            
            if landmarks:
                flex = self.calculate_finger_flexion(landmarks, self.current_finger)
                abd = self.calculate_finger_abduction(landmarks, self.current_finger)
                
                # Draw values
                cv2.putText(image, f"Flexion: {flex:.2f}", (20, 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(image, f"Abduction: {abd:.2f}", (20, 110),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Adjustments
                offset_flex = self.calibration[self.current_finger]['flex'].get('offset', 0)
                mult_flex = self.calibration[self.current_finger]['flex'].get('multiplier', 1.0)
                
                cv2.putText(image, f"Offset: {offset_flex:.2f} Mult: {mult_flex:.2f}", 
                           (300, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        else:
            cv2.putText(image, "Select finger to train (1-4)", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3)
        
        # Instructions
        instructions = [
            "1-4: Select finger | F/A: Flex/Abd mode",
            "W/S: Adjust offset | E/D: Adjust multiplier",
            "R: Reset | Space: Save | Q: Quit"
        ]
        
        y = h - 70
        for inst in instructions:
            cv2.putText(image, inst, (20, y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y += 25
    
    def run(self):
        """Main training loop"""
        # Initialize camera
        print("Starting camera...")
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("\n" + "="*60)
        print("FINGER TRAINING CONTROLS")
        print("="*60)
        print("1: Train Thumb    | 2: Train Index")
        print("3: Train Middle   | 4: Train Ring")
        print()
        print("F: Focus on Flexion  | A: Focus on Abduction")
        print()
        print("W/S: Increase/Decrease Offset")
        print("E/D: Increase/Decrease Multiplier")
        print()
        print("R: Reset adjustments | Space: Save | Q: Quit")
        print("="*60)
        
        finger_map = {
            ord('1'): 'thumb',
            ord('2'): 'index',
            ord('3'): 'middle',
            ord('4'): 'ring'
        }
        
        try:
            while True:
                ret, image = cap.read()
                if not ret:
                    continue
                
                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                results = self.hands.process(image_rgb)
                
                landmarks = None
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(
                            image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        landmarks = hand_landmarks.landmark
                        
                        # Update all fingers
                        for finger in ['thumb', 'index', 'middle', 'ring']:
                            flex = self.calculate_finger_flexion(landmarks, finger)
                            abd = self.calculate_finger_abduction(landmarks, finger)
                            self.set_finger(finger, flex, abd)
                
                self.draw_ui(image, landmarks)
                
                cv2.imshow('Finger Training', image)
                
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                
                elif key in finger_map:
                    self.current_finger = finger_map[key]
                    print(f"\n→ Selected {self.current_finger.upper()}")
                
                elif key == ord('f'):
                    if self.current_finger:
                        self.training_mode = 'flex'
                        print(f"→ Training {self.current_finger} FLEXION")
                
                elif key == ord('a'):
                    if self.current_finger:
                        self.training_mode = 'abd'
                        print(f"→ Training {self.current_finger} ABDUCTION")
                
                elif key == ord('w'):
                    if self.current_finger and self.training_mode:
                        self.calibration[self.current_finger][self.training_mode]['offset'] += 0.05
                        print(f"Offset: {self.calibration[self.current_finger][self.training_mode]['offset']:.2f}")
                
                elif key == ord('s'):
                    if self.current_finger and self.training_mode:
                        self.calibration[self.current_finger][self.training_mode]['offset'] -= 0.05
                        print(f"Offset: {self.calibration[self.current_finger][self.training_mode]['offset']:.2f}")
                
                elif key == ord('e'):
                    if self.current_finger and self.training_mode:
                        self.calibration[self.current_finger][self.training_mode]['multiplier'] += 0.1
                        print(f"Multiplier: {self.calibration[self.current_finger][self.training_mode]['multiplier']:.2f}")
                
                elif key == ord('d'):
                    if self.current_finger and self.training_mode:
                        self.calibration[self.current_finger][self.training_mode]['multiplier'] -= 0.1
                        print(f"Multiplier: {self.calibration[self.current_finger][self.training_mode]['multiplier']:.2f}")
                
                elif key == ord('r'):
                    if self.current_finger and self.training_mode:
                        self.calibration[self.current_finger][self.training_mode]['offset'] = 0
                        self.calibration[self.current_finger][self.training_mode]['multiplier'] = 1.0
                        print("→ Reset adjustments")
                
                elif key == ord(' '):
                    self.save_calibration()
                    print("✓ Training data saved!")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
        
        finally:
            print("\nCleaning up...")
            for i in range(8):
                self.pwm.set_pwm(i, 0, 0)
            cap.release()
            cv2.destroyAllWindows()
            self.hands.close()
            print("✓ Training complete")


if __name__ == "__main__":
    trainer = FingerTrainer()
    trainer.run()
