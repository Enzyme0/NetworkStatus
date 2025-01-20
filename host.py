from flask import Flask, render_template, request
import csv
import random
import time
from flask_wtf.csrf import CSRFProtect
from flask import jsonify
import hmac
import hashlib
import datetime  # <--- Changed from "from datetime import datetime"

app = Flask(__name__)

# Flask-WTF CSRF key
app.config['SECRET_KEY'] = 'FISHYBUSINESS-THEYCANFLY-BUTTHEYDONT-WANTYOU-TOKNOWTHAT22'

# Rotating key secrets
SECRET_KEY = 'FISHYBUSINESS-THEYCANFLY-BUTTHEYDONT-WANTYOU-TOKNOWTHAT22'
TIME_FORMAT = '%Y-%m-%d-%H'

csrf = CSRFProtect(app)
csrf.init_app(app)

def generate_sample_csv():
    with open('data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Status", "Packet Info"])
        for _ in range(60):
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            status = random.choice(['Connected', 'Disconnected'])
            packet_info = random.choice(['Normal', 'Dropped'])
            writer.writerow([timestamp, status, packet_info])

def sanitize_csv_field(field):
    if field.startswith(('=', '+', '-', '@')):
        return "'" + field
    return field

def generate_token_for_time(dt):
    """
    Given a datetime.datetime object, produce a hex digest token by HMACing
    the datetime string with the shared SECRET_KEY.
    """
    time_str = dt.strftime(TIME_FORMAT)
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        time_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def valid_tokens():
    """
    Return a list of tokens that should be valid:
    - Current hour
    - Previous hour (helps with minor clock skews)
    """
    now = datetime.datetime.utcnow()
    tokens = []
    
    # current hour
    tokens.append(generate_token_for_time(now))
    
    # previous hour
    previous_hour = now - datetime.timedelta(hours=1)
    tokens.append(generate_token_for_time(previous_hour))

    return tokens

@app.route('/', methods=['GET'])
@csrf.exempt
def index():
    with open('data.csv', 'r') as f:
        reader = csv.reader(f)
        data = list(reader)[1:]  # skip header

    feed_filter = request.args.get('feed', 'all')
    error_filter = request.args.get('error', 'all')

    valid_feeds = ['all', 'Connected', 'Disconnected']
    if feed_filter not in valid_feeds:
        feed_filter = 'all'

    valid_errors = ['all', 'Normal', 'Dropped']
    if error_filter not in valid_errors:
        error_filter = 'all'

    if feed_filter != 'all':
        data = [row for row in data if row[1] == feed_filter]

    if error_filter != 'all':
        data = [row for row in data if row[2] == error_filter]

    # Use datetime.datetime.strptime (since we imported datetime, not strptime directly)
    data.sort(
        key=lambda row: datetime.datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S'),
        reverse=True
    )

    return render_template('index.html', data=data, feed_filter=feed_filter, error_filter=error_filter)

@app.route('/post', methods=['POST'])
@csrf.exempt
def post():
    incoming_token = request.headers.get('X-API-Token')
    if not incoming_token:
        return "Missing API Token", 401
    
    if incoming_token not in valid_tokens():
        return "Unauthorized", 401

    timestamp = request.form.get('timestamp')
    status = request.form.get('status')
    packet_info = request.form.get('packet_info')
    print(f"Received data: {timestamp}, {status}, {packet_info}")
    # Sanitize the input
    timestamp = sanitize_csv_field(timestamp)
    status = sanitize_csv_field(status)
    packet_info = sanitize_csv_field(packet_info)

    with open('data.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, status, packet_info])
    return "Data posted successfully!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
