from influxdb_client import InfluxDBClient
import json

client = InfluxDBClient(url='http://localhost:8086', token='7TvvxhaER8EoLJJOUBgu7kfv49j4gIYjUUaT4OP3gHVPcEiX39x5FOeD-q_0Ay96ZEacBOZC9Uxe90BtDccUvQ==', org='digital_twin_org')
query_api = client.query_api()

query = 'from(bucket:"ev_telemetry") |> range(start:-10m) |> filter(fn: (r) => r["_measurement"] == "thermal_alerts")'

tables = query_api.query(query)
if not tables:
    print("NO DATA FOUND IN INFLUXDB FOR MEASUREMENT: thermal_alerts")
else:
    for table in tables:
        for record in table.records:
            print(record.values)
