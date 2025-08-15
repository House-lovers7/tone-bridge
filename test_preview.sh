#!/bin/bash

# ToneBridge Preview Mode Test Script
# This script tests the preview mode functionality without authentication

echo "========================================="
echo "  ToneBridge Preview Mode Test"
echo "========================================="
echo ""

# Set the API endpoint
API_URL="http://localhost:8082/api/v1"

# Test 1: Get preview info
echo "📋 Getting preview mode information..."
curl -s "${API_URL}/preview/info" | jq '.'
echo ""

# Test 2: Transform text - casual tone
echo "🔄 Test 1: Transforming text to casual tone..."
curl -X POST "${API_URL}/preview/transform" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "この件について至急ご確認いただき、明日までにご返答をお願いいたします。",
    "target_tone": "casual",
    "intensity_level": 2
  }' | jq '.'
echo ""

# Test 3: Transform text - professional tone
echo "🔄 Test 2: Transforming text to professional tone..."
curl -X POST "${API_URL}/preview/transform" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "ちょっと確認してもらえる？明日までに返事ちょうだい！",
    "target_tone": "professional",
    "intensity_level": 2
  }' | jq '.'
echo ""

# Test 4: Transform text - warm tone
echo "🔄 Test 3: Transforming text to warm tone..."
curl -X POST "${API_URL}/preview/transform" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "このタスクを完了させてください。期限は明日です。",
    "target_tone": "warm",
    "intensity_level": 3
  }' | jq '.'
echo ""

# Test 5: Test character limit (should fail)
echo "❌ Test 4: Testing character limit (should fail)..."
LONG_TEXT=$(python3 -c "print('あ' * 501)")
curl -X POST "${API_URL}/preview/transform" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"${LONG_TEXT}\",
    \"target_tone\": \"casual\",
    \"intensity_level\": 2
  }" | jq '.'
echo ""

# Test 6: Analyze text in preview mode
echo "🔍 Test 5: Analyzing text..."
curl -X POST "${API_URL}/preview/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "このプロジェクトについて、至急ご確認をお願いします。明日の会議で議論する必要があります。"
  }' | jq '.'
echo ""

echo "========================================="
echo "  Preview Mode Test Complete!"
echo "========================================="
echo ""
echo "Note: Preview mode limitations:"
echo "  - Max 500 characters per request"
echo "  - 3 requests per minute"
echo "  - 10 requests per day"
echo ""
echo "To test the Web UI preview mode:"
echo "  1. Open http://localhost:3001 in your browser"
echo "  2. Click '🎯 お試しで使ってみる（プレビュー版）'"
echo ""