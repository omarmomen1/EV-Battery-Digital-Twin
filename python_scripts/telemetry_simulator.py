import paho.mqtt.client as mqtt
import time
import json
import random
import math

"""
EV Battery Digital Twin: Telemetry Simulator
Phase 4: IoT Data Pipeline

This script simulates a real-time EV driving cycle. It calculates the dynamic 
heat generation based on throttle percentage and publishes the live battery 
temperatures to our local Mosquitto MQTT broker.
"""

# MQTT Broker Configuration
BROKER_ADDRESS = "127.0.0.1"
PORT = 1883
TOPIC = "ev/battery/telemetry"

import pandas as pd
import numpy as np

def simulate_drive_cycle():
    # Initialize MQTT Client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "EVDigitalTwin_Simulator")
    
    try:
        client.connect(BROKER_ADDRESS, PORT)
        print(f"Successfully connected to MQTT Broker at {BROKER_ADDRESS}:{PORT}")
    except ConnectionRefusedError:
        print(f"ERROR: Could not connect to MQTT Broker.")
        return

    print("Loading Phase 3 CFD Optimization Data into Digital Twin Memory...")
    try:
        cfd_data = pd.read_csv("D:/MEK/The Digital Twins EV Battery/phase3_cfd_model/CFD_Optimization_Report.csv")
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
            # Simulate aggressive driving (throttle spikes)
            throttle = abs(math.sin(t / 15.0) * math.cos(t / 5.0)) * 100 
            
            # Digital Twin Logic: The pump flow rate responds dynamically to throttle (0.05 to 0.20 kg/s)
            dynamic_flow_rate = 0.05 + (throttle / 100.0) * 0.15
            
            # Retrieve the EXACT physics temperature limit from the CFD Data!
            cfd_steady_state = get_cfd_target_temp(dynamic_flow_rate)
            
            # Modulate based on load (0 throttle = ambient)
            thermal_target = ambient_temp + (cfd_steady_state - ambient_temp) * (throttle / 100.0)
            
            # The thermal mass of the battery takes time to heat up/cool down (Newton's Law)
            current_temp += (thermal_target - current_temp) * 0.35
            
            # Add realistic sensor noise (Thermocouple variance)
            sensor_temp = current_temp + random.uniform(-0.15, 0.15)
            
            # Simulate an occasional hardware short-circuit / thermal runaway event
            if t > 0 and t % 15 == 0:
                sensor_temp += 15.0  # Instant 15-degree spike!
                current_temp += 15.0
            
            # Package Telemetry as JSON payload
            payload = {
                "timestamp": int(time.time()),
                "throttle_percent": round(throttle, 2),
                "battery_temperature_c": round(sensor_temp, 2),
                "coolant_flow_rate_kg_s": round(dynamic_flow_rate, 3),
                "status": "NORMAL" if sensor_temp < 60.0 else "OVERHEATING"
            }
            
            # Publish to MQTT Topic
            client.publish(TOPIC, json.dumps(payload))
            print(f"[Telemetry Stream] -> {payload}")
            
            t += 1
            time.sleep(1) # Stream at 1Hz (1 data point per second)
            
        except KeyboardInterrupt:
            print("\nSimulation stopped.")
            client.disconnect()
            break

if __name__ == "__main__":
    simulate_drive_cycle()
