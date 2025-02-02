#include "fwwasm.h"
#include <cmath>    // For atan2, sqrt, fabs
#include <stdint.h> // For int types

// MIDI Note and Channel
#define MIDI_NOTE 60   // Middle C (C4)
#define MIDI_CHANNEL 0 // Channel 1 in MIDI

int8_t exitApp = 0;

void processAccelData(uint8_t *event_data) {
    int16_t iX, iY, iZ;
    float scaleFactor = 32768.0f / 2.0f; // ±2g
    
    // Read raw accelerometer data
    iX = static_cast<int16_t>(event_data[0] | event_data[1] << 8);
    iY = static_cast<int16_t>(event_data[2] | event_data[3] << 8);
    iZ = static_cast<int16_t>(event_data[4] | event_data[5] << 8);
    
    // Scale accelerometer data to g-force
    float x = static_cast<float>(iX) / scaleFactor;
    float y = static_cast<float>(iY) / scaleFactor;
    float z = static_cast<float>(iZ) / scaleFactor;


    // Compute roll angle (in degrees)
    double roll = atan2(y, z) * 180.0 / M_PI;

    // Compute pitch angle (for volume control)
    double pitch = atan2(-x, sqrt(y * y + z * z)) * 180.0 / M_PI;
   
    double midi_note = 0.0;
    double midi_volume = 0.0;

    if (roll < -90.0)
    {
        roll = -90.0;
        midi_note = 60.0;

    }
    else if (roll >= -90.0 && roll <= -67.5){
        midi_note=60.0;
    }
    else if(roll >= -67.5 && roll <= -45.0){
        midi_note=62.0;
    }
    else if (roll >= -45.0 && roll <= -22.5){
        midi_note=64.0;
    }
    else if (roll >= -22.5 && roll <= 0.0){
        midi_note=65.0;
    }
    else if (roll >= 0.0 && roll <= 22.5){
        midi_note=67.0;
    }
    else if (roll >= 22.5 && roll <= 45.0){
        midi_note=69.0;
    }
    else if (roll >= 45.0 && roll <= 67.5){
        midi_note=71.0;
    }
    else if (roll >= 67.5 && roll <= 90.0){
        midi_note=72.0;
    }
    if (roll > 90) 
    {
        roll = 90;
        midi_note=72.0;
    }
    
    if (pitch < -30) {
        midi_volume = 127; // Max volume at 45° up or more
    } else if (pitch > 30) {
        midi_volume = 0; // Max volume at 45° up or more
    } else {
        // Linear mapping between -45° and +45°
        midi_volume = 127 * ((pitch + 30) / 90.0);
    }
     
    // Debug: Print MIDI pitch and velocity
    printFloat("%.1f ", printOutColor::printColorBlack, static_cast<float>(midi_note));
    printFloat("%.1f\n", printOutColor::printColorBlack, static_cast<float>(midi_volume));
}

// not "proper" loop check the note holding functions to play notes out
void loop() {
    uint8_t event_data[FW_GET_EVENT_DATA_MAX] = {0};
    int last_event;

    // Check if there is an event, and if so, get the data from it
    last_event = 0;
    //note changer here?
    if (hasEvent()) {
        last_event = getEventData(event_data);
    }

    // If the event was SENSOR_DATA, process it
    // note changer here?
    if (last_event == FWGUI_EVENT_GUI_SENSOR_DATA) {
        processAccelData(event_data);
    }

    // Reset accelerometer on blue button press
    if (last_event == FWGUI_EVENT_BLUE_BUTTON) {        
        // Reset accelerometer values to default (neutral position)
        uint8_t reset_data[6] = {0, 0, 0, 0, 0, 0}; // x = 0, y = 0, z = 1 (scaled)
        reset_data[4] = 0x00; // z low byte
        reset_data[5] = 0x40; // z high byte (scaled to 1g)

        // Process the reset data
        processAccelData(reset_data);
    }

    // Exit condition: red button pressed
    if (last_event == FWGUI_EVENT_RED_BUTTON) {
        printInt("Exit...\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
        exitApp = 1;
    }
}

int main() {
    //setup_panels();
    setSensorSettings(1, 0, 10, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0);
    printInt("\nmain()\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    while (!exitApp) {
        loop();
        waitms(20);  // Reduced wait time for more frequent updates, instead do the volume as a function to repaet
    }
    
    return 0;
}