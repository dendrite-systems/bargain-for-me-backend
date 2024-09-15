import requests

def test_chat_endpoint():
    url = "http://127.0.0.1:8000/chat"
    data = {
        "message": "I'm interested in buying the piano listed here. Can you negotiate the price for me?",
        "chat_history": [],
        "seller_response": {
            "price": 100,
            "location": "NYC",
            "description": "The piano is in great shape!"
        }
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
    print("\nTesting chat endpoint...")
    test_chat_endpoint()