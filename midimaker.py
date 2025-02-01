import math
import time
from typing import Optional, Tuple
import serial
import rtmidi

class MidiController:
    # Scale patterns (semitones from root)
    MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
    MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10, 12]
    PENTATONIC_SCALE = [0, 2, 4, 7, 9, 12, 14, 16]
    BLUES_SCALE = [0, 3, 5, 6, 7, 10, 12, 15]
    
    def __init__(self, serial_port: str, midi_channel: int = 0):
        self.current_octave = 4  # BASE_OCTAVE
        self.current_scale = self.MAJOR_SCALE
        self.last_note = None
        self.powered = True
        self.show_guide = False
        
        # MIDI setup
        self.midi_channel = midi_channel
        self.midi_out = rtmidi.MidiOut()
        available_ports = self.midi_out.get_ports()
        if available_ports:
            self.midi_out.open_port(0)
        else:
            self.midi_out.open_virtual_port("Virtual MIDI Output")
            
        # Serial setup
        self.serial_port = serial_port
        
    def process_accel_data(self, x: int, y: int):
        """Process accelerometer data and convert to MIDI."""
        if not self.powered:
            return
            
        # Calculate magnitude from center
        magnitude = math.sqrt(x*x + y*y)
        
        DEAD_ZONE = 100
        if magnitude < DEAD_ZONE:
            if self.last_note is not None:
                self.send_midi_note(self.last_note, False)
                self.last_note = None
            return
            
        note = self.calculate_note(x, y)
        if note != self.last_note:
            if self.last_note is not None:
                self.send_midi_note(self.last_note, False)
            self.send_midi_note(note, True)
            self.last_note = note
            
    def calculate_note(self, x: int, y: int) -> int:
        """Calculate MIDI note from accelerometer position."""
        # Calculate angle from accelerometer values (0-360 degrees)
        angle = math.atan2(y, x) * 180.0 / math.pi
        if angle < 0:
            angle += 360.0
            
        # Convert angle to note index (0-7)
        index = int((angle / 360.0) * 8)
        
        return (self.current_octave * 12) + self.current_scale[index]
        
    def calculate_velocity(self, x: int, y: int) -> int:
        """Calculate MIDI velocity from accelerometer magnitude."""
        magnitude = math.sqrt(x*x + y*y)
        # Map magnitude to MIDI velocity (0-127)
        DEAD_ZONE = 100
        return min(127, int((magnitude - DEAD_ZONE) / 32767.0 * 127.0))
        
    def send_midi_note(self, note: int, note_on: bool):
        """Send MIDI note message."""
        command = 0x90 if note_on else 0x80
        command |= self.midi_channel
        velocity = self.calculate_velocity(note, note) if note_on else 0
        self.midi_out.send_message([command, note, velocity])
        
    def process_serial_data(self, baudrate: int = 9600, timeout: int = 1):
        """Process incoming serial data from Free Willy."""
        try:
            with serial.Serial(self.serial_port, baudrate, timeout=timeout) as ser:
                print(f"Connected to {self.serial_port}")
                
                while self.powered:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        if data:
                            # Parse x,y accelerometer data
                            x, y = map(int, data.split(','))
                            self.process_accel_data(x, y)
                            
                    except ValueError as e:
                        print(f"Invalid data format: {e}")
                        continue
                        
        except KeyboardInterrupt:
            self.power_off()
            
        except serial.SerialException as e:
            print(f"Serial port error: {e}")
            
        finally:
            if self.last_note is not None:
                self.send_midi_note(self.last_note, False)
            self.midi_out.close_port()
    
    # Button control methods
    def octave_up(self):
        if self.powered and self.current_octave < 8:
            self.current_octave += 1
            
    def octave_down(self):
        if self.powered and self.current_octave > 0:
            self.current_octave -= 1
            
    def next_scale(self):
        if not self.powered:
            return
        scales = [self.MAJOR_SCALE, self.MINOR_SCALE, self.PENTATONIC_SCALE, self.BLUES_SCALE]
        current_index = scales.index(self.current_scale)
        self.current_scale = scales[(current_index + 1) % len(scales)]
        
    def toggle_guide(self):
        if self.powered:
            self.show_guide = not self.show_guide
            
    def power_off(self):
        if self.last_note is not None:
            self.send_midi_note(self.last_note, False)
        self.powered = False

def main():
    # Configure serial port and MIDI settings
    SERIAL_PORT = "/dev/ttyUSB0"  # Adjust for your system
    MIDI_CHANNEL = 0  # MIDI channel 1
    
    controller = MidiController(SERIAL_PORT, MIDI_CHANNEL)
    controller.process_serial_data()

if __name__ == "__main__":
    main()