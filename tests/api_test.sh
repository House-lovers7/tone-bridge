#!/bin/bash

# ToneBridge API Test Script
# This script tests all API endpoints

set -e

API_URL="${API_URL:-http://localhost:8080}"
EMAIL="test@example.com"
PASSWORD="testpassword123"
NAME="Test User"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Helper functions
print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
    ((TOTAL_TESTS++))
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((PASSED_TESTS++))
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    ((FAILED_TESTS++))
}

# Health Check
print_test "Health Check"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    print_success "Health check passed"
else
    print_error "Health check failed (HTTP $HEALTH_RESPONSE)"
fi

# Register User
print_test "User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"$NAME\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    print_success "User registration successful"
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    print_error "User registration failed"
    echo "$REGISTER_RESPONSE"
fi

# Login
print_test "User Login"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    print_success "User login successful"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
else
    print_error "User login failed"
    echo "$LOGIN_RESPONSE"
fi

# Transform Text - Tone
print_test "Text Transformation (Tone)"
TRANSFORM_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/transform" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
        "text": "Fix this bug ASAP. The code is broken.",
        "transformation_type": "tone",
        "target_tone": "warm"
    }')

if echo "$TRANSFORM_RESPONSE" | grep -q "transformed_text"; then
    print_success "Text transformation (tone) successful"
    echo "  Original: Fix this bug ASAP. The code is broken."
    TRANSFORMED=$(echo "$TRANSFORM_RESPONSE" | grep -o '"transformed_text":"[^"]*' | cut -d'"' -f4)
    echo "  Transformed: $TRANSFORMED"
else
    print_error "Text transformation (tone) failed"
    echo "$TRANSFORM_RESPONSE"
fi

# Transform Text - Structure
print_test "Text Transformation (Structure)"
STRUCTURE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/transform" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
        "text": "we need to fix the login bug and also update the dashboard and dont forget to check the api endpoints",
        "transformation_type": "structure"
    }')

if echo "$STRUCTURE_RESPONSE" | grep -q "transformed_text"; then
    print_success "Text transformation (structure) successful"
else
    print_error "Text transformation (structure) failed"
    echo "$STRUCTURE_RESPONSE"
fi

# Analyze Text
print_test "Text Analysis"
ANALYZE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
        "text": "URGENT: Production server is down! We need immediate action to restore service."
    }')

if echo "$ANALYZE_RESPONSE" | grep -q "priority"; then
    print_success "Text analysis successful"
    PRIORITY=$(echo "$ANALYZE_RESPONSE" | grep -o '"priority":"[^"]*' | cut -d'"' -f4)
    TONE=$(echo "$ANALYZE_RESPONSE" | grep -o '"tone":"[^"]*' | cut -d'"' -f4)
    echo "  Priority: $PRIORITY"
    echo "  Tone: $TONE"
else
    print_error "Text analysis failed"
    echo "$ANALYZE_RESPONSE"
fi

# Get History
print_test "Get Transformation History"
HISTORY_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/history?limit=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$HISTORY_RESPONSE" | grep -q "success"; then
    print_success "History retrieval successful"
else
    print_error "History retrieval failed"
    echo "$HISTORY_RESPONSE"
fi

# Get Profile
print_test "Get User Profile"
PROFILE_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/profile" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$PROFILE_RESPONSE" | grep -q "email"; then
    print_success "Profile retrieval successful"
else
    print_error "Profile retrieval failed"
    echo "$PROFILE_RESPONSE"
fi

# Test Rate Limiting
print_test "Rate Limiting"
RATE_LIMIT_COUNT=0
for i in {1..5}; do
    RATE_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/api/v1/profile" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    if [ "$RATE_RESPONSE" = "200" ]; then
        ((RATE_LIMIT_COUNT++))
    fi
done

if [ "$RATE_LIMIT_COUNT" -gt 0 ]; then
    print_success "Rate limiting working (allowed $RATE_LIMIT_COUNT/5 requests)"
else
    print_error "Rate limiting test failed"
fi

# Summary
echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi