"""Anomalyze ML Service - Kafka Producer for Anomaly Events"""
import json
from confluent_kafka import Producer
import structlog
from src.config import get_settings
from src.api.schemas import AnomalyEvent

logger = structlog.get_logger()


class AnomalyProducer:
    """
    Kafka producer for publishing anomaly events to the 'anomalies' topic.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._producer: Producer | None = None
    
    def connect(self) -> bool:
        """Connect to Kafka broker."""
        try:
            config = {
                'bootstrap.servers': self.settings.kafka_bootstrap_servers,
                'client.id': f'{self.settings.service_name}-producer',
            }
            
            # Add security config if using SASL
            if self.settings.kafka_security_protocol != "PLAINTEXT":
                config.update({
                    'security.protocol': self.settings.kafka_security_protocol,
                    'sasl.mechanism': self.settings.kafka_sasl_mechanism,
                    'sasl.username': self.settings.kafka_sasl_username,
                    'sasl.password': self.settings.kafka_sasl_password,
                })
            
            self._producer = Producer(config)
            logger.info(
                "kafka_producer_connected",
                bootstrap_servers=self.settings.kafka_bootstrap_servers
            )
            return True
        except Exception as e:
            logger.error("kafka_producer_connection_failed", error=str(e))
            return False
    
    def disconnect(self) -> None:
        """Flush and disconnect."""
        if self._producer:
            self._producer.flush(timeout=5)
            self._producer = None
            logger.info("kafka_producer_disconnected")
    
    async def produce_anomaly(self, event: AnomalyEvent) -> bool:
        """
        Produce an anomaly event to the anomalies topic.
        
        Args:
            event: AnomalyEvent to publish
        
        Returns:
            bool: True if successfully queued
        """
        if not self._producer:
            logger.error("producer_not_connected")
            return False
        
        try:
            # Serialize event
            payload = event.model_dump_json()
            
            # Produce message
            self._producer.produce(
                topic=self.settings.kafka_anomalies_topic,
                key=event.data.tx_id.encode('utf-8'),
                value=payload.encode('utf-8'),
                callback=self._delivery_callback
            )
            
            # Trigger delivery (non-blocking)
            self._producer.poll(0)
            
            return True
        except Exception as e:
            logger.error("produce_failed", error=str(e))
            return False
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation."""
        if err:
            logger.error(
                "delivery_failed",
                topic=msg.topic(),
                error=str(err)
            )
        else:
            logger.debug(
                "message_delivered",
                topic=msg.topic(),
                partition=msg.partition(),
                offset=msg.offset()
            )
    
    def flush(self, timeout: float = 5.0) -> None:
        """Flush pending messages."""
        if self._producer:
            self._producer.flush(timeout=timeout)


# Global instance
_producer: AnomalyProducer | None = None


def get_producer() -> AnomalyProducer:
    """Get the global producer instance."""
    global _producer
    if _producer is None:
        _producer = AnomalyProducer()
    return _producer
