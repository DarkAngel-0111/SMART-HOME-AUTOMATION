#!/usr/bin/env python3
"""
Test script for Smart Home Gateway & Liquid Crystal Glass UI API.
"""
import time
import json
import urllib.request
import urllib.error
import subprocess
import sys

def test_endpoints():
    base_url = "http://127.0.0.1:5000"
    
    # Check if server is running; if not, spin up a background instance
    server_proc = None
    try:
        urllib.request.urlopen(f"{base_url}/api/status", timeout=1.0)
    except Exception:
        print("[INFO] Starting test gateway server on port 5000...")
        server_proc = subprocess.Popen([sys.executable, "app.py"])
        # Wait up to 5 seconds for server to start
        for _ in range(15):
            time.sleep(0.3)
            try:
                with urllib.request.urlopen(f"{base_url}/api/status", timeout=1.0) as r:
                    if r.status == 200:
                        break
            except Exception:
                pass

    try:
        print("1. Testing GET / (Liquid Crystal Glass HTML UI)...")
        with urllib.request.urlopen(f"{base_url}/") as res:
            assert res.status == 200
            html = res.read().decode('utf-8')
            assert "SmartHome Pro" in html
            assert "MQ-6 Gas" in html
            assert "Indoor Climate" in html
            assert "screen-home" in html
            assert "screen-lights" in html
            assert "screen-sensors" in html
            assert "screen-settings" in html
            assert "modal-connect" in html
            assert "nav-btn-home" in html
            assert "nav-btn-lights" in html
            assert "nav-btn-sensors" in html
            assert "nav-btn-settings" in html
            print("   [PASS] HTML UI served with all 5 Liquid Crystal Glass screens.")

        print("2. Testing GET /static/style.css (Liquid Glass Stylesheet)...")
        with urllib.request.urlopen(f"{base_url}/static/style.css") as res:
            assert res.status == 200
            css = res.read().decode('utf-8')
            assert ".glass-card" in css
            assert "--primary-emerald" in css
            assert "--accent-cyan" in css
            print("   [PASS] CSS served successfully with glassmorphism styles.")

        print("3. Testing GET /static/app.js (Client SPA Logic)...")
        with urllib.request.urlopen(f"{base_url}/static/app.js") as res:
            assert res.status == 200
            js = res.read().decode('utf-8')
            assert "showScreen" in js
            assert "updateUI" in js
            assert "updateSparklines" in js
            assert "testConnection" in js
            print("   [PASS] Client JS served successfully with screen switcher and sparklines.")

        print("4. Testing GET /api/status (Live Telemetry)...")
        with urllib.request.urlopen(f"{base_url}/api/status") as res:
            assert res.status == 200
            data = json.loads(res.read().decode('utf-8'))
            assert "temp" in data
            assert "gas" in data
            assert "dist" in data
            assert "door" in data
            print(f"   [PASS] Telemetry: Temp={data['temp']}°C, Gas={data['gas']}, Light={data['light']}, Door={data['door']}°")

        print("5. Testing POST /api/light/toggle...")
        req = urllib.request.Request(f"{base_url}/api/light/toggle", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["status"] == "ok"
            print("   [PASS] Light toggle successful.")

        print("5b. Testing 4-light endpoints (/api/light/1..4/on, /api/lights/all/off)...")
        for lid in [1, 2, 3, 4]:
            req = urllib.request.Request(f"{base_url}/api/light/{lid}/on", data=b"", method="POST")
            with urllib.request.urlopen(req) as res:
                assert res.status == 200
                resp = json.loads(res.read().decode('utf-8'))
                assert resp["status"] == "ok"
                assert resp[f"light{lid}"] == 1
        print("   [PASS] All 4 lights turned ON individually.")

        req = urllib.request.Request(f"{base_url}/api/lights/all/off", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["status"] == "ok"
            for lid in [1, 2, 3, 4]:
                assert resp[f"light{lid}"] == 0
        print("   [PASS] Master All Lights turned OFF.")

        print("6. Testing POST /api/door/open...")
        req = urllib.request.Request(f"{base_url}/api/door/open", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["status"] == "ok"
            print("   [PASS] Door open (90°) successful.")

        print("7. Testing POST /api/door/close...")
        req = urllib.request.Request(f"{base_url}/api/door/close", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["status"] == "ok"
            print("   [PASS] Door close (0°) successful.")

        print("8. Testing POST /api/simulate/gas...")
        req = urllib.request.Request(f"{base_url}/api/simulate/gas", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["simulated"] == "gas_alert"
            print("   [PASS] Simulated gas leak successful.")

        # Check status again to verify alarm activated
        time.sleep(1.2)
        with urllib.request.urlopen(f"{base_url}/api/status") as res:
            data = json.loads(res.read().decode('utf-8'))
            assert data["gas"] >= 400
            assert data["alarm"] == 1
            print(f"   [PASS] Alarm state verified: Gas={data['gas']}, AlarmActive={data['alarm']}")

        print("9. Testing POST /api/alarm/silence...")
        req = urllib.request.Request(f"{base_url}/api/alarm/silence", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            print("   [PASS] Alarm silenced.")

        print("10. Testing POST /api/mode/auto & manual...")
        req = urllib.request.Request(f"{base_url}/api/mode/auto", data=b"", method="POST")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp = json.loads(res.read().decode('utf-8'))
            assert resp["mode"] == "AUTO"
            print("   [PASS] Auto Mode set successfully.")

        print("\nALL 10 API & UI TESTS PASSED SUCCESSFULLY!")

    finally:
        if server_proc:
            print("[INFO] Shutting down test gateway server...")
            server_proc.terminate()
            server_proc.wait()

if __name__ == "__main__":
    test_endpoints()
