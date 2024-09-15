BROWSING_PROMPT_TEMPLATE = """
Given the following request and listings, please return a JSON array of the top 3 most relevant listings. Each listing in the array should be a JSON object with 'name', 'description', and 'value' fields.

Request: {request}

Listings:
{listings}

Please analyze the request and the available listings. Return only the top 3 most relevant listings based on the request, maintaining their original details. Ensure the response is a valid JSON array.

Response format:
[
  {{"name": "Item Name", "description": "Item Description", "value": 100.00}},
  {{"name": "Item Name", "description": "Item Description", "value": 200.00}},
  {{"name": "Item Name", "description": "Item Description", "value": 300.00}}
]
"""