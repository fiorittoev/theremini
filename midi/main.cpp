#include "fwwasm.h"
#include <math.h>    // For atan2, sqrt, fabs
#include <stdint.h>  // For int types

// MIDI Note and Channel
#define MIDI_NOTE 60   // Middle C (C4)
#define MIDI_CHANNEL 0 // Channel 1 in MIDI
#define MIN_OCTAVE 2   // Lowest octave
#define MAX_OCTAVE 6   // Highest octave

int8_t exitApp = 0;
int currentOctave = 4; // Start at middle octave

// Function to setup button menu text
void setupButtonMenus() {
    // Set menu text for grey and yellow buttons
    setPanelMenuText(0, 0, "Octave Up");   // Grey button
    setPanelMenuText(0, 1, "Octave Down"); // Yellow button
    setPanelMenuText(0, 3, "Reset");       // Blue button
    setPanelMenuText(0, 4, "Exit");        // Red button
}

void handleButtonEvent(int eventType, uint8_t buttonData) {
    const char* buttonAction = getButtonData(buttonData);
    
    // Only process "clicked" events
    if (strcmp(buttonAction, "clicked") == 0) {
        switch(eventType) {
            case FWGUI_EVENT_GRAY_BUTTON:
                if (currentOctave < MAX_OCTAVE) {
                    currentOctave++;
                    printInt("Octave Up: ", printOutColor::printColorBlack, printOutDataType::printUInt32, currentOctave);
                    printInt("\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
                }
                break;
                
            case FWGUI_EVENT_YELLOW_BUTTON:
                if (currentOctave > MIN_OCTAVE) {
                    currentOctave--;
                    printInt("Octave Down: ", printOutColor::printColorBlack, printOutDataType::printUInt32, currentOctave);
                    printInt("\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
                }
                break;

            case FWGUI_EVENT_BLUE_BUTTON:
                {
                    // Reset accelerometer values to default
                    uint8_t reset_data[6] = {0, 0, 0, 0, 0, 0};
                    reset_data[4] = 0x00;
                    reset_data[5] = 0x40;
                    processAccelData(reset_data);
                    currentOctave = 4; // Reset octave to middle
                    printInt("Reset to default position and middle octave\n", 
                            printOutColor::printColorBlack, 
                            printOutDataType::printUInt32, 0);
                }
                break;

            case FWGUI_EVENT_RED_BUTTON:
                printInt("Exit...\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
                exitApp = 1;
                break;
        }
    }
}

void processAccelData(uint8_t *event_data) {
    int16_t iX, iY, iZ;
    float scaleFactor = 32768.0f / 2.0f;
    
    iX = static_cast<int16_t>(event_data[0] | event_data[1] << 8);
    iY = static_cast<int16_t>(event_data[2] | event_data[3] << 8);
    iZ = static_cast<int16_t>(event_data[4] | event_data[5] << 8);
    
    float x = static_cast<float>(iX) / scaleFactor;
    float y = static_cast<float>(iY) / scaleFactor;
    float z = static_cast<float>(iZ) / scaleFactor;
    
    double roll = atan2(y, z) * 180.0 / M_PI;
    double pitch = atan2(-x, sqrt(y * y + z * z)) * 180.0 / M_PI;
   
    double midi_note = 0.0;
    double midi_volume = 0.0;
    
    // Note calculation with octave offset
    if (roll < -90.0) {
        roll = -90.0;
        midi_note = 60.0;
    } else if (roll >= -90.0 && roll <= -67.5) {
        midi_note = 60.0;
    } else if(roll >= -67.5 && roll <= -45.0) {
        midi_note = 62.0;
    } else if (roll >= -45.0 && roll <= -22.5) {
        midi_note = 64.0;
    } else if (roll >= -22.5 && roll <= 0.0) {
        midi_note = 65.0;
    } else if (roll >= 0.0 && roll <= 22.5) {
        midi_note = 67.0;
    } else if (roll >= 22.5 && roll <= 45.0) {
        midi_note = 69.0;
    } else if (roll >= 45.0 && roll <= 67.5) {
        midi_note = 71.0;
    } else if (roll >= 67.5 && roll <= 90.0) {
        midi_note = 72.0;
    }
    if (roll > 90) {
        roll = 90;
        midi_note = 72.0;
    }
    
    // Apply octave offset
    midi_note = midi_note + ((currentOctave - 4) * 12);
    
    // Volume calculation logic
    if (pitch < -30) {
        midi_volume = 127;
    } 
    else if (pitch > 30) {
        midi_volume = 0;
    } 
    else {
        midi_volume = abs(pitch - 30) * 2.116;
    }
    
    printFloat("%.1f ", printOutColor::printColorBlack, static_cast<float>(midi_note));
    printFloat("%.1f\n", printOutColor::printColorBlack, static_cast<float>(midi_volume));
}

void loop() {
    uint8_t event_data[FW_GET_EVENT_DATA_MAX] = {0};
    int last_event;
    
    last_event = 0;
    if (hasEvent()) {
        last_event = getEventData(event_data);
        
        // Handle button events
        if (last_event >= FWGUI_EVENT_GRAY_BUTTON && last_event <= FWGUI_EVENT_RED_BUTTON) {
            handleButtonEvent(last_event, event_data[0]);
        }
        // Handle sensor data
        else if (last_event == FWGUI_EVENT_GUI_SENSOR_DATA) {
            processAccelData(event_data);
        }
    }
}

int main() {
    // Initialize sensor settings
    setSensorSettings(1, 0, 10, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0);
    
    // Setup button menus
    setupButtonMenus();
    
    // Print startup message
    printInt("\nFreeWili MIDI Controller Started\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    printInt("Current Octave: ", printOutColor::printColorBlack, printOutDataType::printUInt32, currentOctave);
    printInt("\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    
    // Main loop
    while (!exitApp) {
        loop();
        waitms(1);
    }
    
    return 0;
}