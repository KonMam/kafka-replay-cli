# Local Kafka Setup (KRaft Mode, No ZooKeeper)

This folder contains the Docker setup for running Kafka locally using KRaft mode (ZooKeeper-free), intended for development and testing `kafka-replay-cli`.

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Ports `9092` available

---

## Running Kafka

From this `dev/` directory, start the Kafka container:

```bash
docker-compose up -d
```
