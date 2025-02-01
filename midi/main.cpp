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
    if (pitch > 90) pitch = 90;

    // Map roll to MIDI Pitch Bend (-1200 to +1200 cents)
    double midiCents = ((roll - 270) / 360.0) * 2400;
    // Map pitch to MIDI Velocity (0 to 127)
    double velocity = 127 * (1 - (pitch / 90.0));

    // Debug Output
    printFloat("Pitch: %.1f ", printOutColor::printColorBlack, static_cast<float>(midiCents));
    printFloat("Velocity: %.1f\n", printOutColor::printColorBlack, static_cast<float>(velocity));
}


void loop()
{

    uint8_t event_data[FW_GET_EVENT_DATA_MAX] = {0};
    int last_event;

    printInt("\nloop()\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);

    // check if there is an event, and if so, get the data from it
    last_event = 0;
    if (hasEvent())
    {
        last_event = getEventData(event_data);
        printInt("Last event: %d\n", printOutColor::printColorBlack, printOutDataType::printUInt32, last_event);
    }

    // if the event was SENSOR_DATA, do something with it
    if (last_event == FWGUI_EVENT_GUI_SENSOR_DATA)
    {
        processAccelData(event_data);
    }

//as soon as I enable this if condition the app will not run...?
#if (0)
    // exit condition: red button pressed
    else if (last_event == FWGUI_EVENT_RED_BUTTON)
    {
        printInt("Exit...\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
        exitApp = 1;
    }
#endif
}

int main()
{
    setSensorSettings(1, 0, 100, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0);
    printInt("\nmain()\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    while (!exitApp)
    {
        loop();
        waitms(1000);
    }
    return 0;
}