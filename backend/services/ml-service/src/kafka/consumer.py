"""Anomalyze ML Service - Kafka Consumer for Transaction Processing"""
import json
import asyncio
from datetime import datetime
from confluent_kafka import Consumer, KafkaError, KafkaException
import structlog
from src.config import get_settings
from src.api.schemas import (
    TransactionEvent, TransactionMeta, TransactionData,
    TransactionEnrichment, AnalysisResult, Verdict, Severity, AnomalyEvent
)
from src.ml.model import get_model
from src.ml.features import get_feature_engineer

logger = structlog.get_logger()


class TransactionConsumer:
    """
    Kafka consumer for processing transactions from the 'transactions' topic.
    
    Flow:
    1. Consume transaction from Kafka
    2. Extract features using Redis
    3. Run ML inference
    4. Generate verdict with explanation
    5. Publish anomalies to 'anomalies' topic
    """
    
    def __init__(self, producer=None):
        self.settings = get_settings()
        self._consumer: Consumer | None = None
        self._producer = producer
        self._running = False
    
    def connect(self) -> bool:
        """Connect to Kafka broker."""
        try:
            config = {
                'bootstrap.servers': self.settings.kafka_bootstrap_servers,
                'group.id': self.settings.kafka_group_id,
                'auto.offset.reset': 'latest',
                'enable.auto.commit': True,
            }
            
            # Add security config if using SASL
            if self.settings.kafka_security_protocol != "PLAINTEXT":
                config.update({
                    'security.protocol': self.settings.kafka_security_protocol,
                    'sasl.mechanism': self.settings.kafka_sasl_mechanism,
                    'sasl.username': self.settings.kafka_sasl_username,
                    'sasl.password': self.settings.kafka_sasl_password,
                })
            
            self._consumer = Consumer(config)
            self._consumer.subscribe([self.settings.kafka_transactions_topic])
            
            logger.info(
                "kafka_consumer_connected",
                bootstrap_servers=self.settings.kafka_bootstrap_servers,
                topic=self.settings.kafka_transactions_topic
            )
            return True
        except Exception as e:
            logger.error("kafka_consumer_connection_failed", error=str(e))
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Kafka."""
        self._running = False
        if self._consumer:
            self._consumer.close()
            self._consumer = None
            logger.info("kafka_consumer_disconnected")
    
    async def start(self) -> None:
        """Start consuming messages in an async loop."""
        if not self._consumer:
            if not self.connect():
                return
        
        self._running = True
        logger.info("kafka_consumer_started")
        
        while self._running:
            try:
                # Poll for messages (non-blocking)
                msg = self._consumer.poll(timeout=1.0)
                
                if msg is None:
                    await asyncio.sleep(0.1)
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error("kafka_error", error=msg.error())
                        continue
                
                # Process the message
                await self._process_message(msg)
                
            except KafkaException as e:
                logger.error("kafka_exception", error=str(e))
                await asyncio.sleep(1)
            except Exception as e:
                logger.error("consumer_loop_error", error=str(e))
                await asyncio.sleep(1)
    
    async def _process_message(self, msg) -> None:
        """Process a single transaction message."""
        try:
            # Parse message
            raw_data = json.loads(msg.value().decode('utf-8'))
            
            # Handle both full event format and simple format
            if 'meta' in raw_data and 'data' in raw_data:
                event = TransactionEvent.model_validate(raw_data)
                user_id = event.meta.user_id
                tx_data = event.data
                timestamp = event.meta.timestamp
            else:
                # Simple format (from ingestion service)
                tx_data = TransactionData.model_validate(raw_data.get('data', raw_data))
                user_id = raw_data.get('user_id', 'unknown')
                timestamp = datetime.fromisoformat(
                    raw_data.get('timestamp', datetime.now().isoformat())
                )
            
            logger.debug(
                "processing_transaction",
                tx_id=tx_data.tx_id,
                user_id=user_id,
                amount=tx_data.amount
            )
            
            # Extract features
            feature_engineer = get_feature_engineer()
            features, enrichment_dict = feature_engineer.extract_features(
                user_id=user_id,
                amount=tx_data.amount,
                timestamp=timestamp,
                location=tx_data.location
            )
            
            # Run inference
            model = get_model()
            if not model.is_loaded:
                logger.warning("model_not_loaded_skipping")
                return
            
            ml_score, ml_prediction = model.predict(features)
            
            # Generate verdict
            verdict = self._generate_verdict(
                tx_data=tx_data,
                enrichment=enrichment_dict,
                ml_score=ml_score,
                ml_prediction=ml_prediction
            )
            
            logger.info(
                "transaction_analyzed",
                tx_id=tx_data.tx_id,
                ml_score=round(ml_score, 3),
                prediction=ml_prediction,
                severity=verdict.final_severity.value
            )
            
            # Publish if anomaly detected
            if ml_prediction == "ANOMALY" or ml_score >= self.settings.anomaly_threshold:
                await self._publish_anomaly(
                    user_id=user_id,
                    tx_data=tx_data,
                    enrichment_dict=enrichment_dict,
                    ml_score=ml_score,
                    ml_prediction=ml_prediction,
                    verdict=verdict,
                    timestamp=timestamp
                )
        
        except Exception as e:
            logger.error("message_processing_failed", error=str(e))
    
    def _generate_verdict(
        self,
        tx_data: TransactionData,
        enrichment: dict,
        ml_score: float,
        ml_prediction: str
    ) -> Verdict:
        """Generate human-readable verdict and severity."""
        
        rule_flags = []
        explanations = []
        
        # Check amount spike
        user_avg = enrichment.get('user_avg_spend', 100)
        if user_avg > 0 and tx_data.amount > user_avg * 5:
            rule_flags.append("AMOUNT_SPIKE")
            multiplier = round(tx_data.amount / user_avg, 1)
            explanations.append(
                f"Amount (${tx_data.amount:.2f}) is {multiplier}x higher than average (${user_avg:.2f})"
            )
        
        # Check velocity
        velocity = enrichment.get('tx_count_last_10min', 0)
        if velocity >= 5:
            rule_flags.append("VELOCITY_HIGH")
            explanations.append(f"High transaction velocity: {velocity} transactions in last 10 minutes")
        
        # Determine severity based on ML score and rules
        if ml_score >= 0.9 or len(rule_flags) >= 2:
            severity = Severity.CRITICAL
        elif ml_score >= 0.7 or len(rule_flags) >= 1:
            severity = Severity.HIGH
        elif ml_score >= 0.5:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW
        
        # Build explanation
        if explanations:
            explanation = ". ".join(explanations) + f". ML anomaly score: {ml_score:.2f}"
        else:
            explanation = f"ML model flagged transaction with anomaly score: {ml_score:.2f}"
        
        return Verdict(final_severity=severity, explanation=explanation)
    
    async def _publish_anomaly(
        self,
        user_id: str,
        tx_data: TransactionData,
        enrichment_dict: dict,
        ml_score: float,
        ml_prediction: str,
        verdict: Verdict,
        timestamp: datetime
    ) -> None:
        """Publish anomaly event to Kafka."""
        if not self._producer:
            logger.warning("no_producer_configured_skipping_publish")
            return
        
        anomaly_event = AnomalyEvent(
            meta=TransactionMeta(
                trace_id=f"ml-{tx_data.tx_id}",
                timestamp=timestamp,
                source="REALTIME_API",  # Default, could be enhanced
                user_id=user_id
            ),
            data=tx_data,
            enrichment=TransactionEnrichment(**enrichment_dict),
            analysis=AnalysisResult(
                rule_flags=[],  # Could add rule engine flags here
                ml_score=ml_score,
                ml_prediction=ml_prediction
            ),
            verdict=verdict
        )
        
        await self._producer.produce_anomaly(anomaly_event)
        logger.info("anomaly_published", tx_id=tx_data.tx_id, severity=verdict.final_severity.value)


# Global instance
_consumer: TransactionConsumer | None = None


def get_consumer() -> TransactionConsumer:
    """Get the global consumer instance."""
    global _consumer
    if _consumer is None:
        _consumer = TransactionConsumer()
    return _consumer
