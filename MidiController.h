#pragma once
#include <stdint.h>

class MidiController {
public:
    static constexpr int16_t DEAD_ZONE = 100;  // Accelerometer dead zone threshold
    static constexpr int BASE_OCTAVE = 4;
    static constexpr int VELOCITY_DEFAULT = 100;

    enum class Scale {
        MAJOR,
        MINOR,
        PENTATONIC,
        BLUES
    };

    MidiController();
    
    // Process accelerometer data
    void processAccelData(int16_t x, int16_t y);
    
    // Button controls
    void octaveUp();
    void octaveDown();
    void nextScale();
    void toggleGuide();
    void powerOff();
    
    // Status
    bool isPowered() const { return powered; }
    bool isGuideVisible() const { return showGuide; }
    const char* getCurrentNoteName() const;
    Scale getCurrentScale() const { return currentScale; }

private:
    int currentOctave;
    Scale currentScale;
    int lastNote;
    bool powered;
    bool showGuide;
    
    void sendMidiNote(int note, bool noteOn);
    int calculateNote(int16_t x, int16_t y) const;
    int calculateVelocity(int16_t x, int16_t y) const;
};