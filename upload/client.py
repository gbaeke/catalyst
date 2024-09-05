import sys
import requests
import os

def upload_file(file_path, url, template_name):
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {'template_name': template_name}
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                print(f"File uploaded successfully. Response: {response.json()}")
            else:
                print(f"Failed to upload file. Status code: {response.status_code}")
                print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py <file_path> <template_name> <number_of_uploads>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    template_name = sys.argv[2]
    num_uploads = int(sys.argv[3])
    
    upload_url = "http://localhost:8000/upload/"
    
    for i in range(num_uploads):
        print(f"Upload attempt {i+1}/{num_uploads}")
        upload_file(file_path, upload_url, template_name)