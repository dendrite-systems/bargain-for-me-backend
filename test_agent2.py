import requests

def test_browse_endpoint():
    url = "http://127.0.0.1:8000/browse"
    data = {
        "request": "I'm looking for a used piano in good condition",
        "listings": [
            {"name": "Upright Piano", "description": "Beautiful upright piano in great condition", "value": 1000},
            {"name": "Electric Keyboard", "description": "Yamaha digital piano, barely used", "value": 500},
            {"name": "Grand Piano", "description": "Steinway grand piano, needs tuning", "value": 5000},
            {"name": "Guitar", "description": "Acoustic guitar, perfect for beginners", "value": 200},
            {"name": "Digital Piano", "description": "Roland digital piano, like new", "value": 800}
        ]
    }
    
    try:
        print(f"Sending POST request to {url}")
        print(f"Request data: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            print("Endpoint is working. Response:", response.json())
        else:
            print(f"Endpoint returned status code: {response.status_code}")
            print("Response:", response.text)
    except requests.RequestException as e:
        print(f"Error checking endpoint: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("\nTesting browse endpoint...")
    test_browse_endpoint()