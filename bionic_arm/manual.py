#!/usr/bin/env python3
"""
Manual Hand Control - Text Commands
Control the bionic hand using simple text commands
Uses trained servo angles from servo_training_angles.json
"""

import Adafruit_PCA9685
import json
import os
import time
import sys

class ManualHandControl:
    def __init__(self):
        """Initialize hand with trained data"""
        print("\n" + "="*60)
        print("🤖  MANUAL HAND CONTROL  🤖")
        print("="*60)
        
        # Initialize PCA9685
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pwm.set_pwm_freq(50)
        
        # Finger configuration
        self.fingers = {
            'thumb': {'flex': 0, 'abd': 1, 'name': 'Thumb'},
            'index': {'flex': 2, 'abd': 3, 'name': 'Index'},
            'middle': {'flex': 4, 'abd': 5, 'name': 'Middle'},
            'ring': {'flex': 6, 'abd': 7, 'name': 'Ring'}
        }
        
        # Load trained data
        self.training_file = "servo_training_angles.json"
        self.training_data = self.load_training_data()
        
        print("\n✓ Hardware initialized")
        print("✓ Training data loaded\n")
        
        # Initialize to neutral
        self.move_all('neutral', speed='fast')
        time.sleep(0.5)
    
    def load_training_data(self):
        """Load trained servo angles"""
        if not os.path.exists(self.training_file):
            print(f"✗ Training file not found: {self.training_file}")
            print("Please run train.py first to calibrate your servos!")
            sys.exit(1)
        
        try:
            with open(self.training_file, 'r') as f:
                data = json.load(f)
                print(f"✓ Loaded training data from {self.training_file}")
                return data
        except Exception as e:
            print(f"✗ Error loading training data: {e}")
            sys.exit(1)
    
    def set_servo(self, channel, pulse):
        """Set servo to specific pulse width"""
        pulse = int(max(150, min(600, pulse)))
        self.pwm.set_pwm(channel, 0, pulse)
    
    def move_finger(self, finger_name, position, speed='medium'):
        """
        Move a single finger to a position
        
        Args:
            finger_name: 'thumb', 'index', 'middle', 'ring'
            position: 'open', 'neutral', 'closed'
            speed: 'slow', 'medium', 'fast'
        """
        if finger_name not in self.fingers:
            print(f"✗ Unknown finger: {finger_name}")
            return
        
        if position not in ['open', 'neutral', 'closed']:
            print(f"✗ Unknown position: {position}")
            return
        
        # Get target pulses
        flex_pulse = self.training_data[finger_name]['flex'][position]
        abd_pulse = self.training_data[finger_name]['abd'][position]
        
        # Set servos
        self.set_servo(self.fingers[finger_name]['flex'], flex_pulse)
        self.set_servo(self.fingers[finger_name]['abd'], abd_pulse)
        
        # Delay based on speed
        delays = {'slow': 0.5, 'medium': 0.2, 'fast': 0.05}
        time.sleep(delays.get(speed, 0.2))
        
        print(f"✓ {self.fingers[finger_name]['name']}: {position}")
    
    def move_all(self, position, speed='medium'):
        """
        Move all fingers to the same position
        
        Args:
            position: 'open', 'neutral', 'closed'
            speed: 'slow', 'medium', 'fast'
        """
        if position not in ['open', 'neutral', 'closed']:
            print(f"✗ Unknown position: {position}")
            return
        
        print(f"→ Moving all fingers to {position.upper()}...")
        for finger in ['thumb', 'index', 'middle', 'ring']:
            self.move_finger(finger, position, speed)
        print(f"✓ All fingers: {position}")
    
    def stop_all(self):
        """Stop all servos"""
        for i in range(8):
            self.pwm.set_pwm(i, 0, 0)
        print("✓ All servos stopped")
    
    def demo_sequence(self):
        """Run a demo sequence"""
        print("\n→ Running demo sequence...\n")
        
        sequences = [
            ("Opening hand", 'open'),
            ("Closing hand", 'closed'),
            ("Neutral position", 'neutral'),
            ("Wave (index up)", None),
            ("Peace sign", None),
            ("Thumbs up", None),
            ("Pointing", None),
        ]
        
        for desc, pos in sequences:
            print(f"  {desc}...")
            time.sleep(1)
            
            if pos:
                self.move_all(pos, speed='medium')
            else:
                # Custom gestures
                if "Wave" in desc:
                    self.move_all('closed', 'fast')
                    self.move_finger('index', 'open', 'fast')
                
                elif "Peace" in desc:
                    self.move_all('closed', 'fast')
                    self.move_finger('index', 'open', 'fast')
                    self.move_finger('middle', 'open', 'fast')
                
                elif "Thumbs" in desc:
                    self.move_all('closed', 'fast')
                    self.move_finger('thumb', 'open', 'fast')
                
                elif "Pointing" in desc:
                    self.move_all('closed', 'fast')
                    self.move_finger('index', 'open', 'fast')
            
            time.sleep(1.5)
        
        print("\n✓ Demo complete!\n")
        self.move_all('neutral', 'medium')
    
    def print_help(self):
        """Print command help"""
        print("\n" + "="*60)
        print("AVAILABLE COMMANDS")
        print("="*60)
        print("\nBASIC POSITIONS:")
        print("  open          - Open all fingers")
        print("  close         - Close all fingers")
        print("  neutral       - Move all to neutral position")
        print()
        print("INDIVIDUAL FINGER CONTROL:")
        print("  thumb open    - Open thumb")
        print("  thumb close   - Close thumb")
        print("  thumb neutral - Thumb to neutral")
        print("  (Same for: index, middle, ring)")
        print()
        print("GESTURES:")
        print("  fist          - Make a fist")
        print("  wave          - Wave (index finger up)")
        print("  peace         - Peace sign (index + middle)")
        print("  point         - Point (index up)")
        print("  thumbsup      - Thumbs up")
        print("  ok            - OK sign (thumb + index circle)")
        print()
        print("UTILITY:")
        print("  demo          - Run demo sequence")
        print("  stop          - Stop all servos")
        print("  help          - Show this help")
        print("  quit / exit   - Exit program")
        print("="*60 + "\n")
    
    def execute_gesture(self, gesture):
        """Execute predefined gestures"""
        gesture = gesture.lower()
        
        if gesture == 'fist':
            print("→ Making fist...")
            self.move_all('closed', 'medium')
        
        elif gesture == 'wave':
            print("→ Waving...")
            self.move_all('closed', 'fast')
            self.move_finger('index', 'open', 'fast')
        
        elif gesture == 'peace':
            print("→ Peace sign...")
            self.move_all('closed', 'fast')
            self.move_finger('index', 'open', 'fast')
            self.move_finger('middle', 'open', 'fast')
        
        elif gesture == 'point':
            print("→ Pointing...")
            self.move_all('closed', 'fast')
            self.move_finger('index', 'open', 'fast')
        
        elif gesture == 'thumbsup':
            print("→ Thumbs up...")
            self.move_all('closed', 'fast')
            self.move_finger('thumb', 'open', 'fast')
        
        elif gesture == 'ok':
            print("→ OK sign...")
            self.move_all('open', 'fast')
            self.move_finger('thumb', 'neutral', 'fast')
            self.move_finger('index', 'neutral', 'fast')
        
        else:
            print(f"✗ Unknown gesture: {gesture}")
    
    def run_interactive(self):
        """Run interactive command loop"""
        self.print_help()
        
        print("Type commands below (or 'help' for command list):\n")
        
        try:
            while True:
                try:
                    cmd = input("hand> ").strip().lower()
                    
                    if not cmd:
                        continue
                    
                    parts = cmd.split()
                    
                    # Exit commands
                    if cmd in ['quit', 'exit', 'q']:
                        print("\n→ Exiting...")
                        break
                    
                    # Help
                    elif cmd == 'help':
                        self.print_help()
                    
                    # All fingers commands
                    elif cmd == 'open':
                        self.move_all('open')
                    
                    elif cmd in ['close', 'closed']:
                        self.move_all('closed')
                    
                    elif cmd == 'neutral':
                        self.move_all('neutral')
                    
                    # Demo
                    elif cmd == 'demo':
                        self.demo_sequence()
                    
                    # Stop
                    elif cmd == 'stop':
                        self.stop_all()
                    
                    # Gestures
                    elif cmd in ['fist', 'wave', 'peace', 'point', 'thumbsup', 'ok']:
                        self.execute_gesture(cmd)
                    
                    # Individual finger control
                    elif len(parts) == 2:
                        finger, position = parts
                        if finger in self.fingers and position in ['open', 'close', 'closed', 'neutral']:
                            if position == 'close':
                                position = 'closed'
                            self.move_finger(finger, position)
                        else:
                            print("✗ Invalid command. Try: thumb open, index close, etc.")
                    
                    else:
                        print("✗ Unknown command. Type 'help' for command list.")
                
                except EOFError:
                    print("\n→ EOF received, exiting...")
                    break
                
                except KeyboardInterrupt:
                    print("\n→ Use 'quit' to exit")
                    continue
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
        
        finally:
            print("\n→ Moving to neutral and stopping...")
            self.move_all('neutral', 'fast')
            time.sleep(0.5)
            self.stop_all()
            print("✓ Goodbye!\n")


def main():
    """Main function"""
    try:
        controller = ManualHandControl()
        controller.run_interactive()
    
    except KeyboardInterrupt:
        print("\n\n→ Interrupted by user")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
