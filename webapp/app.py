from flask import Flask, render_template
from flask_socketio import SocketIO
from kafka import KafkaConsumer, TopicPartition
import json
import threading
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# Global variable to store the latest messages
latest_messages = []
MAX_MESSAGES = 100  # Maximum number of messages to keep in memory

def safe_decode(bytes_data):
    try:
        # First try to decode as UTF-8
        return json.loads(bytes_data.decode('utf-8'))
    except UnicodeDecodeError:
        # If UTF-8 fails, try to decode as bytes and convert to string representation
        try:
            # Convert bytes to a string representation that can be displayed
            return {"raw_data": str(bytes_data)}
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            return None
    except json.JSONDecodeError:
        # If JSON parsing fails, return the raw string
        try:
            return {"raw_data": bytes_data.decode('utf-8', errors='replace')}
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            return None
    except Exception as e:
        logger.error(f"Unexpected error in safe_decode: {e}")
        return None

def kafka_consumer():
    logger.info("Starting Kafka consumer...")
    consumer = KafkaConsumer(
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='webapp-consumer-group',
        consumer_timeout_ms=1000,  # 1 second timeout
        value_deserializer=safe_decode
    )
    
    # Get list of all topics
    topics = consumer.topics()
    # Filter out internal topics (those starting with __)
    user_topics = [topic for topic in topics if not topic.startswith('__')]
    logger.info(f"Subscribing to topics: {user_topics}")
    
    # Subscribe to user topics
    consumer.subscribe(user_topics)
    
    while True:
        try:
            # Poll for messages
            message_batch = consumer.poll(timeout_ms=1000)
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    logger.info(f"Raw message from topic {message.topic}: {message.value}")
                    if message.value is not None:  # Only process messages that were successfully decoded
                        logger.info(f"Processed message from topic: {message.topic}, value: {message.value}")
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
                        logger.debug(f"Emitting new_message event with data: {message.value}")
                        socketio.emit('new_message', {
                            'topic': message.topic,
                            'partition': message.partition,
                            'offset': message.offset,
                            'value': message.value,
                            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.debug("Event emitted successfully")
                    else:
                        logger.warning(f"Message from topic {message.topic} was not decoded properly")
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}", exc_info=True)
            time.sleep(1)  # Wait before retrying

@app.route('/')
def index():
    return render_template('index.html', messages=latest_messages)

@app.route('/generator')
def generator():
    return render_template('event-generator.html')

if __name__ == '__main__':
    # Start Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=kafka_consumer, daemon=True)
    consumer_thread.start()
    
    # Start the Flask application
    socketio.run(app, debug=True, host='0.0.0.0', port=5002) 