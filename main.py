import time
import subprocess
import csv
import requests
from datetime import datetime
import hmac
import hashlib

SECRET_KEY = 'FISHYBUSINESS-THEYCANFLY-BUTTHEYDONT-WANTYOU-TOKNOWTHAT22'
TIME_FORMAT = '%Y-%m-%d-%H'

def generate_current_token():
    """
    Generate a token for the *current* hour (UTC).
    """
    now_str = datetime.utcnow().strftime(TIME_FORMAT)
    return hmac.new(
        SECRET_KEY.encode('utf-8'), 
        now_str.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

def ping_network():
    """
    Continuously pings the network extender (192.168.1.139) and logs both
    successful (Connected) and failed (Disconnected) attempts.
    """
    while True:
        # Run the ping command to the IP address (Windows syntax with '-n 1')
        response = subprocess.run(
            ["ping", "-c", "1", "192.168.1.139"], 
            capture_output=True, 
            text=True
        )
        
        # Check if the ping was successful
        if response.returncode == 0:
            status = "Connected"
            packet_info = "Normal"
        else:
            status = "Disconnected"
            packet_info = "Dropped"
            # Log failure to error_log.csv
            with open('error_log.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), status, packet_info])
                #in 10s, send a POST request to the Flask host
                return
        
        # Capture the timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Send data to the Flask host
        send_to_host(timestamp, status, packet_info)
        
        # Wait 1 second before pinging again
        time.sleep(1)

def send_to_host(timestamp, status, packet_info):
    """
    Sends data via POST to the /post endpoint of the local Flask server,
    including the rotating HMAC token in X-API-Token.
    """
    url = "http://127.0.0.1:5000/post"
    
    # Form data
    data = {
        'timestamp': timestamp,
        'status': status,
        'packet_info': packet_info
    }
    
    # Generate a rotating token for the current hour
    token = generate_current_token()
    
    # Include it in the request headers
    headers = {
        'X-API-Token': token
    }
    
    # Make the POST request
    response = requests.post(url, data=data, headers=headers)
    
    if response.status_code == 200:
        print(f"Data posted successfully: {timestamp}, {status}, {packet_info}")
    else:
        print(f"Failed to post data: {response.status_code} - {response.text}")

if __name__ == "__main__":
    ping_network()
