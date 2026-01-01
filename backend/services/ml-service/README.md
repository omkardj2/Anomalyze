# ML & Detection Engine (`ml-service`)

## Overview
The **ML & Detection Engine** is a specialized worker service. While primarily an event consumer, it exposes a Management API for operational control, model versioning, and debugging. It combines deterministic rules (velocity, geo) with probabilistic ML models (Isolation Forest).

## Architecture
- **Consumer**: Kafka Group `ml-detection-group`
- **ML Runtime**: ONNX Runtime
- **State**: Redis (Sliding Windows)

## API Reference (Management Port)

### 1. Model Management

#### Get Model Info
Returns details about the currently loaded ML model.
- **Endpoint**: `GET /v1/model/info`

**Response**:
```json
{
  "version": "v2.4.0",
  "type": "isolation_forest",
  "loaded_at": "2025-12-20T10:00:00Z",
  "input_features": ["amount", "hour_of_day", "category_encoding"],
  "threshold": 0.75
}
```

#### Force Reload Model
Triggers a hot-reload of the model from Cloudflare R2 without restarting the service.
- **Endpoint**: `POST /v1/model/reload`
- **Auth**: Admin API Key

### 2. Rule Management

#### List Active Rules
View the deterministic rules currently applied to the stream.
- **Endpoint**: `GET /v1/rules`

**Response**:
```json
[
  {
    "id": "VELOCITY_HIGH",
    "description": "> 5 transactions in 1 minute",
    "enabled": true,
    "severity": "HIGH"
  },
  {
    "id": "GEO_IMPOSSIBLE",
    "description": "Speed > 800km/h between transactions",
    "enabled": true,
    "severity": "CRITICAL"
  }
]
```

#### Update Rule Configuration
Dynamically adjust thresholds.
- **Endpoint**: `PATCH /v1/rules/:ruleId`
- **Body**: `{ "threshold": 10, "window_seconds": 120 }`

### 3. Debugging & Testing

#### Dry-Run Prediction
Send a transaction payload to get a detection result *without* persisting it or triggering alerts. Useful for testing model behavior.
- **Endpoint**: `POST /v1/predict/dry-run`

**Request**:
```json
{
  "amount": 99999,
  "currency": "USD",
  "history": [...] // Optional simulated history
}
```

**Response**:
```json
{
  "is_anomaly": true,
  "score": 0.99,
  "triggered_rules": ["AMOUNT_SPIKE"],
  "explanation": "Amount is 500% above baseline."
}
```

### 4. Health

#### Service Health
- **Endpoint**: `GET /health`
- **Checks**: Kafka connectivity, Redis latency, ONNX runtime status.

## Event Processing Logic
1. **Deserialization**: Parse Kafka message.
2. **State Hydration**: Fetch user's last 10 transactions from Redis.
3. **Rule Execution**: Run Python/Pandas logic.
4. **Feature Engineering**: Transform raw data for ONNX.
5. **Inference**: Run `session.run()`.
6. **Aggregation**: Combine Rule + ML results.
7. **Publish**: Send to `anomalies` topic if severity > LOW.
