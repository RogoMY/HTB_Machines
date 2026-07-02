from opcua import Client, ua
import time

client = Client("opc.tcp://127.0.0.1:4840/helix/")
client.connect()

mode          = client.get_node("ns=2;i=12")
test_override = client.get_node("ns=2;i=13")
cal_offset    = client.get_node("ns=2;i=6")
temp          = client.get_node("ns=2;i=4")
pressure      = client.get_node("ns=2;i=5")
trip          = client.get_node("ns=2;i=10")

mode.set_data_value(ua.DataValue(ua.Variant("MAINTENANCE", ua.VariantType.String)))
test_override.set_data_value(ua.DataValue(ua.Variant(True, ua.VariantType.Boolean)))
cal_offset.set_data_value(ua.DataValue(ua.Variant(11.0, ua.VariantType.Double)))
for i in range(60):
    t = temp.get_value()
    p = pressure.get_value()
    tr = trip.get_value()
    print(f"[{i:02d}] Temp={t:.2f}°C  Pressure={p:.2f} bar  TripActive={tr}")
    time.sleep(1)

client.disconnect()
