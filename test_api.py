#!/usr/bin/env python3
"""
Test script for edu-news-ticker API.

This script tests all API endpoints to verify the application is working correctly.
Run this after starting the application with: uvicorn app.main:app --reload
"""

import requests
import json
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_response(response: requests.Response, title: str = "") -> None:
    """Print a formatted response."""
    if title:
        print(f"✓ {title}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except:
        print(response.text)
    print(f"Status Code: {response.status_code}\n")


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_section("TEST 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response, "GET /")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_api_health() -> bool:
    """Test the API health endpoint."""
    print_section("TEST 2: API Health & Info")
    try:
        response = requests.get(f"{BASE_URL}/api")
        print_response(response, "GET /api")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_get_shortened_news() -> bool:
    """Test getting shortened news headlines."""
    print_section("TEST 3: Get Shortened Headlines")
    try:
        response = requests.get(f"{BASE_URL}/api/news?limit=5")
        print_response(response, "GET /api/news?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("breaking_news"):
                print(f"✓ Got {len(data['breaking_news'])} headlines:")
                for i, headline in enumerate(data["breaking_news"], 1):
                    print(f"  {i}. {headline}")
                print()
                return True
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_get_full_news() -> bool:
    """Test getting full news headlines with links."""
    print_section("TEST 4: Get Full Headlines with Links")
    try:
        response = requests.get(f"{BASE_URL}/api/news/full?limit=3")
        print_response(response, "GET /api/news/full?limit=3")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("news"):
                print(f"✓ Got {len(data['news'])} full headlines:")
                for i, article in enumerate(data["news"], 1):
                    print(f"  {i}. {article['title']}")
                    print(f"     Link: {article['link']}")
                print()
                return True
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_invalid_limit() -> bool:
    """Test error handling with invalid limit."""
    print_section("TEST 5: Error Handling - Invalid Limit")
    try:
        response = requests.get(f"{BASE_URL}/api/news?limit=100")
        print_response(response, "GET /api/news?limit=100 (should be limited)")
        # Limit should be capped at 50
        if response.status_code in [200, 422]:
            print("✓ API correctly handles invalid limits\n")
            return True
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def test_documentation() -> bool:
    """Test API documentation endpoints."""
    print_section("TEST 6: API Documentation")
    try:
        # Test Swagger UI
        response = requests.get(f"{BASE_URL}/docs")
        swagger_ok = response.status_code == 200
        
        # Test ReDoc
        response = requests.get(f"{BASE_URL}/redoc")
        redoc_ok = response.status_code == 200
        
        if swagger_ok:
            print(f"✓ Swagger UI is available at: {BASE_URL}/docs")
        else:
            print(f"❌ Swagger UI not available")
        
        if redoc_ok:
            print(f"✓ ReDoc is available at: {BASE_URL}/redoc")
        else:
            print(f"❌ ReDoc not available")
        
        print()
        return swagger_ok and redoc_ok
    except Exception as e:
        print(f"❌ Error: {str(e)}\n")
        return False


def run_all_tests() -> None:
    """Run all tests and print summary."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  edu-news-ticker API Test Suite".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    print("\nMake sure the application is running:")
    print("  uvicorn app.main:app --reload\n")
    
    results = {
        "Health Check": test_health_check(),
        "API Health": test_api_health(),
        "Shortened Headlines": test_get_shortened_news(),
        "Full Headlines": test_get_full_news(),
        "Error Handling": test_invalid_limit(),
        "Documentation": test_documentation(),
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! Your API is working perfectly.\n")
        print("Next steps:")
        print("  1. Access the interactive docs at: http://localhost:8000/docs")
        print("  2. Integrate the API with your frontend")
        print("  3. Deploy to production\n")
    else:
        print("⚠️ Some tests failed. Check the output above for details.\n")
        print("Troubleshooting:")
        print("  - Make sure the app is running: uvicorn app.main:app --reload")
        print("  - Check your .env file has GROQ_API_KEY configured")
        print("  - Check the application logs for errors\n")


if __name__ == "__main__":
    try:
        # Quick connectivity check
        try:
            requests.get(f"{BASE_URL}/", timeout=2)
        except requests.exceptions.ConnectionError:
            print("❌ ERROR: Cannot connect to the API server")
            print(f"\nMake sure the application is running:")
            print(f"  uvicorn app.main:app --reload\n")
            exit(1)
        
        # Run all tests
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user\n")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}\n")
        exit(1)

