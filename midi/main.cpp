#include "fwwasm.h"
#include <cmath>    // For atan2, sqrt, fabs
#include <stdint.h> // For int types

// MIDI Note and Channel
#define MIDI_NOTE 60   // Middle C (C4)
#define MIDI_CHANNEL 0 // Channel 1 in MIDI

int8_t exitApp = 0;

// Process Accelerometer Data
void processAccelData(uint8_t *event_data) {
    int16_t iX, iY, iZ;
    float scaleFactor = 32768.0f / 2.0f; // ±2g

    iX = static_cast<int16_t>(event_data[0] | event_data[1] << 8);
    iY = static_cast<int16_t>(event_data[2] | event_data[3] << 8);
    iZ = static_cast<int16_t>(event_data[4] | event_data[5] << 8);

    float x = static_cast<float>(iX) / scaleFactor;
    float y = static_cast<float>(iY) / scaleFactor;
    float z = static_cast<float>(iZ) / scaleFactor;

    // Compute roll (pitch bend)
    double roll = atan2(y, z) * 180.0 / M_PI;
    if (roll < -90) {
        roll += 360;
    }

    // Compute pitch (velocity)
    double pitch = atan2(-x, sqrt(y * y + z * z)) * 180.0 / M_PI;
    pitch = fabs(pitch);

    // Map roll to MIDI Pitch Bend (-1200 to +1200 cents)
    double midiCents = ((roll - 270) / 360.0) * 2400;

    // Map pitch to MIDI Velocity (0 to 127) with a 45° limit
    double velocity;
    if (pitch > 45) {
        velocity = 127; // Max velocity at 45° or more
    } else {
        velocity = 127 * (pitch / 45.0); // Scale velocity linearly up to 45°
    }

    // Debug Output
    printFloat("%.1f ", printOutColor::printColorBlack, static_cast<float>(midiCents));
    printFloat("%.1f\n", printOutColor::printColorBlack, static_cast<float>(velocity));
}

void loop() {
    uint8_t event_data[FW_GET_EVENT_DATA_MAX] = {0};
    int last_event;

    // Check if there is an event, and if so, get the data from it
    last_event = 0;
    if (hasEvent()) {
        last_event = getEventData(event_data);
    }

    // If the event was SENSOR_DATA, process it
    if (last_event == FWGUI_EVENT_GUI_SENSOR_DATA) {
        processAccelData(event_data);
    }

    // Exit condition: red button pressed
    if (last_event == FWGUI_EVENT_RED_BUTTON) {
        printInt("Exit...\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
        exitApp = 1;
    }
}

int main() {
    setSensorSettings(1, 0, 10, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0);
    printInt("\nmain()\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    while (!exitApp) {
        loop();
        waitms(1000);
    }
    return 0;
}