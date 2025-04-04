import requests
import json
import time
import sys
import getpass

DNAC_URL = "dnac.fda.gov"
DNAC_PORT = "443"
USERNAME = input("ad_dio_firstinitial.lastname: ")
PASSWORD = getpass.getpass("PIN+RSA: ")
DEVICES = ('fc015970-0156-42d7-9f4f-0ab65e34d620', '5d39bcd8-cfa0-4879-a286-0f2eaa44a349', '5bc1f9e7-141e-40cb-9387-5c67ba217cc7')
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

def main():
    while True:
        try:
            token = get_auth_token()
            for device in DEVICES:
                task_id = run_cli_command(token, device)
                file_id = get_task_result(task_id, token)
                get_cli_command(file_id, token, device)
                print("")
            input("Press enter to exit...")
            sys.exit(1)
        except KeyboardInterrupt:
            continue


def get_auth_token():
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/system/api/v1/auth/token"
    response = requests.post(url, auth=(USERNAME, PASSWORD), verify=False)
    if 'Token' in response.json():
        print("Logged in!")
        print("")
        token = response.json()['Token']
        return token
    else:
        print("Incorrect login credentials. Try again...")
        input("Press enter to exit...")
        sys.exit(1)

def run_cli_command(token, device_id):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/network-device-poller/cli/read-request"
    headers = {"X-Auth-Token": token}
    command = [
        f"show running-config | include location"
    ]
    payload = {
        "commands": command,
        "description": "show running-config | include location",
        "deviceUuids": [device_id],
        "name": "show_run_include_location_command",
        "timeout": 60
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    task_id = response.json()['response']['taskId']
    return task_id

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

def get_cli_command(file_id, token, device_id):
    url = f"https://{DNAC_URL}:{DNAC_PORT}/dna/intent/api/v1/file/{file_id}"
    headers = {"X-Auth-Token": token}
    response = requests.get(url, headers=headers, verify=False)
    result = response.json()
    data = result[0]["commandResponses"]["SUCCESS"]
    temp = data.get(f"show running-config | include location", "")
    lines = temp.splitlines()
    formatted_lines = []
    for line in lines:
        if 'location' in line:
            formatted_lines.append(line.strip())
    if device_id == 'fc015970-0156-42d7-9f4f-0ab65e34d620' or device_id == '5d39bcd8-cfa0-4879-a286-0f2eaa44a349':
        if device_id == 'fc015970-0156-42d7-9f4f-0ab65e34d620':
            print("adc-wgwr-01#show running-config | include location")
            print(formatted_lines)
        else:
            print("wodc-wgwr-01#show running-config | include location")
            print(formatted_lines)            
    else:
        print("nctr-wgwr-01#show running-config | include location")
        print(formatted_lines)
        print("")

if __name__ == "__main__":
    main()

"""3/30/2025 - dante cicciarelli + benjamin zahirpour 4/4/2025"""
