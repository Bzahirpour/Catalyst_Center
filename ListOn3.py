import requests
import json
import time
import sys
import getpass

# DNA Center settings
DNAC_URL = "dnac.fda.gov"
DNAC_PORT = "443"
USERNAME = input("ad_dio_firstinitial.lastname: ")
PASSWORD = getpass.getpass("PIN+RSA: ")

# List of device IDs to run commands on
DEVICE_IDS = [
    'fc015970-0156-42d7-9f4f-0ab65e34d620',
    '5d39bcd8-cfa0-4879-a286-0f2eaa44a349',
    '5bc1f9e7-141e-40cb-9387-5c67ba217cc7'
]

# Disable SSL warnings for simplicity
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def main():
    try:
        token = get_auth_token()
        with open("device_output.txt", "w") as output_file:
            for device_id in DEVICE_IDS:
                # Fetch the device information (like hostname) using the device ID
                device = get_device_by_id(token, device_id)
                print(f"Running commands on device {device['hostname']} ({device_id})...")
                
                # Run the show commands
                task_id_1 = run_cli_command(token, device_id, "show run | include hostname")
                task_id_2 = run_cli_command(token, device_id, "show run | include location")
                
                # Get the results for both commands
                file_id_1 = get_task_result(task_id_1, token)
                file_id_2 = get_task_result(task_id_2, token)
                
                # Retrieve command output
                output_1 = get_cli_command(file_id_1, token)
                output_2 = get_cli_command(file_id_2, token)
                
                # Write output to file
                output_file.write(f"Output for {device['hostname']} ({device_id}):\n")
                output_file.write(f"--- show run | include hostname ---\n{output_1}\n")
                output_file.write(f"--- show run | include location ---\n{output_2}\n")
                output_file.write("\n" + "="*50 + "\n")
            
        print("Output written to 'device_output.txt'")
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(1)

def get_auth_token():
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/system/api/v1/auth/token"
    response = requests.post(url, auth=(USERNAME, PASSWORD), verify=False)
    if 'Token' in response.json():
        print("Logged in!")
        return response.json()['Token']
    else:
        print("Incorrect login credentials. Exiting...")
        input("Press enter to exit...")
        sys.exit(1)

def get_device_by_id(token, device_id):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/network-device/{device_id}"
    headers = {"X-Auth-Token": token}
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        return response.json()['response']
    else:
        print(f"Failed to fetch device {device_id}: {response.text}")
        sys.exit(1)

def run_cli_command(token, device_id, command):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/network-device-poller/cli/read-request"
    headers = {"X-Auth-Token": token}
    payload = {
        "commands": [command],
        "description": command,
        "deviceUuids": [device_id],
        "name": f"{command.replace(' ', '_')}_command",
        "timeout": 60
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 202:
        task_id = response.json()['response']['taskId']
        return task_id
    else:
        print(f"Failed to run command on device {device_id}: {response.text}")
        sys.exit(1)

def get_task_result(task_id, token):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/task/{task_id}"
    headers = {"X-Auth-Token": token}
    while True:
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            task_data = response.json()
            task_progress = task_data['response']['progress']
            try:
                progress_json = json.loads(task_progress)
                if 'fileId' in progress_json:
                    file_id = progress_json['fileId']
                    return file_id
            except json.JSONDecodeError:
                time.sleep(1)
                continue

def get_cli_command(file_id, token):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/file/{file_id}"
    headers = {"X-Auth-Token": token}
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        result = response.json()
        data = result[0]["commandResponses"].get("SUCCESS", "")
        return data
    else:
        print(f"Failed to retrieve output from file {file_id}: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
