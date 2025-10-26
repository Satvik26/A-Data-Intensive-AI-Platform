# ADR 001: Architecture Overview

**Status**: Accepted  
**Date**: 2025-10-26  
**Deciders**: Atlas Team  
**Tags**: architecture, ddia, patterns

## Context

We need to build a production-grade platform that demonstrates all major concepts from "Designing Data-Intensive Applications" (DDIA) in a practical, runnable system. The platform must be:

1. **Reliable**: Handle failures gracefully with proper retry logic, circuit breakers, and idempotency
2. **Scalable**: Support horizontal scaling through partitioning and replication
3. **Maintainable**: Clear code structure, comprehensive tests, and observability

## Decision

We will implement a **layered architecture** with clear boundaries:

### Layer Structure

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (FastAPI Routers, Schemas)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Application Layer               │
│    (Services, Use Cases)                │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Domain Layer                    │
│    (Entities, Value Objects)            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Infrastructure Layer            │
│    (Repositories, Adapters)             │
└─────────────────────────────────────────┘
```

### Technology Stack

**Backend Framework**: FastAPI
- Async support for high concurrency
- Automatic OpenAPI documentation
- Built-in dependency injection
- Type-safe with Pydantic v2

**Data Stores**:
- **PostgreSQL**: Primary relational database (ACID guarantees)
- **Redis**: Caching and session store (low-latency reads)
- **Kafka**: Event streaming (reliable message delivery)
- **MinIO**: Object storage (S3-compatible)

**Observability**:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **OpenTelemetry**: Distributed tracing
- **Structlog**: Structured logging

### DDIA Patterns Implemented

1. **Reliability** (Chapter 1)
   - Idempotency keys for write operations
   - Retry with exponential backoff + jitter
   - Circuit breakers for external services
   - Graceful degradation

2. **Data Models** (Chapter 2-3)
   - Relational model (PostgreSQL)
   - Document model (JSON in PostgreSQL)
   - Graph model (future: relationships)

3. **Replication** (Chapter 5)
   - Leader-follower replication (PostgreSQL streaming)
   - Read replicas for scaling reads

4. **Partitioning** (Chapter 6)
   - Kafka topic partitioning
   - Database sharding strategy (future)

5. **Transactions** (Chapter 7)
   - ACID transactions in PostgreSQL
   - Outbox pattern for reliable event publishing

6. **Distributed Systems** (Chapter 8-9)
   - Consensus through Kafka/Zookeeper
   - Linearizability guarantees where needed

7. **Batch Processing** (Chapter 10)
   - Background workers for async tasks
   - Batch job framework (future)

8. **Stream Processing** (Chapter 11)
   - Kafka consumers for event processing
   - Exactly-once semantics

## Consequences

### Positive

✅ **Clear Boundaries**: Each layer has well-defined responsibilities  
✅ **Testability**: Easy to mock dependencies and test in isolation  
✅ **Flexibility**: Can swap implementations without affecting other layers  
✅ **DDIA Alignment**: Direct mapping to book concepts  
✅ **Production Ready**: Includes all operational concerns

### Negative

⚠️ **Complexity**: More layers mean more files and abstractions  
⚠️ **Learning Curve**: Developers need to understand the architecture  
⚠️ **Boilerplate**: Some repetition across layers

### Mitigations

- Comprehensive documentation and examples
- Code generators for common patterns
- Clear naming conventions
- Extensive inline comments

## Alternatives Considered

### 1. Monolithic Architecture
**Rejected**: Doesn't demonstrate distributed systems concepts from DDIA

### 2. Microservices Architecture
**Rejected**: Too complex for initial implementation, harder to demonstrate concepts in isolation

### 3. Hexagonal Architecture
**Considered**: Similar benefits but less familiar to most developers

## References

- "Designing Data-Intensive Applications" by Martin Kleppmann
- Clean Architecture by Robert C. Martin
- Domain-Driven Design by Eric Evans
- FastAPI Documentation: https://fastapi.tiangolo.com/

## Notes

This architecture will evolve as we implement more DDIA concepts. Future ADRs will document specific pattern implementations.

