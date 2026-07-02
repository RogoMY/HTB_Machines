from opcua import Client

client = Client("opc.tcp://127.0.0.1:4840/helix/")
client.connect()

def browse(node, indent=0):
    try:
        name = node.get_browse_name()
    except Exception as e:
        name = f"?({e})"
    print("  " * indent + f"{name} -> {node.nodeid}")
    try:
        val = node.get_value()
        print("  " * indent + f"  value: {val}")
    except Exception:
        pass
    try:
        for child in node.get_children():
            browse(child, indent + 1)
    except Exception as e:
        print("  " * indent + f"  (no children / error: {e})")

custom_node = client.get_node("ns=2;i=1")
browse(custom_node)

client.disconnect()
