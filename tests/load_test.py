#!/usr/bin/env python3
"""
ToneBridge Load Testing Script
Tests system performance under various load conditions
"""

import os
import sys
import time
import json
import random
import threading
import requests
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8080")
NUM_USERS = int(os.getenv("NUM_USERS", "10"))
REQUESTS_PER_USER = int(os.getenv("REQUESTS_PER_USER", "10"))
RAMP_UP_TIME = int(os.getenv("RAMP_UP_TIME", "5"))  # seconds

# Test data
TEST_TEXTS = [
    "Please review this code when you have time.",
    "The bug in the login module needs immediate attention.",
    "Can we schedule a meeting to discuss the architecture?",
    "The deployment failed. We need to rollback immediately.",
    "I've updated the documentation as requested.",
    "The API endpoint is returning 500 errors intermittently.",
    "Could you help me understand this error message?",
    "The customer reported issues with the payment system.",
    "We need to optimize the database queries for better performance.",
    "The new feature is ready for QA testing."
]

TRANSFORMATION_TYPES = [
    {"type": "tone", "target_tone": "warm"},
    {"type": "tone", "target_tone": "professional"},
    {"type": "structure", "target_tone": None},
    {"type": "summarize", "target_tone": None}
]


class LoadTester:
    """Load testing harness for ToneBridge API"""
    
    def __init__(self, base_url: str, num_users: int, requests_per_user: int):
        self.base_url = base_url
        self.num_users = num_users
        self.requests_per_user = requests_per_user
        self.results = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        self.access_tokens = {}
        
    def create_test_user(self, user_id: int) -> str:
        """Create a test user and return access token"""
        email = f"loadtest_user_{user_id}@example.com"
        password = "LoadTest123!"
        
        # Try to register
        register_url = f"{self.base_url}/api/v1/auth/register"
        register_payload = {
            "email": email,
            "password": password,
            "name": f"Load Test User {user_id}"
        }
        
        try:
            response = requests.post(register_url, json=register_payload, timeout=10)
            if response.status_code == 201:
                return response.json().get("access_token")
        except:
            pass
        
        # If registration fails, try login
        login_url = f"{self.base_url}/api/v1/auth/login"
        login_payload = {
            "email": email,
            "password": password
        }
        
        try:
            response = requests.post(login_url, json=login_payload, timeout=10)
            if response.status_code == 200:
                return response.json().get("access_token")
        except Exception as e:
            print(f"Failed to authenticate user {user_id}: {e}")
            return None
    
    def simulate_user_behavior(self, user_id: int) -> List[Dict[str, Any]]:
        """Simulate a single user making requests"""
        results = []
        
        # Get access token for this user
        if user_id not in self.access_tokens:
            token = self.create_test_user(user_id)
            if not token:
                return results
            self.access_tokens[user_id] = token
        
        token = self.access_tokens[user_id]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        for request_num in range(self.requests_per_user):
            # Random delay between requests (0.5 to 2 seconds)
            time.sleep(random.uniform(0.5, 2))
            
            # Choose random operation
            operation = random.choice(["transform", "analyze", "history"])
            
            try:
                if operation == "transform":
                    # Transform text
                    text = random.choice(TEST_TEXTS)
                    transform_type = random.choice(TRANSFORMATION_TYPES)
                    
                    payload = {
                        "text": text,
                        "transformation_type": transform_type["type"]
                    }
                    if transform_type["target_tone"]:
                        payload["target_tone"] = transform_type["target_tone"]
                    
                    url = f"{self.base_url}/api/v1/transform"
                    start = time.time()
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    elapsed = time.time() - start
                    
                    results.append({
                        "user_id": user_id,
                        "operation": "transform",
                        "status_code": response.status_code,
                        "response_time": elapsed,
                        "timestamp": time.time()
                    })
                    
                elif operation == "analyze":
                    # Analyze text
                    text = random.choice(TEST_TEXTS)
                    payload = {"text": text}
                    
                    url = f"{self.base_url}/api/v1/analyze"
                    start = time.time()
                    response = requests.post(url, json=payload, headers=headers, timeout=30)
                    elapsed = time.time() - start
                    
                    results.append({
                        "user_id": user_id,
                        "operation": "analyze",
                        "status_code": response.status_code,
                        "response_time": elapsed,
                        "timestamp": time.time()
                    })
                    
                else:  # history
                    url = f"{self.base_url}/api/v1/history?limit=10"
                    start = time.time()
                    response = requests.get(url, headers=headers, timeout=10)
                    elapsed = time.time() - start
                    
                    results.append({
                        "user_id": user_id,
                        "operation": "history",
                        "status_code": response.status_code,
                        "response_time": elapsed,
                        "timestamp": time.time()
                    })
                    
            except requests.exceptions.Timeout:
                self.errors.append({
                    "user_id": user_id,
                    "operation": operation,
                    "error": "Timeout",
                    "timestamp": time.time()
                })
            except Exception as e:
                self.errors.append({
                    "user_id": user_id,
                    "operation": operation,
                    "error": str(e),
                    "timestamp": time.time()
                })
        
        return results
    
    def run_load_test(self):
        """Run the load test with all users"""
        print(f"Starting load test with {self.num_users} users")
        print(f"Each user will make {self.requests_per_user} requests")
        print(f"Ramp-up time: {RAMP_UP_TIME} seconds")
        print("-" * 60)
        
        self.start_time = time.time()
        
        # Use ThreadPoolExecutor for concurrent users
        with ThreadPoolExecutor(max_workers=self.num_users) as executor:
            futures = []
            
            for user_id in range(self.num_users):
                # Ramp-up delay
                delay = (RAMP_UP_TIME / self.num_users) * user_id
                time.sleep(delay)
                
                future = executor.submit(self.simulate_user_behavior, user_id)
                futures.append(future)
                print(f"Started user {user_id + 1}/{self.num_users}")
            
            # Collect results
            for future in as_completed(futures):
                user_results = future.result()
                self.results.extend(user_results)
        
        self.end_time = time.time()
        print("\nLoad test completed!")
    
    def analyze_results(self):
        """Analyze and print test results"""
        if not self.results:
            print("No results to analyze")
            return
        
        total_duration = self.end_time - self.start_time
        total_requests = len(self.results)
        successful_requests = len([r for r in self.results if r["status_code"] == 200])
        failed_requests = total_requests - successful_requests
        
        # Response times by operation
        operations = {}
        for result in self.results:
            op = result["operation"]
            if op not in operations:
                operations[op] = []
            operations[op].append(result["response_time"])
        
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        
        print(f"\nTest Duration: {total_duration:.2f} seconds")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests} ({successful_requests/total_requests*100:.1f}%)")
        print(f"Failed Requests: {failed_requests}")
        print(f"Error Count: {len(self.errors)}")
        print(f"Requests/Second: {total_requests/total_duration:.2f}")
        
        print("\n" + "-" * 40)
        print("Response Time Statistics (seconds)")
        print("-" * 40)
        
        all_times = [r["response_time"] for r in self.results]
        if all_times:
            print(f"Min: {min(all_times):.3f}")
            print(f"Max: {max(all_times):.3f}")
            print(f"Mean: {statistics.mean(all_times):.3f}")
            print(f"Median: {statistics.median(all_times):.3f}")
            if len(all_times) > 1:
                print(f"Std Dev: {statistics.stdev(all_times):.3f}")
            
            # Percentiles
            sorted_times = sorted(all_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p90 = sorted_times[int(len(sorted_times) * 0.9)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            
            print(f"\nPercentiles:")
            print(f"  50th: {p50:.3f}")
            print(f"  90th: {p90:.3f}")
            print(f"  95th: {p95:.3f}")
            print(f"  99th: {p99:.3f}")
        
        print("\n" + "-" * 40)
        print("Response Times by Operation")
        print("-" * 40)
        
        for op, times in operations.items():
            print(f"\n{op.upper()}:")
            print(f"  Count: {len(times)}")
            print(f"  Mean: {statistics.mean(times):.3f}s")
            print(f"  Median: {statistics.median(times):.3f}s")
            print(f"  Min: {min(times):.3f}s")
            print(f"  Max: {max(times):.3f}s")
        
        # Status code distribution
        status_codes = {}
        for result in self.results:
            code = result["status_code"]
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print("\n" + "-" * 40)
        print("Status Code Distribution")
        print("-" * 40)
        for code, count in sorted(status_codes.items()):
            print(f"  {code}: {count} ({count/total_requests*100:.1f}%)")
        
        # Errors
        if self.errors:
            print("\n" + "-" * 40)
            print("Errors")
            print("-" * 40)
            error_types = {}
            for error in self.errors:
                error_type = error.get("error", "Unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_types.items()):
                print(f"  {error_type}: {count}")
        
        # Performance assessment
        print("\n" + "=" * 60)
        print("PERFORMANCE ASSESSMENT")
        print("=" * 60)
        
        if successful_requests / total_requests >= 0.99:
            print("✅ Excellent: 99%+ success rate")
        elif successful_requests / total_requests >= 0.95:
            print("✅ Good: 95%+ success rate")
        elif successful_requests / total_requests >= 0.90:
            print("⚠️  Fair: 90%+ success rate")
        else:
            print("❌ Poor: <90% success rate")
        
        mean_time = statistics.mean(all_times)
        if mean_time <= 1.0:
            print("✅ Excellent: Mean response time ≤ 1s")
        elif mean_time <= 2.0:
            print("✅ Good: Mean response time ≤ 2s")
        elif mean_time <= 3.0:
            print("⚠️  Fair: Mean response time ≤ 3s")
        else:
            print("❌ Poor: Mean response time > 3s")
        
        if p95 <= 2.5:
            print("✅ Excellent: 95th percentile ≤ 2.5s")
        elif p95 <= 4.0:
            print("✅ Good: 95th percentile ≤ 4s")
        elif p95 <= 6.0:
            print("⚠️  Fair: 95th percentile ≤ 6s")
        else:
            print("❌ Poor: 95th percentile > 6s")


def main():
    """Main entry point"""
    print("=" * 60)
    print("ToneBridge Load Testing")
    print("=" * 60)
    print(f"Target: {API_BASE_URL}")
    print(f"Users: {NUM_USERS}")
    print(f"Requests per user: {REQUESTS_PER_USER}")
    print(f"Total requests: {NUM_USERS * REQUESTS_PER_USER}")
    print("=" * 60)
    print()
    
    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API health check failed: {response.status_code}")
            return 1
        print("✅ API is accessible")
    except Exception as e:
        print(f"❌ Cannot reach API: {e}")
        return 1
    
    # Run load test
    tester = LoadTester(API_BASE_URL, NUM_USERS, REQUESTS_PER_USER)
    tester.run_load_test()
    tester.analyze_results()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())