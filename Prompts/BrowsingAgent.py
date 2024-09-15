RANK_PROMPT_TEMPLATE = """
Given the following request and listings, please return a JSON array of the top 8 most relevant listings to the user's request.
Each listing in the array should be a JSON object with 'name', 'description', and 'price' fields.

User's request: {request}

Listings:
{listings}

Please analyze the request and the available listings. Return only the top 8 most relevant listings based on the request, maintaining their original details. Ensure the response is a valid JSON array.

Response format:
[
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageuUrl: "imageUrl"}},
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageuUrl: "imageUrl"}},
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageuUrl: "imageUrl"}}
]
"""