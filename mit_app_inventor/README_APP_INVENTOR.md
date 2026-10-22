# 📱 MIT App Inventor - IoT Device Controller Guide

This folder contains the complete MIT App Inventor mobile application project to control your Arduino Uno IoT devices.

---

## 🚀 Quick Start: Import the Project (1 Click)

1. Open your browser and go to **[MIT App Inventor](http://ai2.appinventor.mit.edu)**.
2. Log in with your Google account.
3. In the top navigation menu, click **Projects** &rarr; **Import project (.aia) from my computer**.
4. Choose the file:
   ```
   mit_app_inventor/IoT_Controller.aia
   ```
5. Click **OK**. The project `IoT_Controller` will open immediately with all UI screens and Blockly logic pre-configured!

---

## 📲 How to Run on Your Android Phone

### Option A: Live Testing with MIT AI2 Companion (Recommended)
1. Install **MIT AI2 Companion** from the Google Play Store on your Android phone.
2. Connect your phone to the **same Wi-Fi network** as your laptop.
3. In MIT App Inventor on your laptop, click **Connect** &rarr; **AI Companion**.
4. Open the Companion app on your phone, tap **Scan QR code**, and scan the QR code displayed on your laptop screen.
5. The app will launch instantly on your phone!

### Option B: Build Standalone APK
1. In MIT App Inventor, click **Build** &rarr; **Android App (.apk)**.
2. Wait for the compilation progress bar to complete (1-2 minutes).
3. Scan the generated QR code with your phone camera or download the `.apk` file directly to install it.

---

## ⚙️ How to Connect to Your Laptop

1. Ensure the Python gateway is running on your laptop:
   ```bash
   python3 app.py
   ```
2. Note your laptop's IP address printed in the terminal (e.g., `http://192.168.1.15:5000`).
3. In the mobile app:
   - Type `http://192.168.1.15:5000` into the **Gateway Server URL** text box.
   - Tap **Save**.
4. The connection indicator will turn green:
   - `📡 MQTT Broker: Connected`
   - `⚡ Arduino Uno: Connected`
5. Tap **ON** or **OFF** on any of the 4 devices to control them in real time!

---

## 🧩 Designer Component Structure

If you prefer to build the UI manually or inspect the components, here is the component hierarchy:

| Component Type | Component Name | Properties / Settings | Purpose |
|---|---|---|---|
| **Form** | `Screen1` | Title: "IoT Device Controller", Background: `#0F172A`, Scrollable: True | Main Screen |
| **Label** | `Label_Title` | Text: "⚡ IoT Device Controller", FontBold: True, Color: Sky Blue | App Title |
| **VerticalArrangement** | `Card_Server` | Background: `#1E293B`, Width: Fill parent | Server IP Box |
| &nbsp;&nbsp;&boxur; **TextBox** | `TextBox_ServerIP` | Hint: "http://192.168.1.15:5000", Width: Fill parent | Enter Laptop IP |
| &nbsp;&nbsp;&boxur; **Button** | `Button_SaveIP` | Text: "Save", Background: Blue | Saves URL to TinyDB |
| **VerticalArrangement** | `Card_Status` | Background: `#1E293B`, Width: Fill parent | Status indicators |
| &nbsp;&nbsp;&boxur; **Label** | `Label_MqttStatus` | Text: "📡 MQTT Broker: Checking..." | Shows MQTT state |
| &nbsp;&nbsp;&boxur; **Label** | `Label_ArduinoStatus` | Text: "⚡ Arduino Uno: Checking..." | Shows Arduino state |
| **VerticalArrangement** | `Card_Dev1` | Device 1 Card (Living Room Light - D2) | Control Device 1 |
| &nbsp;&nbsp;&boxur; **Label** | `Label_Dev1_State` | Text: "OFF", FontBold: True | Shows ON / OFF |
| &nbsp;&nbsp;&boxur; **Button** | `Button_Dev1_On` | Text: "ON", Background: Green (`#10B981`) | Turns D2 ON |
| &nbsp;&nbsp;&boxur; **Button** | `Button_Dev1_Off` | Text: "OFF", Background: Red (`#EF4444`) | Turns D2 OFF |
| **VerticalArrangement** | `Card_Dev2` | Device 2 Card (Ceiling Fan - D3) | Control Device 2 |
| **VerticalArrangement** | `Card_Dev3` | Device 3 Card (Air Cooler / AC - D4) | Control Device 3 |
| **VerticalArrangement** | `Card_Dev4` | Device 4 Card (Power Socket - D5) | Control Device 4 |
| **HorizontalArrangement** | `Row_Master` | Width: Fill parent | Batch Controls |
| &nbsp;&nbsp;&boxur; **Button** | `Button_AllOn` | Text: "⚡ ALL ON", Background: Dark Green | Turns all 4 ON |
| &nbsp;&nbsp;&boxur; **Button** | `Button_AllOff` | Text: "⭕ ALL OFF", Background: Dark Red | Turns all 4 OFF |
| &nbsp;&nbsp;&boxur; **Button** | `Button_Refresh` | Text: "🔄 SYNC", Background: Slate Gray | Force refresh |
| **Web** | `Web1` | Non-visible | Makes HTTP GET & POST calls |
| **Clock** | `Clock1` | TimerInterval: 2000 ms, TimerEnabled: True | Auto-polls `/api/status` |
| **TinyDB** | `TinyDB1` | Non-visible | Stores server IP permanently |
| **Notifier** | `Notifier1` | Non-visible | Pops up alert messages |

---

## 🧠 Blockly Logic Explanation

### 1. Variables and Helper Procedures
```
initialize global server_url to "http://192.168.1.100:5000"

to sendCommand(endpoint):
    set Web1.Url to join(get global server_url, get endpoint)
    call Web1.PostText(text = "")

to requestStatus:
    set Web1.Url to join(get global server_url, "/api/status")
    call Web1.Get
```

### 2. Screen Startup & Persistence
```
when Screen1.Initialize:
    set global server_url to call TinyDB1.GetValue(tag="server_url", valueIfTagNotThere="http://192.168.1.100:5000")
    set TextBox_ServerIP.Text to get global server_url
    call requestStatus

when Button_SaveIP.Click:
    set global server_url to TextBox_ServerIP.Text
    call TinyDB1.StoreValue(tag="server_url", valueToStore=get global server_url)
    call Notifier1.ShowAlert("Server URL Saved!")
    call requestStatus
```

### 3. Device Controls
```
when Button_Dev1_On.Click:
    call sendCommand("/api/device/1/on")

when Button_Dev1_Off.Click:
    call sendCommand("/api/device/1/off")

when Button_Dev2_On.Click:
    call sendCommand("/api/device/2/on")

when Button_Dev2_Off.Click:
    call sendCommand("/api/device/2/off")

when Button_Dev3_On.Click:
    call sendCommand("/api/device/3/on")

when Button_Dev3_Off.Click:
    call sendCommand("/api/device/3/off")

when Button_Dev4_On.Click:
    call sendCommand("/api/device/4/on")

when Button_Dev4_Off.Click:
    call sendCommand("/api/device/4/off")

when Button_AllOn.Click:
    call sendCommand("/api/devices/all/on")

when Button_AllOff.Click:
    call sendCommand("/api/devices/all/off")
```

### 4. Live Status Sync
```
when Clock1.Timer:
    call requestStatus

when Button_Refresh.Click:
    call requestStatus

when Web1.GotText(url, responseCode, responseType, responseContent):
    if responseCode == 200 then:
        set local data to call Web1.JsonTextDecode(responseContent)
        set Label_MqttStatus.Text to join("📡 MQTT Broker: ", lookup in pairs(key="mqtt", list=data))
        set Label_ArduinoStatus.Text to join("⚡ Arduino Uno: ", lookup in pairs(key="arduino", list=data))
```
