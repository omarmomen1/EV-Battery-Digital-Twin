import paho.mqtt.client as mqtt
import time
import json
import random
import math
import pandas as pd
import numpy as np

"""
EV Battery Digital Twin: Telemetry Simulator
Phase 4: IoT Data Pipeline (CLOSED-LOOP UPDATE)

This script simulates a real-time EV driving cycle. 
UPDATED TO FOLLOW ENGINEERING AUDIT:
- Now features True Closed-Loop Control.
- Subscribes to BMS anomaly alerts.
- Dynamically alters coolant flow rate and throttles load upon thermal runaway detection.
"""

# MQTT Broker Configuration
BROKER_ADDRESS = "127.0.0.1"
PORT = 1883
TELEMETRY_TOPIC = "ev/battery/telemetry"
ALERT_TOPIC = "ev/battery/thermal_alerts"

# Global state for Closed-Loop Feedback
BMS_EMERGENCY_COOLING = False

def on_message(client, userdata, msg):
    """Callback for closed-loop BMS feedback"""
    global BMS_EMERGENCY_COOLING
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("alert_level") in ["WARNING", "CRITICAL"]:
            print(f"\n[BMS INTERVENTION] Received Alert: {payload.get('alert_type')}! Engaging Max Coolant Pump RPM and Limp Mode.")
            BMS_EMERGENCY_COOLING = True
    except Exception as e:
        pass

def simulate_drive_cycle():
    global BMS_EMERGENCY_COOLING
    
    # Initialize MQTT Client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "EVDigitalTwin_Simulator_ClosedLoop")
    client.on_message = on_message
    
    try:
        client.connect(BROKER_ADDRESS, PORT)
        client.subscribe(ALERT_TOPIC)
        client.loop_start() # Start background thread for listening to BMS
        print(f"Successfully connected to MQTT Broker at {BROKER_ADDRESS}:{PORT} (Closed-Loop Mode Active)")
    except ConnectionRefusedError:
        print(f"ERROR: Could not connect to MQTT Broker.")
        return

    print("Loading Phase 3 CFD Optimization Data into Digital Twin Memory...")
    try:
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(base_dir, "cfd_results", "CFD_Optimization_Report.csv")
        cfd_data = pd.read_csv(csv_path)
        copper_df = cfd_data[cfd_data["Material"] == "copper"].sort_values("Mass Flow (kg/s)")
        print("CFD Data Loaded Successfully! Ground-truth physics established.")
    except Exception as e:
        print(f"Error loading CFD Data: {e}")
        return

    # Helper function to get the authentic CFD Target Temp
    def get_cfd_target_temp(flow_rate):
        return np.interp(flow_rate, copper_df["Mass Flow (kg/s)"], copper_df["Max Temp (C)"])

    print("Starting High-Performance EV Drive Cycle Simulation...")
    
    ambient_temp = 25.0
    current_temp = 25.0
    
    t = 0
    while True:
        try:
            # CLOSED-LOOP LOGIC
            if BMS_EMERGENCY_COOLING:
                # Override throttle to 10% (Limp Mode)
                throttle = 10.0
                # Override pump to maximum capacity (0.4 kg/s)
                dynamic_flow_rate = 0.40
            else:
                # Normal driving simulation
                throttle = abs(math.sin(t / 15.0) * math.cos(t / 5.0)) * 100 
                # Pump flow rate responds dynamically to throttle (0.05 to 0.20 kg/s)
                dynamic_flow_rate = 0.05 + (throttle / 100.0) * 0.15
            
            # Retrieve the EXACT physics temperature limit from the CFD Data
            cfd_steady_state = get_cfd_target_temp(dynamic_flow_rate)
            
            # Modulate based on load (0 throttle = ambient)
            thermal_target = ambient_temp + (cfd_steady_state - ambient_temp) * (throttle / 100.0)
            
            # Thermal mass Newton's Law cooling
            current_temp += (thermal_target - current_temp) * 0.35
            
            # Sensor noise
            sensor_temp = current_temp + random.uniform(-0.15, 0.15)
            
            # Simulate an occasional hardware short-circuit / thermal runaway event
            if not BMS_EMERGENCY_COOLING and t > 0 and t % 30 == 0:
                print("\n[PHYSICS INJECTION] Simulating internal short-circuit (Thermal Runaway!)...")
                sensor_temp += 15.0  # Instant 15-degree spike!
                current_temp += 15.0
            
            # Package Telemetry as JSON payload
            payload = {
                "timestamp": int(time.time()),
                "throttle_percent": round(throttle, 2),
                "battery_temperature_c": round(sensor_temp, 2),
                "coolant_flow_rate_kg_s": round(dynamic_flow_rate, 3),
                "status": "EMERGENCY_COOLING" if BMS_EMERGENCY_COOLING else ("OVERHEATING" if sensor_temp > 60.0 else "NORMAL")
            }
            
            # Publish to MQTT Topic
            client.publish(TELEMETRY_TOPIC, json.dumps(payload))
            print(f"[Telemetry Stream] -> {payload}")
            
            t += 1
            time.sleep(1) # Stream at 1Hz
            
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            client.loop_stop()
            client.disconnect()
            break

if __name__ == "__main__":
    simulate_drive_cycle()
