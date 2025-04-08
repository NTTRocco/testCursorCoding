from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from typing import Dict, List
from kafka import KafkaProducer
from faker import Faker
import jsonschema
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Faker
fake = Faker()

# Kafka producer configuration
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def load_schema(schema_name: str) -> Dict:
    """Load a schema from the schemas directory."""
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas', f'{schema_name}.json')
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_available_schemas() -> List[str]:
    """Get list of available schema files."""
    schemas_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas')
    return [f.replace('.json', '') for f in os.listdir(schemas_dir) if f.endswith('.json')]

def generate_value(schema_type: str) -> any:
    """Generate a random value based on the schema type."""
    if schema_type == 'string':
        return fake.word()
    elif schema_type == 'integer':
        return fake.random_int()
    elif schema_type == 'number':
        return fake.random_number(digits=2)
    elif schema_type == 'boolean':
        return fake.boolean()
    elif schema_type == 'date-time':
        return datetime.now().isoformat()
    elif schema_type == 'uuid':
        return str(uuid.uuid4())
    elif schema_type == 'email':
        return fake.email()
    return None

def generate_event(schema: Dict) -> Dict:
    """Generate a single event based on the schema."""
    event = {}
    for field, field_type in schema.items():
        if isinstance(field_type, dict):
            event[field] = generate_event(field_type)
        elif isinstance(field_type, list):
            event[field] = [generate_event(field_type[0])]
        else:
            event[field] = generate_value(field_type)
    return event

@app.route('/api/schemas', methods=['GET'])
def list_schemas():
    """Get list of available schemas."""
    schemas = get_available_schemas()
    return jsonify({'schemas': schemas})

@app.route('/api/generate', methods=['POST'])
def generate_events():
    """Generate and publish events to Kafka."""
    data = request.get_json()
    
    # Validate request data
    required_fields = ['schema', 'topic', 'num_events']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    schema_name = data['schema']
    topic = data['topic']
    num_events = int(data['num_events'])
    
    # Load schema
    schema = load_schema(schema_name)
    if not schema:
        return jsonify({'error': f'Schema {schema_name} not found'}), 404
    
    # Generate and publish events
    generated_events = []
    for _ in range(num_events):
        event = generate_event(schema)
        producer.send(topic, value=event)
        generated_events.append(event)
    
    producer.flush()
    
    return jsonify({
        'message': f'Generated {num_events} events',
        'events': generated_events
    })

@app.route('/api/topics', methods=['GET'])
def list_topics():
    """Get list of available Kafka topics."""
    # This is a simplified version. In a real application, 
    # you would want to get this from Kafka's admin client
    return jsonify({'topics': ['my-topic']})  # Default topic for now

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003) 