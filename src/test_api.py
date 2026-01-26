import requests

#---------------------------------
#      Test health fo the server
#---------------------------------


url = "http://localhost:8000/"

response = requests.get(url)
print(response.text)

#---------------------------------
#      Test S3 endpiont
#---------------------------------

s3 = False
if s3:
    url = "http://localhost:8000/retrieve_s3"

    data = {
        'client': 'kyle',  # Example goal
        'idx': -1  # Example business profile
    }
    response = requests.post(url, data=data)

    if response.status_code == 200:
        result = response.json()
        print("Snapshot:", result['snapshot'])
    else:
        print(response.text)

#---------------------------------
#      Test Analyze endpoint
#---------------------------------

analyze = True
if analyze:
    
    url = "http://localhost:8000/analyze"

    # Form data: the two required strings
    data = {
        'goal': 'Increase revenue',  # Example goal
        'business_profile': 'A medium size general store'  # Example business profile
    }

    # File to upload: open in binary mode
    file_path = 'downloads/Superstore.csv'  # Replace with the actual file path
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, data=data, files=files)
        

    if response.status_code == 200:
        result = response.json()
        print("Message:", result['message'])
    else:
        print(response.text)