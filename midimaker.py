import math
import time
from typing import Optional, Tuple
import serial
import rtmidi
import re


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
        self.midi_out = rtmidi.MidiOut()  # Changed from RtMidiOut to MidiOut

        # Find and connect to loopMIDI port
        port_number = self.find_loopmidi_port()
        if port_number is not None:
            self.midi_out.open_port(port_number)  # Changed from openPort to open_port
            print(
                f"Connected to loopMIDI port: {self.midi_out.get_port_name(port_number)}"  # Changed from getPortName to get_port_name
            )
        else:
            print("No loopMIDI port found! Creating one...")
            self.midi_out.open_virtual_port("FreeWilly MIDI")  # Changed from openVirtualPort to open_virtual_port
            print("Created virtual MIDI port: FreeWilly MIDI")

        # Serial setup
        self.serial_port = serial_port
        self.current_cents = 0
        self.current_volume = 0

    def find_loopmidi_port(self) -> Optional[int]:
        """Find the first available loopMIDI port."""
        ports = self.midi_out.get_port_count()  # Changed from getPortCount to get_port_count
        print("\nAvailable MIDI ports:")
        for i in range(ports):
            port_name = self.midi_out.get_port_name(i)  # Changed from getPortName to get_port_name
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
        self.midi_out.send_message([0xE0 | self.midi_channel, lsb, msb])  # Changed from sendMessage to send_message

        # Handle note changes
        if self.last_note != note:
            if self.last_note is not None:
                # Send note off for previous note
                self.midi_out.send_message([0x80 | self.midi_channel, self.last_note, 0])  # Changed from sendMessage to send_message

            # Send note on for new note
            self.midi_out.send_message([0x90 | self.midi_channel, note, velocity])  # Changed from sendMessage to send_message
            self.last_note = note
        else:
            # Update velocity if note hasn't changed
            self.midi_out.send_message([0x90 | self.midi_channel, note, velocity])  # Changed from sendMessage to send_message

    # ... rest of the methods remain the same ...

    def process_serial_data(self, baudrate: int = 9600, timeout: int = 1):
        try:
            with serial.Serial(self.serial_port, baudrate, timeout=timeout) as ser:
                print(f"Connected to serial port: {self.serial_port}")

                while self.powered:
                    try:
                        raw_data = ser.readline().decode("utf-8").strip()
                        if raw_data:
                            try:
                                # Remove the '0134' or '134' prefix
                                data = raw_data.replace("0134", "").replace("134", "")

                                # Strip ANSI escape codes
                                data = self.strip_ansi_codes(data)

                                # Split the string on whitespace
                                parts = data.split()
                                if len(parts) >= 2:
                                    cents = float(parts[0])
                                    volume = float(parts[1])
                                    print(cents,volume)

                                    # Process the values
                                    self.current_cents = max(-1200, min(1200, cents))
                                    self.current_volume = max(
                                        0.0, min(1.0, volume / 127.0)
                                    )
                                    self.send_midi_messages()
                                else:
                                    print(
                                        f"Invalid data format (not enough values): {raw_data}"
                                    )

                            except ValueError as e:
                                print(
                                    f"Could not parse values from '{raw_data}' -> '{data}': {e}"
                                )
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
                self.midi_out.send_message([0x80 | self.midi_channel, self.last_note, 0])  # Changed from sendMessage to send_message
            self.midi_out.close_port()  # Changed from closePort to close_port


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