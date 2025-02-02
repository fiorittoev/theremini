import math
import time
from typing import Optional, Tuple
import serial
import rtmidi
from rtmidi import MidiMessage
import re


class MidiController:
    # Scale patterns remain the same
    MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11, 12]
    MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10, 12]
    PENTATONIC_SCALE = [0, 2, 4, 7, 9, 12, 14, 16]
    BLUES_SCALE = [0, 3, 5, 6, 7, 10, 12, 15]

    def __init__(self, serial_port: str, midi_channel: int = 0):
        self.current_octave = 4
        self.current_scale = self.MINOR_SCALE
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
        self.current_midi_value = 60  # Middle C
        self.current_velocity = 64  # Middle velocity

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
        """Send MIDI messages based on current MIDI value and velocity."""
        if not self.powered:
            return

        # Handle note changes
        if self.last_note != self.current_midi_value:
            if self.last_note is not None:
                # Send note off for previous note
                note_off_msg = MidiMessage.noteOff(
                    self.midi_channel + 1, self.last_note
                )
                self.midi_out.sendMessage(note_off_msg)

            # Send note on for new note
            note_on_msg = MidiMessage.noteOn(
                self.midi_channel + 1, self.current_midi_value, self.current_velocity
            )
            self.midi_out.sendMessage(note_on_msg)
            self.last_note = self.current_midi_value
        else:
            # Update velocity if note hasn't changed
            note_on_msg = MidiMessage.noteOn(
                self.midi_channel + 1, self.current_midi_value, self.current_velocity
            )
            self.midi_out.sendMessage(note_on_msg)

    def strip_ansi_codes(self, text: str) -> str:
        """Remove ANSI escape codes from text."""
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

    def process_serial_data(self, baudrate: int = 9600, timeout: int = 1):
        try:
            with serial.Serial(self.serial_port, baudrate, timeout=timeout) as ser:
                print(f"Connected to serial port: {self.serial_port}")
                last_valid_midi = None
                last_valid_velocity = None

                while self.powered:
                    try:
                        raw_data = ser.readline().decode("utf-8").strip()
                        if raw_data:
                            try:
                                # Remove any prefixes and ANSI codes
                                data = raw_data.replace("0134", "").replace("134", "")
                                data = self.strip_ansi_codes(data)

                                # Split the string on whitespace
                                parts = data.split()
                                if len(parts) >= 2:
                                    midi_value = int(float(parts[0]))  # MIDI note value
                                    velocity = int(float(parts[1]))  # MIDI velocity

                                    # Ensure values are within MIDI ranges
                                    midi_value = max(0, min(127, midi_value))
                                    velocity = max(0, min(127, velocity))

                                    # Only update and send MIDI messages if the values have changed
                                    if (midi_value != last_valid_midi or 
                                        velocity != last_valid_velocity):
                                        
                                        self.current_midi_value = midi_value
                                        self.current_velocity = velocity
                                        self.send_midi_messages()

                                        # Update last valid values
                                        last_valid_midi = midi_value
                                        last_valid_velocity = velocity

                                        # Debug output
                                        print(
                                            f"MIDI Note: {self.current_midi_value}, Velocity: {self.current_velocity}"
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
                self.midi_out.sendMessage(
                    [int(0x80 | self.midi_channel), int(self.last_note), 0]
                )
            self.midi_out.closePort()


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
