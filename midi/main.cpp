#include "fwwasm.h"
#include <cmath>    // For atan2, sqrt, fabs
#include <stdint.h> // For int types

// MIDI Note and Channel
#define MIDI_NOTE 60   // Middle C (C4)
#define MIDI_CHANNEL 0 // Channel 1 in MIDI

int8_t exitApp = 0;

const auto NUMBER_OF_LEDS = 7;

struct Color {
    uint8_t red;
    uint8_t green;
    uint8_t blue;

    constexpr Color(uint8_t red, uint8_t green, uint8_t blue) : red(red), green(green), blue(blue) {}
};

constexpr Color RED(255, 0, 0);
constexpr Color ORANGE(255, 127, 0);
constexpr Color YELLOW(255, 255, 0);
constexpr Color GREEN(0, 255, 0);
constexpr Color LIGHT_GREEN(0, 255, 191);
constexpr Color BLUE(0, 0, 255);
constexpr Color LIGHT_BLUE(0, 191, 255);
constexpr Color INDIGO(75, 0, 130);
constexpr Color VIOLET(238, 130, 238);
constexpr Color PINK(255, 192, 203);
constexpr Color GRAY(0x30, 0x30, 0x30);
constexpr Color WHITE(255, 255, 255);

struct PanelInfo {
    const uint8_t index;
    const FWGuiEventType event_type;
    const Color color;
    const char* text;
    const char* sub_fname;
};

constexpr std::array Panels{
    PanelInfo{1, FWGuiEventType::FWGUI_EVENT_GRAY_BUTTON, GRAY, "GRAY", "/midi/white.sub"},
    PanelInfo{2, FWGuiEventType::FWGUI_EVENT_YELLOW_BUTTON, YELLOW, "YELLOW", "/midi/yellow.sub"},
    PanelInfo{3, FWGuiEventType::FWGUI_EVENT_GREEN_BUTTON, GREEN, "GREEN", "/midi/green.sub"},
    PanelInfo{4, FWGuiEventType::FWGUI_EVENT_BLUE_BUTTON, BLUE, "BLUE", "/midi/blue.sub"},
    PanelInfo{5, FWGuiEventType::FWGUI_EVENT_RED_BUTTON, RED, "RED", "/midi/red.sub"},
};

constexpr std::array Buttons{
    FWGuiEventType::FWGUI_EVENT_GRAY_BUTTON,  FWGuiEventType::FWGUI_EVENT_YELLOW_BUTTON,
    FWGuiEventType::FWGUI_EVENT_GREEN_BUTTON, FWGuiEventType::FWGUI_EVENT_BLUE_BUTTON,
    FWGuiEventType::FWGUI_EVENT_RED_BUTTON,
};

auto setup_panels() -> void {
    // Setup the main panel that shows pip boy
    addPanel(0, 1, 0, 0, 0, 0, 0, 0, 1);
    addControlPictureFromFile(0, 0, 0, 0, "guy-closed.fwi", 1);
    showPanel(0);
    // Setup the rest of the panels
    for (auto& panel : Panels) {
        addPanel(panel.index, 1, 0, 0, 0, panel.color.red, panel.color.green, panel.color.blue, 1);
        addControlText(panel.index, 1, 10, 50, 2, 0, 0, 0, 0, panel.text);
    }
}

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

    }
    else if (roll >= -90.0 and roll <= -67.5){
        //setBoardLED(0,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=60.0;
    }
    else if(roll >= -67.5 and roll <= -45.0){
        //setBoardLED(1,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=62.0;
    }
    else if (roll >= -45.0 and roll <= -22.5){
        //setBoardLED(2,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=64.0;
    }
    else if (roll >= -22.5 and roll <= 0.0){
        //setBoardLED(3,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=65.0;
    }
    else if (roll >= 0.0 and roll <= 22.5){
        //setBoardLED(4,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=67.0;
    }
    else if (roll >= 22.5 and roll <= 45.0){
        //setBoardLED(5,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=69.0;
    }
    else if (roll >= 45.0 and roll <= 67.5){
        //setBoardLED(6,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=71.0;
    }
    else if (roll >= 67.5 and roll <= 90.0){
        //setBoardLED(7,0x30,0x30,0x30,300,LEDManagerLEDMode::ledpulsefade);
        midi_note=72.0;
    }
    if (roll > 90) 
    {
        roll = 90;
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
    setup_panels();
    setSensorSettings(1, 0, 10, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0);
    printInt("\nmain()\n", printOutColor::printColorBlack, printOutDataType::printUInt32, 0);
    while (!exitApp) {
        loop();
        waitms(1);  // Reduced wait time for more frequent updates
    }
    
    return 0;
}