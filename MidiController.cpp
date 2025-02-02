#include "MidiController.h"
#include <cmath>

// Scale patterns (semitones from root)
const int MAJOR_SCALE[] = {0, 2, 4, 5, 7, 9, 11, 12};
const int MINOR_SCALE[] = {0, 2, 3, 5, 7, 8, 10, 12};
const int PENTATONIC_SCALE[] = {0, 2, 4, 7, 9, 12, 14, 16};
const int BLUES_SCALE[] = {0, 3, 5, 6, 7, 10, 12, 15};

// MIDI constants from original code
const int MIDI_NOTE_ON = 144;
const int MIDI_NOTE_OFF = 128;

extern void MIDImessage(int command, int MIDInote, int MIDIvelocity);

MidiController::MidiController()
    : currentOctave(BASE_OCTAVE)
    , currentScale(Scale::MAJOR)
    , lastNote(-1)
    , powered(true)
    , showGuide(false)
{}

void MidiController::processAccelData(int16_t x, int16_t y) {
    if (!powered) return;

    // Calculate magnitude from center
    float magnitude = std::sqrt(x*x + y*y);
    
    if (magnitude < DEAD_ZONE) {
        if (lastNote >= 0) {
            sendMidiNote(lastNote, false);
            lastNote = -1;
        }
        return;
    }

    int note = calculateNote(x, y);
    if (note != lastNote) {
        if (lastNote >= 0) {
            sendMidiNote(lastNote, false);
        }
        sendMidiNote(note, true);
        lastNote = note;
    } else {
        // Sustain the note by sending a note-on message with the same note
        sendMidiNote(note, true);
    }
}

int MidiController::calculateNote(int16_t x, int16_t y) const {
    // Calculate angle from accelerometer values (0-360 degrees)
    float angle = std::atan2(y, x * 2) * 180.0f / M_PI; // Emphasize horizontal tilting by multiplying x by 2
    if (angle < 0) angle += 360.0f;
    
    // Convert angle to note index (0-7)
    int index = static_cast<int>((angle / 360.0f) * 8);
    
    // Get current scale pattern (C Major Scale)
    const int* scale = MAJOR_SCALE;
    
    // Ensure the index is within the 8-note range
    index = index % 8;
    
    return (currentOctave * 12) + scale[index];
}

int MidiController::calculateVelocity(int16_t x, int16_t y) const {
    float magnitude = std::sqrt(x*x + y*y);
    // Map magnitude to MIDI velocity (0-127)
    return std::min(127, static_cast<int>((magnitude - DEAD_ZONE) / 32767.0f * 127.0f));
}

void MidiController::sendMidiNote(int note, bool noteOn) {
    MIDImessage(
        noteOn ? MIDI_NOTE_ON : MIDI_NOTE_OFF,
        note,
        noteOn ? calculateVelocity(lastNote, lastNote) : 0
    );
}

// Button control implementations
void MidiController::octaveUp() {
    if (powered && currentOctave < 8) currentOctave++;
}

void MidiController::octaveDown() {
    if (powered && currentOctave > 0) currentOctave--;
}

void MidiController::nextScale() {
    if (!powered) return;
    currentScale = static_cast<Scale>((static_cast<int>(currentScale) + 1) % 4);
}

void MidiController::toggleGuide() {
    if (powered) showGuide = !showGuide;
}

void MidiController::powerOff() {
    if (lastNote >= 0) {
        sendMidiNote(lastNote, false);
    }
    powered = false;
}