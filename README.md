# Kafka Development Environment

This repository contains a Docker Compose setup for a local Kafka development environment.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. Start the Kafka environment:
   ```bash
   docker-compose up -d
   ```

3. Verify the services are running:
   ```bash
   docker-compose ps
   ```

## Services

The following services will be available:

- **Zookeeper**: Running on port 2181
- **Kafka Broker**: Running on ports:
  - 9092 (for local machine access)
  - 29092 (for inter-container access)
- **Kafka UI**: Access the web interface at http://localhost:8080

## Using Kafka

### Connection Details

- Bootstrap Servers: `localhost:9092` (from your local machine)
- Bootstrap Servers: `kafka:29092` (from other containers)

### Kafka UI

The Kafka UI provides a web interface to:
- Monitor topics, partitions, and messages
- Create and delete topics
- View consumer groups
- Browse messages

Access it at: http://localhost:8080

## Stopping the Environment

To stop all services:
```bash
docker-compose down
```

To stop all services and delete all data:
```bash
docker-compose down -v
```

## Troubleshooting

If you encounter any issues:

1. Check service logs:
   ```bash
   docker-compose logs -f [service_name]
   ```

2. Ensure all ports (2181, 9092, 29092, 8080) are available on your machine

3. Restart the services:
   ```bash
   docker-compose restart
   ```

## Notes

- This is a development setup and should not be used in production
- The environment uses a single Kafka broker with replication factor 1
- Data is persisted between restarts unless you use `docker-compose down -v`