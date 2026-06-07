import paho.mqtt.client as mqtt
import json
import time
from collections import deque

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "ev/battery/telemetry"
TOPIC_ALERTS = "ev_battery/alerts/thermal"

# Moving window to store (timestamp, temperature)
# We need to keep roughly 5 seconds of history. 
# Assuming telemetry comes in ~1 Hz, deque of length 10 is plenty safe.
history = deque(maxlen=10)

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"BMS Safety Layer Connected to MQTT Broker: {MQTT_BROKER}")
        client.subscribe(TOPIC_TELEMETRY)
    else:
        print(f"Failed to connect, return code {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        current_temp = payload.get("battery_temperature_c")
        current_time = time.time()
        
        if current_temp is None:
            return

        # Add current data point to history
        history.append((current_time, current_temp))
        
        # We need at least 2 points to calculate a derivative
        if len(history) < 2:
            return

        # Find the data point that is closest to 5 seconds ago
        target_time = current_time - 5.0
        
        # Start from the oldest point in our deque
        past_time, past_temp = history[0]
        
        # Calculate the actual time delta (dt) and temperature delta (dT)
        dt = current_time - past_time
        
        if dt <= 0:
            return

        # Only evaluate if we have a reasonably wide time window (e.g., > 2 seconds)
        # to avoid noise spikes from instantaneous derivatives
        if dt >= 2.0:
            dT_dt = (current_temp - past_temp) / dt
            
            # Evaluate BMS Logic Thresholds
            if dT_dt <= 0.5:
                status = "NORMAL"
            elif 0.5 < dT_dt <= 1.2:
                status = "WARNING_SOFT"
            else:
                status = "CRITICAL_ANOMALY"

            print(f"[BMS] dT/dt = {dT_dt:.3f} °C/s -> Status: {status}")

            # Construct and publish alert packet
            alert_payload = {
                "timestamp": current_time,
                "module": payload.get("module", "Module_A"),
                "dT_dt": round(dT_dt, 3),
                "status": status
            }
            
            client.publish(TOPIC_ALERTS, json.dumps(alert_payload))
            
    except Exception as e:
        print(f"Error processing telemetry: {e}")

def main():
    print("Initializing BMS Thermal Anomaly Detector...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "bms_anomaly_detector")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nDisconnecting from broker...")
        client.disconnect()
        print("BMS Safety Layer Shutdown.")

if __name__ == "__main__":
    main()
