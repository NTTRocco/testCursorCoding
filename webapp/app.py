from flask import Flask, render_template
from flask_socketio import SocketIO
from kafka import KafkaConsumer
import json
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Global variable to store the latest messages
latest_messages = []
MAX_MESSAGES = 100  # Maximum number of messages to keep in memory

def kafka_consumer():
    consumer = KafkaConsumer(
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='webapp-consumer-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    
    # Subscribe to all topics
    consumer.subscribe(pattern='.*')
    
    while True:
        try:
            for message in consumer:
                # Add new message to the list
                latest_messages.append({
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'value': message.value,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
                # Keep only the latest MAX_MESSAGES
                if len(latest_messages) > MAX_MESSAGES:
                    latest_messages.pop(0)
                
                # Emit the new message to all connected clients
                socketio.emit('new_message', {
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'value': message.value,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            print(f"Error in Kafka consumer: {e}")
            time.sleep(5)  # Wait before retrying

@app.route('/')
def index():
    return render_template('index.html', messages=latest_messages)

if __name__ == '__main__':
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Start the Flask application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 