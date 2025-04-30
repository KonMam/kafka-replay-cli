from confluent_kafka import Producer

p = Producer({"bootstrap.servers": "localhost:9092"})


def acked(err, msg):
    if err:
        print("Failed to deliver message:", err)
    else:
        print(f"Produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


for i in range(5):
    p.produce(
        "test-topic", key=f"user-{i}", value=f'{{"event":"test-{i}"}}', callback=acked
    )

p.flush()
