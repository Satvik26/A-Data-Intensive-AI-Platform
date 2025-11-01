#!/bin/bash

# Chaos Testing Script
# Tests system resilience by simulating failures

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║           ATLAS CHAOS TESTING SUITE                        ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"

# Test 1: Database Failure
test_database_failure() {
    echo -e "\n${YELLOW}[TEST 1] Database Failure Scenario${NC}"
    echo "Stopping PostgreSQL..."
    docker-compose stop postgres
    
    echo "Waiting 5 seconds..."
    sleep 5
    
    echo "Testing API behavior..."
    if curl -s http://localhost:8000/health | grep -q "error"; then
        echo -e "${GREEN}✓ API gracefully handles database failure${NC}"
    else
        echo -e "${RED}✗ API did not handle database failure${NC}"
    fi
    
    echo "Restarting PostgreSQL..."
    docker-compose start postgres
    sleep 10
    
    echo "Verifying recovery..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ API recovered after database restart${NC}"
    else
        echo -e "${RED}✗ API did not recover${NC}"
    fi
}

# Test 2: Redis Failure
test_redis_failure() {
    echo -e "\n${YELLOW}[TEST 2] Redis Failure Scenario${NC}"
    echo "Stopping Redis..."
    docker-compose stop redis
    
    echo "Waiting 5 seconds..."
    sleep 5
    
    echo "Testing API behavior..."
    if curl -s http://localhost:8000/health | grep -q "error"; then
        echo -e "${GREEN}✓ API gracefully handles Redis failure${NC}"
    else
        echo -e "${RED}✗ API did not handle Redis failure${NC}"
    fi
    
    echo "Restarting Redis..."
    docker-compose start redis
    sleep 5
    
    echo "Verifying recovery..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ API recovered after Redis restart${NC}"
    else
        echo -e "${RED}✗ API did not recover${NC}"
    fi
}

# Test 3: Kafka Failure
test_kafka_failure() {
    echo -e "\n${YELLOW}[TEST 3] Kafka Failure Scenario${NC}"
    echo "Stopping Kafka..."
    docker-compose stop kafka
    
    echo "Waiting 5 seconds..."
    sleep 5
    
    echo "Testing API behavior..."
    if curl -s http://localhost:8000/health | grep -q "error"; then
        echo -e "${GREEN}✓ API gracefully handles Kafka failure${NC}"
    else
        echo -e "${RED}✗ API did not handle Kafka failure${NC}"
    fi
    
    echo "Restarting Kafka..."
    docker-compose start kafka
    sleep 10
    
    echo "Verifying recovery..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ API recovered after Kafka restart${NC}"
    else
        echo -e "${RED}✗ API did not recover${NC}"
    fi
}

# Test 4: Network Latency
test_network_latency() {
    echo -e "\n${YELLOW}[TEST 4] Network Latency Scenario${NC}"
    echo "Adding 500ms latency to API container..."
    docker-compose exec -T api tc qdisc add dev eth0 root netem delay 500ms || true
    
    echo "Testing API with latency..."
    START=$(date +%s%N)
    curl -s http://localhost:8000/health > /dev/null
    END=$(date +%s%N)
    DURATION=$((($END - $START) / 1000000))
    
    echo "Request took ${DURATION}ms"
    if [ $DURATION -gt 500 ]; then
        echo -e "${GREEN}✓ Latency applied successfully${NC}"
    fi
    
    echo "Removing latency..."
    docker-compose exec -T api tc qdisc del dev eth0 root || true
    
    echo "Verifying normal operation..."
    curl -s http://localhost:8000/health > /dev/null
    echo -e "${GREEN}✓ API recovered after latency removal${NC}"
}

# Test 5: High Load
test_high_load() {
    echo -e "\n${YELLOW}[TEST 5] High Load Scenario${NC}"
    echo "Generating 1000 concurrent requests..."
    
    # Using Apache Bench if available
    if command -v ab &> /dev/null; then
        ab -n 1000 -c 100 http://localhost:8000/health
        echo -e "${GREEN}✓ High load test completed${NC}"
    else
        echo -e "${YELLOW}⚠ Apache Bench not installed, skipping${NC}"
    fi
}

# Test 6: Graceful Shutdown
test_graceful_shutdown() {
    echo -e "\n${YELLOW}[TEST 6] Graceful Shutdown Scenario${NC}"
    echo "Stopping API container..."
    docker-compose stop api
    
    echo "Waiting 5 seconds..."
    sleep 5
    
    echo "Verifying API is down..."
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API stopped successfully${NC}"
    fi
    
    echo "Restarting API..."
    docker-compose start api
    sleep 5
    
    echo "Verifying recovery..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓ API recovered after restart${NC}"
    else
        echo -e "${RED}✗ API did not recover${NC}"
    fi
}

# Run all tests
echo -e "\n${YELLOW}Starting chaos tests...${NC}\n"

test_database_failure
test_redis_failure
test_kafka_failure
test_network_latency
test_high_load
test_graceful_shutdown

echo -e "\n${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           CHAOS TESTING COMPLETED                           ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"

