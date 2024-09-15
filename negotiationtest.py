import os
import json
from dotenv import load_dotenv
from together import Together

# Load environment variables
load_dotenv()

# Initialize Together AI client
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def negotiate_with_llama(negotiation_data):
    context = negotiation_data['context']
    users_goal = negotiation_data['users_goal']
    messages = negotiation_data['messages']

    # Construct the conversation history
    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    prompt = f"""
You are an AI negotiation assistant for second-hand items on a platform like Facebook Marketplace. Here's the context and your task:

Context: {context}
User's Goal: {users_goal}

Previous conversation:
{conversation_history}

Your task is to help the buyer buy an item. The listed price of the item may be higher than the user's goal. 
Consider the following:
1. The item's condition and features as described in the context
2. The user's goal and budget
3. The current state of the negotiation based on the conversation history

Provide your next response in the negotiation, aiming to achieve the user's goal while being respectful and reasonable. Do not be patronizing. You don't have to close the sale in one message--you can send messages back and forth to learn more about the item. 
Do not offer a price above the user's goal. I would be in deep trouble if you did that. 

Your response should be in the following JSON format:
{{
    "role": "assistant",
    "content": string,
    "reasoning": string,
    "current_offer": float
}}

The 'reasoning' field should briefly explain your negotiation strategy and why you chose this response.
"""

    messages = [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            repetition_penalty=1,
        )

        ai_response = completion.choices[0].message.content
        print("AI Response:", ai_response)

        # Parse the JSON response
        negotiation_response = json.loads(ai_response)
        return negotiation_response

    except Exception as e:
        print("Error in negotiation:", e)
        return None

def main():
    # Example negotiation data
    negotiation_data = {
        "context": "The seller is selling a couch that is $120, it's blue and in great condition",
        "users_goal": "I want to buy a couch for $100",
        "messages": [
            {"role": "seller", "content": "Hello! I'm selling a beautiful blue couch for $120. It's in great condition and very comfortable."},
            {"role": "assistant", "content": "Hi there! The couch sounds nice. I'm looking for a couch around $100. Would you be open to negotiating the price?"}
        ]
    }

    negotiation_result = negotiate_with_llama(negotiation_data)
    if negotiation_result:
        print("\nNegotiation Response:")
        print(f"Role: {negotiation_result['role']}")
        print(f"Content: {negotiation_result['content']}")
        print(f"Reasoning: {negotiation_result['reasoning']}")
        print(f"Current Offer: ${negotiation_result['current_offer']:.2f}")
    else:
        print("Failed to generate negotiation response.")

if __name__ == "__main__":
    main()