VALIDATE_PROMPT_TEMPLATE = """
You are an AI agent tasked with determining whether a list of items fulfills the criteria of a user's original request. You are given the following information:

The user's original request:
{request}

Listings:
{listings}

Analyze each item and determine if it matches the user's request. Consider factors such as:

Does the item's description match the user's request?
Is the price within the user's goal?
Does the item meet any specific criteria mentioned in the request?

For each item, write our your reasoning, return a boolean value, :

1 if the item is relevant to the user's request
0 if the item is not relevant to the user's request.

If the item is relevant to the user's requests, come up with a first message to the seller. The first message should be brief and concise, while still expressing interest.

Example output format:
[
  {
    "item_id": "url",
    "reasoning": "This item matches the user's description and price range."
    "relevant": 1,
    "first message": "Hi! Is this still available?"
  },
  {
    "item_id": "url",
    "reasoning": 
    "relevant": 0,
    "first message": "Null"
  }
]
Remember to consider all aspects of the user's request and the item details when making your determination.
"""