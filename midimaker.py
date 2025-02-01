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
        self.midi_out = rtmidi.RtMidiOut()

        self.midi_out.openVirtualPort("Virtual MIDI Output")

        # Serial setup
        self.serial_port = serial_port

        # State for alternating line processing
        self.current_cents = 0
        self.current_volume = 0

    def send_midi_messages(self):
        """Send MIDI messages based on current cents and volume."""
        if not self.powered:
            return

        # Convert cents to note and pitch bend
        note, remaining_cents = self.cents_to_midi_note(self.current_cents)
        pitch_bend = self.cents_to_pitch_bend(remaining_cents)
        velocity = int(max(0, min(127, self.current_volume * 127)))

        # Send pitch bend
        msb = (pitch_bend >> 7) & 0x7F
        lsb = pitch_bend & 0x7F
        self.midi_out.send_message([0xE0 | self.midi_channel, lsb, msb])

        # Handle note changes
        if self.last_note != note:
            if self.last_note is not None:
                # Send note off for previous note
                self.midi_out.send_message(
                    [0x80 | self.midi_channel, self.last_note, 0]
                )

            # Send note on for new note
            self.midi_out.send_message([0x90 | self.midi_channel, note, velocity])
            self.last_note = note
        else:
            # Update velocity if note hasn't changed
            self.midi_out.send_message([0x90 | self.midi_channel, note, velocity])

    def cents_to_midi_note(self, cents: float) -> Tuple[int, float]:
        """Convert cents to MIDI note number and remaining cents for pitch bend."""
        # Calculate total semitones from cents
        semitones = cents / 100.0

        # Split into whole note and remaining cents
        whole_semitones = int(math.floor(semitones))
        remaining_cents = (semitones - whole_semitones) * 100

        midi_note = 60 + whole_semitones  # Middle C (60) as base note
        return midi_note, remaining_cents

    def cents_to_pitch_bend(self, cents: float) -> int:
        """Convert cents to MIDI pitch bend value (0-16383)."""
        # Map cents to pitch bend range (-8192 to +8191)
        normalized = (cents / 100.0) / 2.0  # +/-1 semitone range
        pitch_bend = int(8192 + (normalized * 8192))
        return max(0, min(16383, pitch_bend))

    def process_serial_data(self, baudrate: int = 9600, timeout: int = 1):
        """Process incoming serial data from Free Willy."""
        try:
            with serial.Serial(self.serial_port, baudrate, timeout=timeout) as ser:
                print(f"Connected to {self.serial_port}")

                line_counter = 0
                while self.powered:
                    try:
                        data = ser.readline().decode("utf-8").strip()
                        if data:
                            value = float(data)

                            # Alternate between processing pitch and volume
                            if line_counter % 2 == 0:
                                # First line is pitch (cents)
                                self.current_cents = max(-1200, min(1200, value))
                            else:
                                # Second line is volume (0-1)
                                self.current_volume = max(0.0, min(1.0, value))
                                # Send MIDI messages after we have both values
                                self.send_midi_messages()

                            line_counter += 1

                    except ValueError as e:
                        print(f"Invalid data format: {e}")
                        continue

        except KeyboardInterrupt:
            self.power_off()

        except serial.SerialException as e:
            print(f"Serial port error: {e}")

        finally:
            if self.last_note is not None:
                self.midi_out.send_message(
                    [0x80 | self.midi_channel, self.last_note, 0]
                )
            self.midi_out.closePort()

    # Button control methods remain the same
    def octave_up(self):
        if self.powered and self.current_octave < 8:
            self.current_octave += 1

    def octave_down(self):
        if self.powered and self.current_octave > 0:
            self.current_octave -= 1

    def next_scale(self):
        if not self.powered:
            return
        scales = [
            self.MAJOR_SCALE,
            self.MINOR_SCALE,
            self.PENTATONIC_SCALE,
            self.BLUES_SCALE,
        ]
        current_index = scales.index(self.current_scale)
        self.current_scale = scales[(current_index + 1) % len(scales)]

    def toggle_guide(self):
        if self.powered:
            self.show_guide = not self.show_guide

    def power_off(self):
        if self.last_note is not None:
            self.midi_out.send_message([0x80 | self.midi_channel, self.last_note, 0])
        self.powered = False


def main():
    # Configure serial port and MIDI settings
    SERIAL_PORT = "COM3"  # Adjust for your system
    MIDI_CHANNEL = 0  # MIDI channel 1

    controller = MidiController(SERIAL_PORT, MIDI_CHANNEL)
    controller.process_serial_data()


if __name__ == "__main__":
    main()
