#!/usr/bin/env python3
"""
ToneBridge Integration Tests
Comprehensive testing of all API endpoints and transformations
"""

import os
import sys
import time
import json
import requests
import unittest
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
TEST_EMAIL = "integration_test@example.com"
TEST_PASSWORD = "IntegrationTest123!"
TEST_NAME = "Integration Test User"


class ToneBridgeAPITests(unittest.TestCase):
    """Test suite for ToneBridge API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.api_url = API_BASE_URL
        cls.access_token = None
        cls.user_id = None
        
        # Register and login test user
        cls._register_test_user()
        cls._login_test_user()
    
    @classmethod
    def _register_test_user(cls):
        """Register a test user"""
        url = f"{cls.api_url}/api/v1/auth/register"
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME,
            "organization": "Test Organization"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 201:
                data = response.json()
                cls.access_token = data.get("access_token")
                print(f"✓ Test user registered: {TEST_EMAIL}")
            elif response.status_code == 400:
                # User might already exist, try to login
                print("User already exists, will login instead")
        except Exception as e:
            print(f"Failed to register test user: {e}")
    
    @classmethod
    def _login_test_user(cls):
        """Login test user"""
        if cls.access_token:
            return  # Already have token from registration
        
        url = f"{cls.api_url}/api/v1/auth/login"
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                cls.access_token = data.get("access_token")
                print(f"✓ Test user logged in: {TEST_EMAIL}")
            else:
                print(f"Failed to login: {response.text}")
        except Exception as e:
            print(f"Failed to login test user: {e}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def test_01_health_check(self):
        """Test health check endpoints"""
        # Test gateway health
        response = requests.get(f"{self.api_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        
        # Test readiness
        response = requests.get(f"{self.api_url}/ready")
        self.assertEqual(response.status_code, 200)
    
    def test_02_authentication(self):
        """Test authentication flow"""
        # Test login with wrong credentials
        url = f"{self.api_url}/api/v1/auth/login"
        payload = {
            "email": TEST_EMAIL,
            "password": "WrongPassword"
        }
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 401)
        
        # Test login with correct credentials
        payload["password"] = TEST_PASSWORD
        response = requests.post(url, json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
    
    def test_03_tone_transformation(self):
        """Test tone transformation"""
        url = f"{self.api_url}/api/v1/transform"
        
        test_cases = [
            {
                "input": "Fix this bug immediately. The code is completely broken.",
                "type": "tone",
                "tone": "warm",
                "check": lambda x: "please" in x.lower() or "would" in x.lower()
            },
            {
                "input": "hey can u pls check this when u have time thx",
                "type": "tone",
                "tone": "professional",
                "check": lambda x: len(x) > len("hey can u pls check this when u have time thx")
            }
        ]
        
        for test_case in test_cases:
            payload = {
                "text": test_case["input"],
                "transformation_type": test_case["type"],
                "target_tone": test_case["tone"]
            }
            
            response = requests.post(url, json=payload, headers=self._get_headers())
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn("data", data)
            self.assertIn("transformed_text", data["data"])
            
            transformed = data["data"]["transformed_text"]
            self.assertNotEqual(transformed, test_case["input"])
            
            # Check if transformation meets criteria
            if test_case["check"]:
                self.assertTrue(
                    test_case["check"](transformed),
                    f"Transformation check failed for {test_case['tone']} tone"
                )
    
    def test_04_structure_transformation(self):
        """Test structure transformation"""
        url = f"{self.api_url}/api/v1/transform"
        
        unstructured_text = """
        we need to fix the login bug and also update the dashboard 
        and dont forget to check the api endpoints also the 
        documentation needs updating
        """
        
        payload = {
            "text": unstructured_text,
            "transformation_type": "structure"
        }
        
        response = requests.post(url, json=payload, headers=self._get_headers())
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        transformed = data["data"]["transformed_text"]
        
        # Check if structure improved (likely has bullet points or numbers)
        self.assertTrue(
            any(marker in transformed for marker in ["•", "-", "1.", "*"]),
            "Structured text should contain list markers"
        )
    
    def test_05_summarization(self):
        """Test summarization"""
        url = f"{self.api_url}/api/v1/transform"
        
        long_text = """
        We had a comprehensive meeting today to discuss the Q4 product roadmap. 
        The key decisions made were to prioritize the mobile app development, 
        allocate more resources to the API optimization project, and postpone 
        the blockchain integration until Q1 next year. The team also agreed 
        to implement weekly sprint reviews and increase the QA budget by 20%. 
        Additionally, we discussed the need for better documentation and decided 
        to hire a technical writer. The meeting concluded with action items 
        assigned to each team lead.
        """
        
        payload = {
            "text": long_text,
            "transformation_type": "summarize"
        }
        
        response = requests.post(url, json=payload, headers=self._get_headers())
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        summary = data["data"]["transformed_text"]
        
        # Check if summary is shorter
        self.assertLess(len(summary), len(long_text))
        self.assertGreater(len(summary), 50)  # Not too short
    
    def test_06_text_analysis(self):
        """Test text analysis"""
        url = f"{self.api_url}/api/v1/analyze"
        
        test_texts = [
            {
                "text": "URGENT: Production server is down! Need immediate action!",
                "expected_priority": "critical",
                "expected_tone_keywords": ["urgent", "aggressive", "demanding"]
            },
            {
                "text": "When you have a chance, could you please review my PR?",
                "expected_priority": "low",
                "expected_tone_keywords": ["polite", "passive", "warm"]
            }
        ]
        
        for test in test_texts:
            payload = {"text": test["text"]}
            response = requests.post(url, json=payload, headers=self._get_headers())
            self.assertEqual(response.status_code, 200)
            
            data = response.json()["data"]
            
            # Check priority
            if test["expected_priority"]:
                self.assertEqual(
                    data["priority"],
                    test["expected_priority"],
                    f"Priority mismatch for: {test['text'][:50]}..."
                )
            
            # Check tone
            self.assertIn("tone", data)
            self.assertIn("clarity", data)
            self.assertIsInstance(data["clarity"], (int, float))
            self.assertGreaterEqual(data["clarity"], 0)
            self.assertLessEqual(data["clarity"], 1)
    
    def test_07_history_retrieval(self):
        """Test transformation history"""
        # First, create some transformations
        transform_url = f"{self.api_url}/api/v1/transform"
        
        for i in range(3):
            payload = {
                "text": f"Test message {i}",
                "transformation_type": "tone",
                "target_tone": "warm"
            }
            requests.post(transform_url, json=payload, headers=self._get_headers())
        
        # Now retrieve history
        history_url = f"{self.api_url}/api/v1/history?limit=10"
        response = requests.get(history_url, headers=self._get_headers())
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("data", data)
        self.assertIsInstance(data["data"], list)
        self.assertGreater(len(data["data"]), 0)
        
        # Check history item structure
        if data["data"]:
            item = data["data"][0]
            self.assertIn("original_text", item)
            self.assertIn("transformed_text", item)
            self.assertIn("transformation_type", item)
            self.assertIn("created_at", item)
    
    def test_08_rate_limiting(self):
        """Test rate limiting"""
        url = f"{self.api_url}/api/v1/profile"
        
        # Make rapid requests
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = requests.get(url, headers=self._get_headers())
            responses.append(response.status_code)
            if response.status_code == 429:  # Too Many Requests
                break
        
        # Check if rate limiting kicked in
        self.assertIn(429, responses, "Rate limiting should trigger after many rapid requests")
    
    def test_09_caching(self):
        """Test caching mechanism"""
        url = f"{self.api_url}/api/v1/transform"
        
        # Same request twice
        payload = {
            "text": "This is a caching test message",
            "transformation_type": "tone",
            "target_tone": "professional"
        }
        
        # First request
        start_time = time.time()
        response1 = requests.post(url, json=payload, headers=self._get_headers())
        time1 = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time()
        response2 = requests.post(url, json=payload, headers=self._get_headers())
        time2 = time.time() - start_time
        
        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Second request should be faster (cached)
        self.assertLess(time2, time1 * 0.5, "Cached request should be significantly faster")
        
        # Results should be identical
        self.assertEqual(
            response1.json()["data"]["transformed_text"],
            response2.json()["data"]["transformed_text"]
        )
    
    def test_10_error_handling(self):
        """Test error handling"""
        # Test with invalid transformation type
        url = f"{self.api_url}/api/v1/transform"
        payload = {
            "text": "Test message",
            "transformation_type": "invalid_type"
        }
        response = requests.post(url, json=payload, headers=self._get_headers())
        self.assertEqual(response.status_code, 400)
        
        # Test with missing required fields
        payload = {"transformation_type": "tone"}  # Missing text
        response = requests.post(url, json=payload, headers=self._get_headers())
        self.assertEqual(response.status_code, 400)
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{self.api_url}/api/v1/profile", headers=headers)
        self.assertEqual(response.status_code, 401)


def run_tests():
    """Run all tests and print summary"""
    print("=" * 60)
    print("ToneBridge Integration Tests")
    print("=" * 60)
    print(f"Testing API at: {API_BASE_URL}")
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ToneBridgeAPITests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())