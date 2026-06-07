import paho.mqtt.client as mqtt
import json
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

"""
EV Battery Digital Twin: MQTT to InfluxDB Bridge
Phase 4: IoT Data Pipeline & Active BMS Alerts
"""

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "ev/battery/telemetry"
TOPIC_ALERTS = "ev_battery/alerts/thermal"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "7TvvxhaER8EoLJJOUBgu7kfv49j4gIYjUUaT4OP3gHVPcEiX39x5FOeD-q_0Ay96ZEacBOZC9Uxe90BtDccUvQ=="
INFLUX_ORG = "digital_twin_org"
INFLUX_BUCKET = "ev_telemetry"

influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected to MQTT Broker with result code {reason_code}")
    client.subscribe(TOPIC_TELEMETRY)
    client.subscribe(TOPIC_ALERTS)
    print(f"Subscribed to topics: {TOPIC_TELEMETRY} and {TOPIC_ALERTS}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        
        if msg.topic == TOPIC_TELEMETRY:
            point = (
                Point("battery_metrics")
                .tag("module", "Module_A")
                .tag("status", payload.get("status", "NORMAL"))
                .field("temperature_c", float(payload.get("battery_temperature_c", 0)))
                .field("throttle_percent", float(payload.get("throttle_percent", 0)))
                .field("coolant_flow_kg_s", float(payload.get("coolant_flow_rate_kg_s", 0)))
            )
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            
        elif msg.topic == TOPIC_ALERTS:
            point = (
                Point("thermal_alerts")
                .tag("module", payload.get("module", "Module_A"))
                .field("dT_dt", float(payload.get("dT_dt", 0)))
                .field("status", payload.get("status", "NORMAL"))
            )
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
            print(f"[BMS ALERT SAVED] Status: {payload.get('status')} | dT/dt: {payload.get('dT_dt')}")
            
    except Exception as e:
        print(f"Error processing message on {msg.topic}: {e}")

if __name__ == "__main__":
    print("Starting Advanced MQTT -> InfluxDB Bridge...")
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\nStopping bridge.")
        mqtt_client.disconnect()
        influx_client.close()
