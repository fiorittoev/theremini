import math
import time
from typing import Optional, Tuple
import serial
import rtmidi


class MidiController:
    # Scale patterns remain the same
    MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
    MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10, 12]
    PENTATONIC_SCALE = [0, 2, 4, 7, 9, 12, 14, 16]
    BLUES_SCALE = [0, 3, 5, 6, 7, 10, 12, 15]

    def __init__(self, serial_port: str, midi_channel: int = 0):
        self.current_octave = 4
        self.current_scale = self.MAJOR_SCALE
        self.last_note = None
        self.powered = True
        self.show_guide = False

        # MIDI setup with loopMIDI support
        self.midi_channel = midi_channel
        self.midi_out = rtmidi.RtMidiOut()

        # Find and connect to loopMIDI port
        port_number = self.find_loopmidi_port()
        if port_number is not None:
            self.midi_out.openPort(port_number)
            print(
                f"Connected to loopMIDI port: {self.midi_out.getPortName(port_number)}"
            )
        else:
            print("No loopMIDI port found! Creating one...")
            self.midi_out.openVirtualPort("FreeWilly MIDI")
            print("Created virtual MIDI port: FreeWilly MIDI")

        # Serial setup
        self.serial_port = serial_port
        self.current_cents = 0
        self.current_volume = 0

    def find_loopmidi_port(self) -> Optional[int]:
        """Find the first available loopMIDI port."""
        ports = self.midi_out.getPortCount()
        print("\nAvailable MIDI ports:")
        for i in range(ports):
            port_name = self.midi_out.getPortName(i)
            print(f"  {i}: {port_name}")
            # Look for typical loopMIDI port names
            if "loop" in port_name.lower() or "virtual" in port_name.lower():
                return i
        return None

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
        self.midi_out.sendMessage([0xE0 | self.midi_channel, lsb, msb])

        # Handle note changes
        if self.last_note != note:
            if self.last_note is not None:
                # Send note off for previous note
                self.midi_out.sendMessage([0x80 | self.midi_channel, self.last_note, 0])

            # Send note on for new note
            self.midi_out.sendMessage([0x90 | self.midi_channel, note, velocity])
            self.last_note = note
        else:
            # Update velocity if note hasn't changed
            self.midi_out.sendMessage([0x90 | self.midi_channel, note, velocity])

    def cents_to_midi_note(self, cents: float) -> Tuple[int, float]:
        """Convert cents to MIDI note number and remaining cents for pitch bend."""
        semitones = cents / 100.0
        whole_semitones = int(math.floor(semitones))
        remaining_cents = (semitones - whole_semitones) * 100
        midi_note = 60 + whole_semitones  # Middle C (60) as base note
        return midi_note, remaining_cents

    def cents_to_pitch_bend(self, cents: float) -> int:
        """Convert cents to MIDI pitch bend value (0-16383)."""
        normalized = (cents / 100.0) / 2.0  # +/-1 semitone range
        pitch_bend = int(8192 + (normalized * 8192))
        return max(0, min(16383, pitch_bend))

    def process_serial_data(self, baudrate: int = 9600, timeout: int = 1):
        try:
            with serial.Serial(self.serial_port, baudrate, timeout=timeout) as ser:
                print(f"Connected to serial port: {self.serial_port}")

                line_counter = 0
                while self.powered:
                    try:
                        raw_data = ser.readline().decode("utf-8").strip()
                        if raw_data:
                            # Convert string to float, handling potential formatting issues
                            try:
                                # Handle common number formats and remove any non-numeric characters
                                # except decimal point and minus sign
                                cleaned_data = ''.join(c for c in raw_data if c.isdigit() or c in '.-')
                                value = float(cleaned_data)

                                # Alternate between processing pitch and volume
                                if line_counter % 2 == 0:
                                    self.current_cents = max(-1200, min(1200, value))
                                else:
                                    self.current_volume = max(0.0, min(1.0, value))
                                    self.send_midi_messages()

                                line_counter += 1

                            except ValueError as e:
                                print(f"Could not convert '{raw_data}' to float: {e}")
                                continue

                    except ValueError as e:
                        print(f"Invalid data format: {e}")
                        continue

        except KeyboardInterrupt:
            self.power_off()
        except serial.SerialException as e:
            print(f"Serial port error: {e}")
        finally:
            if self.last_note is not None:
                self.midi_out.sendMessage([0x80 | self.midi_channel, self.last_note, 0])
            self.midi_out.closePort()

    def power_off(self):
        if self.last_note is not None:
            self.midi_out.sendMessage([0x80 | self.midi_channel, self.last_note, 0])
        self.powered = False


def main():
    import sys
    import serial.tools.list_ports

    SERIAL_PORT = "COM3"

    print(f"\nUsing serial port: {SERIAL_PORT}")

    MIDI_CHANNEL = 0  # MIDI channel 1

    try:
        controller = MidiController(SERIAL_PORT, MIDI_CHANNEL)
        controller.process_serial_data()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
