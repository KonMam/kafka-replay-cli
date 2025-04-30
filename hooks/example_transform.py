def transform(msg):
    if msg["value"]:
        msg["value"] = msg["value"].upper()
    msg["debug"] = b"replayed"
    return msg
