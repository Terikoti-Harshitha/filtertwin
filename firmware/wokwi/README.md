# FilterTwin - Wokwi Virtual ESP32 Hardware Simulator

This directory provides a **zero-hardware virtual ESP32 simulator** for FilterTwin using [Wokwi](https://wokwi.com/).

It simulates a physical water purifier monitoring unit with:
- **ESP32 Micro-controller** running C++ firmware
- **0.96" I2C OLED Display (SSD1306)** showing real-time telemetry
- **3 Potentiometers** acting as analog sensor probes:
  - Potentiometer 1: Inlet Feed TDS (100 - 1000 ppm)
  - Potentiometer 2: Purified Product TDS (10 - 450 ppm)
  - Potentiometer 3: Permeate Flow Rate Turbine (0.0 - 3.0 LPM)
- **3 Diagnostic Status LEDs**:
  - Green (GPIO 18): Healthy Normal State
  - Yellow (GPIO 19): Progressive Wear Warning
  - Red (GPIO 23): Acute Abrupt Anomaly
- **Pushbutton (GPIO 4)**: Injects an instant simulated hydraulic blockage and membrane rupture!

---

## How to Run in Wokwi (Zero Prior Experience Needed!)

You do not need to install anything on your computer. You can run it entirely in your web browser:

### Step 1: Open Wokwi
Go to [https://wokwi.com/projects/new/esp32](https://wokwi.com/projects/new/esp32).

### Step 2: Paste the Code & Schematic
1. In the **`sketch.ino`** tab on Wokwi, replace the contents with the code from [`sketch.ino`](sketch.ino).
2. Click the **`diagram.json`** tab (or press the `+` button in Wokwi) and paste the contents from [`diagram.json`](diagram.json).
3. In the **`Library Manager`** tab on the left sidebar (or `libraries.txt`), add:
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`
   - `ArduinoJson`

### Step 3: Click the Green Play Button
- Click the **Play / Start Simulation** button.
- The virtual ESP32 will boot up, connect to Wokwi's virtual WiFi (`Wokwi-GUEST`), and render live metrics onto the virtual OLED screen.
- **Twist the potentiometers**: Rotate the knobs to change the inlet/outlet TDS and flow rate. Watch the OLED and status LEDs change live!
- **Press the red button**: Injects a sudden flow drop and TDS spike; watch the Red Anomaly LED light up immediately!

---

## Connecting Wokwi to your FilterTwin Backend

When running FilterTwin locally or deployed:
1. In `sketch.ino`, line 42:
   ```cpp
   const char* backendUrl = "http://host.wokwi.internal:8000/api/v1/telemetry/ingest";
   ```
2. If your FilterTwin backend is deployed to the cloud (e.g. `https://my-filtertwin.onrender.com`), change `backendUrl` to:
   ```cpp
   const char* backendUrl = "https://my-filtertwin.onrender.com/api/v1/telemetry/ingest";
   ```
3. The virtual ESP32 will stream live sensor telemetry straight into your FilterTwin PostgreSQL database and React dashboard!
