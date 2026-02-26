import requests
import json
import os

url = "http://localhost:8000/api/upload/"
file_path = "BL COPY.PDF"

files = {'file': (file_path, open(file_path, 'rb'), 'application/pdf')}

try:
    response = requests.post(url, files=files)
    print("Status Code:", response.status_code)
    print("Response Body:", json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
       container_num = response.json().get('container_number')
       if container_num:
          print(f"\nTesting GET /api/shipment/{container_num}")
          get_response = requests.get(f"http://localhost:8000/api/shipment/{container_num}")
          print("Status Code:", get_response.status_code)
          print("Response Body:", json.dumps(get_response.json(), indent=2))
except Exception as e:
    print(e)
