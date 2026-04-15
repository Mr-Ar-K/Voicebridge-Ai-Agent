"""
API Testing and Integration Tests for VoiceBridge Backend.
Run this file to test all API endpoints.
"""

import requests
import json
import time
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
    
    def test_health_check(self) -> bool:
        """Test health check endpoint."""
        print("\n🏥 Testing Health Check...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health Check Passed: {data}")
                self.results.append(("Health Check", True))
                return True
            else:
                print(f"✗ Health Check Failed: {response.status_code}")
                self.results.append(("Health Check", False))
                return False
        except Exception as e:
            print(f"✗ Health Check Error: {e}")
            self.results.append(("Health Check", False))
            return False
    
    def test_get_all_schemes(self) -> bool:
        """Test getting all schemes."""
        print("\n📚 Testing Get All Schemes...")
        try:
            response = requests.get(f"{self.base_url}/schemes")
            if response.status_code == 200:
                data = response.json()
                scheme_count = data.get("count", 0)
                print(f"✓ Found {scheme_count} schemes")
                self.results.append(("Get All Schemes", True))
                return True
            else:
                print(f"✗ Failed to get schemes: {response.status_code}")
                self.results.append(("Get All Schemes", False))
                return False
        except Exception as e:
            print(f"✗ Get Schemes Error: {e}")
            self.results.append(("Get All Schemes", False))
            return False
    
    def test_embeddings(self) -> bool:
        """Test embedding generation."""
        print("\n📊 Testing Embeddings...")
        try:
            test_text = "Government scheme for farmers"
            response = requests.post(
                f"{self.base_url}/embed",
                json={"text": test_text}
            )
            if response.status_code == 200:
                data = response.json()
                embedding_dim = data.get("dimension", 0)
                print(f"✓ Generated embedding with {embedding_dim} dimensions")
                self.results.append(("Embeddings", True))
                return True
            else:
                print(f"✗ Embedding generation failed: {response.status_code}")
                self.results.append(("Embeddings", False))
                return False
        except Exception as e:
            print(f"✗ Embeddings Error: {e}")
            self.results.append(("Embeddings", False))
            return False
    
    def test_search_schemes(self) -> bool:
        """Test scheme search."""
        print("\n🔍 Testing Scheme Search...")
        try:
            query = "farmer"
            response = requests.get(
                f"{self.base_url}/search-schemes",
                params={"query": query, "top_k": 3}
            )
            if response.status_code == 200:
                data = response.json()
                num_results = len(data)
                print(f"✓ Search returned {num_results} results for '{query}'")
                if num_results > 0:
                    print(f"  - Top result: {data[0].get('name_en', 'Unknown')}")
                self.results.append(("Search Schemes", True))
                return True
            else:
                print(f"✗ Search failed: {response.status_code}")
                self.results.append(("Search Schemes", False))
                return False
        except Exception as e:
            print(f"✗ Search Error: {e}")
            self.results.append(("Search Schemes", False))
            return False
    
    def test_query_processing(self) -> bool:
        """Test query processing endpoint."""
        print("\n💬 Testing Query Processing...")
        try:
            query_data = {
                "question": "What schemes are available for farmers?",
                "language": "en"
            }
            response = requests.post(
                f"{self.base_url}/query",
                json=query_data
            )
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                schemes = data.get("schemes", [])
                suggestions = data.get("follow_up_suggestions", [])
                
                print(f"✓ Query processed successfully")
                print(f"  - Answer length: {len(answer)} characters")
                print(f"  - Schemes found: {len(schemes)}")
                print(f"  - Follow-up suggestions: {len(suggestions)}")
                print(f"  - Answer preview: {answer[:100]}...")
                
                self.results.append(("Query Processing", True))
                return True
            else:
                print(f"✗ Query processing failed: {response.status_code}")
                print(f"  Error: {response.text}")
                self.results.append(("Query Processing", False))
                return False
        except Exception as e:
            print(f"✗ Query Processing Error: {e}")
            self.results.append(("Query Processing", False))
            return False
    
    def test_multilingual_query(self) -> bool:
        """Test multilingual query support."""
        print("\n🌐 Testing Multilingual Query...")
        try:
            # Note: This requires translation to work properly
            query_data = {
                "question": "రైతులకు ఏమైనా పథకం ఉందా?",  # Telugu: Any scheme for farmers?
                "language": "te"
            }
            response = requests.post(
                f"{self.base_url}/query",
                json=query_data
            )
            if response.status_code == 200:
                data = response.json()
                language = data.get("language")
                print(f"✓ Multilingual query processed")
                print(f"  - Language: {language}")
                self.results.append(("Multilingual Query", True))
                return True
            else:
                print(f"⚠ Multilingual query test inconclusive: {response.status_code}")
                print(f"  Note: Translation requires Google Translate API setup")
                self.results.append(("Multilingual Query", False))
                return False
        except Exception as e:
            print(f"⚠ Multilingual Query: {e}")
            print(f"  Note: Translation API may not be configured")
            self.results.append(("Multilingual Query", None))
            return True  # Don't fail, as translation is optional
    
    def test_qdrant_info(self) -> bool:
        """Test Qdrant info endpoint."""
        print("\n🗄️ Testing Qdrant Status...")
        try:
            response = requests.get(f"{self.base_url}/qdrant-info")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Qdrant connection successful")
                self.results.append(("Qdrant Status", True))
                return True
            else:
                print(f"✗ Qdrant status check failed: {response.status_code}")
                self.results.append(("Qdrant Status", False))
                return False
        except Exception as e:
            print(f"✗ Qdrant Status Error: {e}")
            self.results.append(("Qdrant Status", False))
            return False
    
    def run_all_tests(self):
        """Run all tests and print summary."""
        print("=" * 60)
        print("🚀 VoiceBridge API Test Suite")
        print("=" * 60)
        
        try:
            self.test_health_check()
            self.test_qdrant_info()
            self.test_get_all_schemes()
            self.test_embeddings()
            self.test_search_schemes()
            self.test_query_processing()
            self.test_multilingual_query()
        except Exception as e:
            print(f"\n✗ Test suite interrupted: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, result in self.results if result is True)
        failed = sum(1 for _, result in self.results if result is False)
        total = len(self.results)
        
        for test_name, result in self.results:
            status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⚠ SKIP")
            print(f"{status}: {test_name}")
        
        print("\n" + "-" * 60)
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {failed} test(s) failed. Check configuration and API keys.")
        
        print("=" * 60)

def main():
    """Main test runner."""
    print("Ensure the FastAPI server is running at http://localhost:8000")
    print("Waiting for server availability...")
    
    # Try to connect to server
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Server is available!\n")
                break
        except:
            if i < max_retries - 1:
                print(f"Attempting connection ({i+1}/{max_retries})...")
                time.sleep(1)
            else:
                print("✗ Could not connect to server. Please start the server first:")
                print("  python main.py")
                return
    
    # Run tests
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
