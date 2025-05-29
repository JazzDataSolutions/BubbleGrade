#!/bin/bash

# BubbleGrade API Testing Script
# Comprehensive testing of all microservices and endpoints

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

BASE_URL="http://localhost:8080/api/v1"
OMR_URL="http://localhost:8090"
OCR_URL="http://localhost:8100"
 # Detect Docker Compose command
 if command -v docker-compose >/dev/null 2>&1; then
     COMPOSE_CMD="docker-compose"
 elif docker compose version >/dev/null 2>&1; then
     COMPOSE_CMD="docker compose"
 else
     echo -e "${RED}Neither 'docker-compose' nor 'docker compose' found. Please install Docker Compose.${NC}"
     exit 1
 fi
 
 # Ensure required tools are available
 for tool in curl jq; do
     if ! command -v $tool >/dev/null 2>&1; then
         echo -e "${RED}Required tool '$tool' not found. Please install it before running tests.${NC}"
         exit 1
     fi
 done

echo "🧪 BubbleGrade System Testing"
echo "=========================="

# Test 1: Health checks
echo -e "\n${BLUE}1. Health Checks${NC}"
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5173 || echo 'FAILED')"
echo "API: $(curl -s $BASE_URL/../health | jq -r '.status // "FAILED"')"
echo "OMR: $(curl -s $OMR_URL/health | jq -r '.status // "FAILED"')"
echo "OCR: $(curl -s $OCR_URL/health | jq -r '.status // "FAILED"')"

# Test 2: Create exam template
echo -e "\n${BLUE}2. Creating Exam Template${NC}"
TEMPLATE_RESPONSE=$(curl -s -X POST $BASE_URL/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Exam Template",
    "description": "20-question multiple choice exam",
    "total_questions": 20,
    "correct_answers": ["A","B","C","D","A","B","C","D","A","B","C","D","A","B","C","D","A","B","C","D"]
  }')

TEMPLATE_ID=$(echo $TEMPLATE_RESPONSE | jq -r '.id // "failed"')
echo "Template ID: $TEMPLATE_ID"

# Test 3: Upload test image
echo -e "\n${BLUE}3. Testing Document Upload${NC}"
# Create a test image (you would use a real exam sheet)
echo "Creating test image..."

# Using HTTPie (if available) or curl
if command -v http &> /dev/null; then
    echo "Using HTTPie for file upload..."
    UPLOAD_RESPONSE=$(http --form POST $BASE_URL/scans file@test_exam.jpg template_id=$TEMPLATE_ID 2>/dev/null || echo '{"error":"No test file"}')
else
    echo "Using curl for file upload..."
    # Create a dummy file for testing
    echo "Creating dummy test file..."
    convert -size 800x1000 xc:white -pointsize 24 \
      -draw "text 50,100 'NOMBRE: ________________'" \
      -draw "text 50,150 'CURP: __________________'" \
      -draw "rectangle 100,200 120,220" \
      -draw "rectangle 140,200 160,220" \
      -draw "rectangle 180,200 200,220" \
      -draw "rectangle 220,200 240,220" \
      test_exam.jpg 2>/dev/null || echo "test" > test_exam.txt
    
    UPLOAD_RESPONSE=$(curl -s -X POST $BASE_URL/scans \
      -F "file=@test_exam.jpg" \
      -F "template_id=$TEMPLATE_ID" 2>/dev/null || \
      curl -s -X POST $BASE_URL/scans \
      -F "file=@test_exam.txt" \
      -F "template_id=$TEMPLATE_ID")
fi

echo "Upload response: $UPLOAD_RESPONSE"
SCAN_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id // .scan_id // "failed"')
echo "Scan ID: $SCAN_ID"

# Test 4: Monitor processing
echo -e "\n${BLUE}4. Monitoring Processing${NC}"
for i in {1..10}; do
    SCAN_STATUS=$(curl -s $BASE_URL/scans/$SCAN_ID | jq -r '.status // "unknown"')
    echo "Status check $i: $SCAN_STATUS"
    
    if [[ "$SCAN_STATUS" == "COMPLETED" || "$SCAN_STATUS" == "NEEDS_REVIEW" ]]; then
        echo -e "${GREEN}Processing completed!${NC}"
        break
    elif [[ "$SCAN_STATUS" == "ERROR" ]]; then
        echo -e "${RED}Processing failed!${NC}"
        break
    fi
    
    sleep 2
done

# Test 5: Retrieve results
echo -e "\n${BLUE}5. Retrieving Results${NC}"
SCAN_RESULTS=$(curl -s $BASE_URL/scans/$SCAN_ID)
echo "Results: $SCAN_RESULTS" | jq '.'

# Test 6: Manual correction simulation
echo -e "\n${BLUE}6. Testing Manual Correction${NC}"
CORRECTION_RESPONSE=$(curl -s -X PATCH $BASE_URL/scans/$SCAN_ID \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": {
      "value": "JUAN CARLOS MENDOZA RUIZ",
      "needsReview": false
    },
    "curp": {
      "value": "MERJ950315HDFRNN04",
      "needsReview": false
    }
  }')

echo "Correction response: $CORRECTION_RESPONSE" | jq '.'

# Test 7: Export functionality
echo -e "\n${BLUE}7. Testing Export${NC}"
EXPORT_URL="$BASE_URL/exports/$SCAN_ID"
echo "Excel export: $(curl -s -o /dev/null -w '%{http_code}' $EXPORT_URL?format=xlsx)"
echo "CSV export: $(curl -s -o /dev/null -w '%{http_code}' $EXPORT_URL?format=csv)"

# Test 8: Direct OCR service test
echo -e "\n${BLUE}8. Direct OCR Service Test${NC}"
if [[ -f "test_exam.jpg" ]]; then
    OCR_REQUEST='{
      "region": "nombre",
      "boundingBox": {"x": 10, "y": 10, "width": 300, "height": 50}
    }'
    
    OCR_RESPONSE=$(curl -s -X POST $OCR_URL/ocr \
      -F "image=@test_exam.jpg" \
      -F "request=$OCR_REQUEST")
    
    echo "OCR Response: $OCR_RESPONSE" | jq '.'
fi

# Test 9: Direct OMR service test
echo -e "\n${BLUE}9. Direct OMR Service Test${NC}"
if [[ -f "test_exam.jpg" ]]; then
    OMR_RESPONSE=$(curl -s -X POST $OMR_URL/grade \
      -F "file=@test_exam.jpg")
    
    echo "OMR Response: $OMR_RESPONSE" | jq '.'
fi

# Test 10: List all scans
echo -e "\n${BLUE}10. Listing All Scans${NC}"
ALL_SCANS=$(curl -s "$BASE_URL/scans?limit=5")
echo "Recent scans: $ALL_SCANS" | jq '.scans[0:3]'

# Test 11: Performance metrics
echo -e "\n${BLUE}11. Performance Metrics${NC}"
echo "OCR Metrics: $(curl -s $OCR_URL/metrics | jq -r '.processingTime.average // "N/A"') ms avg"
echo "API Health: $(curl -s $BASE_URL/../health | jq -r '.services.database // "N/A"')"

# Test 12: Batch processing test
echo -e "\n${BLUE}12. Batch OCR Test${NC}"
if [[ -f "test_exam.jpg" ]]; then
    BATCH_REQUEST='[
      {
        "region": "nombre",
        "boundingBox": {"x": 50, "y": 100, "width": 400, "height": 40}
      },
      {
        "region": "curp", 
        "boundingBox": {"x": 50, "y": 150, "width": 400, "height": 40}
      }
    ]'
    
    BATCH_RESPONSE=$(curl -s -X POST $OCR_URL/ocr/batch \
      -F "image=@test_exam.jpg" \
      -F "requests=$BATCH_REQUEST")
    
    echo "Batch OCR Results:"
    echo "$BATCH_RESPONSE" | jq '.summary'
fi

# Cleanup
echo -e "\n${BLUE}Cleanup${NC}"
rm -f test_exam.jpg test_exam.txt

# Summary
echo -e "\n${GREEN}🎉 Testing Complete!${NC}"
echo "Check the logs for any errors:"
echo "$COMPOSE_CMD -f docker-compose.bubblegrade.yml logs"
echo ""
echo "Frontend URL: http://localhost:5173"
echo "API Docs: http://localhost:8080/docs"