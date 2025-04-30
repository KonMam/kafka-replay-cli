import json
import time

from confluent_kafka import Producer

NUM_MESSAGES = 100_000
TOPIC = "load-test"

producer = Producer({"bootstrap.servers": "localhost:9092"})


def acked(err, msg):
    if err:
        print("Failed to deliver message:", err)
    elif msg.offset() % 10_000 == 0:
        print(f"Produced to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")


print(f"[+] Producing {NUM_MESSAGES:,} messages to topic '{TOPIC}'...")

start = time.time()

for i in range(NUM_MESSAGES):
    key = f"user-{i % 1000}"
    value = json.dumps({"event": f"test-{i}", "i": i})
    producer.produce(TOPIC, key=key.encode(), value=value.encode(), callback=acked)

    if i % 1000 == 0:
        producer.poll(0)

producer.flush()
end = time.time()

print(f"[✔] Done. Time taken: {end - start:.2f}s")
