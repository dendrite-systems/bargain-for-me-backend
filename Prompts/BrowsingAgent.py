RANK_PROMPT_TEMPLATE = """
Given the following request and listings, please return a ranked json array of relevant items to the user. The items should be ranked in order of relevance to the user's request. 
Each listing in the array should be a JSON object with only a 'url' field. Do not return anything else. Do not provide reasoning. 

User's request: {request}

Listings:
{listings}

Please analyze the request and the available listings. Return only relevant listings based on the request, maintaining their original details. Ensure the response is a valid JSON array. Do not provide reasoning; only return a json object of URLs. 
If none of the listings look relevant, return null. Do not return anything else. 
Example response:
[
  {{"url": "Item Url"}},
  {{"url": "Item Url"}},
  {{"url": "Item Url"}}
]
"""