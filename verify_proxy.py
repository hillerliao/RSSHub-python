
import requests
import time
import subprocess
import sys
import threading
import os

def start_server():
    try:
        subprocess.run(["flask", "run", "--port=5000"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Server failed to start: {e}")

def test_proxy():
    # Wait for server to start, or assume it's running
    time.sleep(2)
    
    # Test 1: Basic functionality without proxy
    print("Test 1: Basic functionality without proxy")
    url = "http://localhost:5000/proxy/readability?url=https://example.com"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("SUCCESS: Proxy returned 200 OK")
            if "Example Domain" in response.text:
                 print("SUCCESS: Content contains expected text.")
            else:
                 print("FAILURE: Content does not contain expected text.")
        else:
            print(f"FAILURE: Proxy returned status code {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        print(f"FAILURE: Exception during request: {e}")

    # Test 2: With proxy parameter (using an invalid proxy to verify it's being used/tried)
    # We expect a failure or timeout if the proxy is unreachable.
    print("\nTest 2: With proxy parameter")
    # Using a local non-existent proxy port to force an error
    proxy_test_url = "http://localhost:5000/proxy/readability?url=https://example.com&proxy=http://127.0.0.1:9999"
    try:
        response = requests.get(proxy_test_url)
        # We expect 400 or 500 error because the proxy is unreachable
        if response.status_code == 400 and "Error: Failed to fetch URL" in response.text:
             print("SUCCESS: Received expected error when using unreachable proxy.")
        else:
             print(f"NOTE: Response code {response.status_code}. Response: {response.text}")
             print("If you have a proxy running at 9999, this might be a success.")

    except Exception as e:
        print(f"FAILURE: Exception during request: {e}")


if __name__ == "__main__":
    try:
        requests.get("http://localhost:5000/")
        print("Server is already running.")
    except:
        print("Server not running. Please start the server separately with 'uv run python main.py'.")
        sys.exit(1)

    test_proxy()
