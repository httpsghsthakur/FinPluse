# Finpluse Streaming Architecture

## Overview

Real-time event processing for transaction enrichment, anomaly scoring, and alerts.

## Topology

```
transactions.raw
  -> Parse & Validate
  -> Enrich (user profile, features)
  -> Branch:
      -> Anomaly Scoring (<100ms)
      -> Forecast Update Trigger
      -> Category Spending Update
  -> transactions.scored
  -> Alert Generation
```

## Topics

| Topic | Purpose | Retention |
|-------|---------|-----------|
| transactions.raw | Incoming bank webhooks | 7 days |
| transactions.enriched | After feature engineering | 7 days |
| transactions.scored | After anomaly detection | 30 days |
| alerts.generated | Alert events | Forever |
| forecasts.updated | New forecast available | 30 days |
| user.events | Login, settings changes | 7 days |

## Local Development

Uses `EventBus` (asyncio queues) for local development.
Production uses Kafka with 12 partitions per topic, replication factor 3.

## Performance

- P99 latency target: <200ms
- Throughput: 10,000 tx/second per partition
- Backpressure: Queue-based with configurable max size
