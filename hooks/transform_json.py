import json


def transform(msg):
    data = json.loads(msg["value"])
    data["transformed"] = True
    msg["value"] = json.dumps(data).encode()
    return msg
