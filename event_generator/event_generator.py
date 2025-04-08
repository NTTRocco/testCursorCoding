import json
import random
from typing import Dict, Any
import typer
from kafka import KafkaProducer
from jsonschema import validate
from faker import Faker
from datetime import datetime
import uuid

app = typer.Typer()
fake = Faker()

def generate_value_for_type(field_type: str, field_format: str = None) -> Any:
    """Generate random values based on JSON schema types."""
    if field_type == "string":
        if field_format == "date-time":
            return datetime.now().isoformat()
        elif field_format == "uuid":
            return str(uuid.uuid4())
        elif field_format == "email":
            return fake.email()
        else:
            return fake.text(max_nb_chars=50)
    elif field_type == "integer":
        return random.randint(1, 1000)
    elif field_type == "number":
        return round(random.uniform(1, 1000), 2)
    elif field_type == "boolean":
        return random.choice([True, False])
    elif field_type == "array":
        # Generate a small array of strings by default
        return [fake.word() for _ in range(random.randint(1, 5))]
    elif field_type == "object":
        # Generate an empty object by default
        return {}
    else:
        return None

def generate_data_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively generate data based on JSON schema."""
    if "type" not in schema:
        return {}

    if schema["type"] == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = generate_data_from_schema(prop_schema)
        return result
    elif schema["type"] == "array":
        items_schema = schema.get("items", {})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 5)
        num_items = random.randint(min_items, max_items)
        return [generate_data_from_schema(items_schema) for _ in range(num_items)]
    else:
        return generate_value_for_type(schema["type"], schema.get("format"))

@app.command()
def generate_events(
    topic: str = typer.Argument(..., help="Kafka topic to publish events to"),
    schema_file: str = typer.Argument(..., help="Path to JSON schema file"),
    num_events: int = typer.Option(10, help="Number of events to generate"),
    bootstrap_servers: str = typer.Option("localhost:9092", help="Kafka bootstrap servers"),
):
    """Generate and publish random events to Kafka based on a JSON schema."""
    try:
        # Load schema
        with open(schema_file, 'r') as f:
            schema = json.load(f)

        # Create Kafka producer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        typer.echo(f"Generating {num_events} events for topic '{topic}'...")

        # Generate and send events
        for i in range(num_events):
            event_data = generate_data_from_schema(schema)
            
            # Validate generated data against schema
            validate(instance=event_data, schema=schema)
            
            # Send to Kafka
            future = producer.send(topic, event_data)
            future.get(timeout=10)  # Wait for confirmation
            
            typer.echo(f"Event {i+1}/{num_events} sent successfully")

        producer.flush()
        producer.close()
        
        typer.echo(typer.style(
            f"\nSuccessfully generated and sent {num_events} events to topic '{topic}'",
            fg=typer.colors.GREEN
        ))

    except Exception as e:
        typer.echo(typer.style(f"Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 