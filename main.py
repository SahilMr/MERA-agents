# Main application entry point
import os
import json
import logging
import requests
from confluent_kafka import Consumer, KafkaError, KafkaException
from schema.kafka_schema import RTIKafkaMessage
from pydantic import ValidationError
from constants.app_constants import KafkaConfig, MeeraEndpoints

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



def process_message(msg_value: str):
    """Process incoming Kafka message and call external API."""
    try:
        # Parse message as JSON 
        data = json.loads(msg_value)
        
        # Validate against Pydantic schema
        validated_msg = RTIKafkaMessage(**data)
        logger.info(f"Successfully validated message for RTI ID: {validated_msg.rti_id}")
        
        # Call fetch_rti_query API
        params = {"rti_query_id": validated_msg.rti_id}
        logger.info(f"Calling API: {MeeraEndpoints.FETCH_RTI_REQUEST_URL} with params: {params}")
        
        response = requests.get(MeeraEndpoints.FETCH_RTI_REQUEST_URL, params=params)
        response.raise_for_status() # Raise HTTP errors if any
        
        # Process API response
        api_data = response.json()
        logger.info(f"Successfully fetched RTI query details: {api_data}")
        
        query_text = api_data.get("query_text", "")
        applicant_email = api_data.get("applicant_email")
        
        if not query_text:
            logger.error("No query_text found in the API response.")
            return

        # Initialize and run the LangGraph Workflow
        logger.info("Initializing RTI Agent Workflow...")
        from workflow.rti_agent import RTIAgentWorkflow
        workflow_app = RTIAgentWorkflow().graph
        
        initial_state = {
            "rti_id": validated_msg.rti_id,
            "query": query_text,
            "applicant_email": applicant_email
        }
        
        logger.info("Invoking LangGraph workflow...")
        final_state = workflow_app.invoke(initial_state)
        
        logger.info(f"Workflow completed for RTI ID: {validated_msg.rti_id}. Final status: {final_state.get('final_status')}")
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON message: {msg_value}. Error: {e}")
    except ValidationError as e:
        logger.error(f"Message failed schema validation: {msg_value}. Validation errors: {e.errors()}")
    except requests.RequestException as e:
        logger.error(f"API request failed. Error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)


def consume_messages():
    """Consume messages from Kafka topic."""
    conf = {
        'bootstrap.servers': KafkaConfig.BOOTSTRAP_SERVERS,
        'group.id': KafkaConfig.GROUP_ID,
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)
    
    try:
        consumer.subscribe([KafkaConfig.TOPIC])
        logger.info(f"Subscribed to topic: {KafkaConfig.TOPIC}")
        
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    logger.debug(f"{msg.topic()} [{msg.partition()}] reached end at offset {msg.offset()}")
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                msg_value = msg.value().decode('utf-8')
                logger.info(f"Received message: {msg_value}")
                process_message(msg_value)
                
    except KeyboardInterrupt:
        logger.info("Consumer stopped by user.")
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}", exc_info=True)
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()
        logger.info("Consumer closed.")

if __name__ == "__main__":
    logger.info("Starting RTI Agent Kafka Consumer...")
    consume_messages()
