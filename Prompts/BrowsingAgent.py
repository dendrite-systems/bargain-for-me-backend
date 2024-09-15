RANK_PROMPT_TEMPLATE = """
Given the following request and listings, please return a ranked json array of relevant items to the user. The items should be ranked in order of relevance to the user's request. 
Each listing in the array should be a JSON object with  'url', 'description', 'price','imageUrl' fields. Do not provide reasoning. 

User's request: {request}

Listings:
{listings}

Please analyze the request and the available listings. Return only relevant listings based on the request, maintaining their original details. Ensure the response is a valid JSON array. Do not provide reasoning; only return a json object with  'url', 'description', 'price','imageUrl' fields.

Example response:
[
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageUrl: "imageUrl"}},
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageUrl: "imageUrl"}},
  {{"url": "Item Url", "description": "Item Description", "price": "Item Price", "imageUrl: "imageUrl"}}
]
"""