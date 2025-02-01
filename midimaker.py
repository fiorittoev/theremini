import math
import serial
import time
from typing import List, Optional
import rtmidi


class MidiController:
    # Scale patterns (semitones from root)
    MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
    MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10, 12]
    PENTATONIC_SCALE = [0, 2, 4, 7, 9, 12, 14, 16]
    BLUES_SCALE = [0, 3, 5, 6, 7, 10, 12, 15]

    # MIDI constants
    MIDI_NOTE_ON = 0x90
    MIDI_NOTE_OFF = 0x80

    def __init__(self):
        self.current_octave = 4  # BASE_OCTAVE
        self.current_scale = 0  # 0: Major, 1: Minor, 2: Pentatonic, 3: Blues
        self.last_note = -1
        self.powered = True
        self.show_guide = False
        self.dead_zone = 1000  # Adjust based on your accelerometer sensitivity

        # Initialize MIDI output
        self.midi_out = rtmidi.RtMidiOut()

        self.midi_out.openPort(0)  # Open the correct port

    def process_accel_data(self, x: int, y: int):
        """Process accelerometer data and convert to MIDI notes."""
        if not self.powered:
            return

        # Calculate magnitude from center
        magnitude = math.sqrt(x * x + y * y)

        if magnitude < self.dead_zone:
            if self.last_note >= 0:
                self.send_midi_note(self.last_note, False)
                self.last_note = -1
            return

        note = self.calculate_note(x, y)
        if note != self.last_note:
            if self.last_note >= 0:
                self.send_midi_note(self.last_note, False)
            self.send_midi_note(note, True)
            self.last_note = note

    def calculate_note(self, x: int, y: int) -> int:
        """Calculate MIDI note based on accelerometer position."""
        # Calculate angle from accelerometer values (0-360 degrees)
        angle = math.degrees(math.atan2(y, x))
        if angle < 0:
            angle += 360.0

        # Convert angle to note index (0-7)
        index = int((angle / 360.0) * 8)

        # Get current scale pattern
        scale = {
            0: self.MAJOR_SCALE,
            1: self.MINOR_SCALE,
            2: self.PENTATONIC_SCALE,
            3: self.BLUES_SCALE,
        }[self.current_scale]

        return (self.current_octave * 12) + scale[index]

    def calculate_velocity(self, x: int, y: int) -> int:
        """Calculate MIDI velocity based on movement magnitude."""
        magnitude = math.sqrt(x * x + y * y)
        return min(127, int((magnitude - self.dead_zone) / 32767.0 * 127.0))

    def send_midi_note(self, note: int, note_on: bool):
        """Send MIDI message."""
        command = self.MIDI_NOTE_ON if note_on else self.MIDI_NOTE_OFF
        velocity = (
            self.calculate_velocity(self.last_note, self.last_note) if note_on else 0
        )
        self.midi_out.send_message([command, note, velocity])

    # Control methods
    def octave_up(self):
        if self.powered and self.current_octave < 8:
            self.current_octave += 1

    def octave_down(self):
        if self.powered and self.current_octave > 0:
            self.current_octave -= 1

    def next_scale(self):
        if not self.powered:
            return
        self.current_scale = (self.current_scale + 1) % 4

    def toggle_guide(self):
        if self.powered:
            self.show_guide = not self.show_guide

    def power_off(self):
        if self.last_note >= 0:
            self.send_midi_note(self.last_note, False)
        self.powered = False
        self.midi_out.close_port()


def read_serial_data(
    port: str, midi_controller: MidiController, baudrate: int = 9600, timeout: int = 1
):
    """Read accelerometer data from serial port and convert to MIDI."""
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            try:
                data = ser.readline().decode("utf-8").strip()
                if data:
                    # Assuming data format is "x,y" as comma-separated integers
                    x, y = map(int, data.split(","))
                    midi_controller.process_accel_data(x, y)
            except KeyboardInterrupt:
                midi_controller.power_off()
                break
            except Exception as e:
                print(f"Error processing data: {e}")
                continue


if __name__ == "__main__":
    port = "/dev/ttyUSB0"  # Replace with your actual port
    controller = MidiController()
    read_serial_data(port, controller)
