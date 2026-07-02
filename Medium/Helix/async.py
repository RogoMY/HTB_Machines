from opcua import Client

client = Client("opc.tcp://127.0.0.1:4840/helix/")
client.connect()

root = client.get_objects_node()
print(root.get_children())
