from flask import Flask, render_template, request, redirect, url_for
import re
import json
import hashlib

# Global set to store hashes of payloads
submitted_payload_hashes = set()


def hash_payload(payload):
    # Create a hash of the payload
    return hashlib.sha256(payload.encode()).hexdigest()

app = Flask(__name__)

# Store the user submissions and results in memory
leaderboard2 = []

# Define the requirements to check against all the contexts you provided
requirements = [
    {'name': 'Escape double quotes', 'pattern': r'\"'},
    {'name': 'Escape single quotes', 'pattern': r'\''},
    {'name': 'Break out of textarea', 'pattern': r'</textarea>'},
    {'name': 'Break out of style', 'pattern': r'</style>'},
    {'name': 'Break out of noscript', 'pattern': r'</noscript>'},
    {'name': 'Break out of noembed', 'pattern': r'</noembed>'},
    {'name': 'Break out of template', 'pattern': r'</template>'},
    {'name': 'Break out of frameset', 'pattern': r'</frameset>'},
    {'name': 'Break out of select', 'pattern': r'</select>'},
    {'name': 'Break out of script', 'pattern': r'</script>'},
    {'name': 'Break out of comment', 'pattern': r'-->'},
    {'name': 'Break out of iframe', 'pattern': r'<\/iframe>'},
    {'name': 'Trigger alert() in 2+ contexts', 'pattern': r'alert\(\)', 'count': 2},  # Must trigger in 2+ contexts
    {'name': 'Limit payload length to 1024 characters', 'custom_check': 'check_payload_length'},  # Custom check
    {'name': 'Disable network requests', 'custom_check': 'check_network_requests'},  # Custom check
    {'name': 'Trigger alert()', 'pattern': r'alert\(\)'},
    {'name': 'Escape HTML entities', 'pattern': r'&lt;'},
    {'name': 'Escape script closing', 'pattern': r'<\/script>'},
]


def store_payload(username, payload, result):
    # Store the payload and result in a JSON file
    entry = {
        'username': username,
        'payload': payload,
        'result': result
    }
    with open('payloads.json', 'a') as f:
        json.dump(entry, f)
        f.write('\n')


def evaluate_payload(username, payload):
    # Check if the payload has been submitted before
    payload_hash = hash_payload(payload)
    if payload_hash in submitted_payload_hashes:
        print(f"Duplicate payload submission detected for user {username}.")
        return

    # Add the new payload hash to the set
    submitted_payload_hashes.add(payload_hash)

    # Count the number of characters in the payload
    payload_length = len(payload)

    # Evaluate the payload for each requirement
    resultsx = []
    context_bypass_count = 0  
    alert_count = len(re.findall(r'alert\(\)', payload))

    for requirement in requirements:
        if 'pattern' in requirement:
            if re.search(requirement['pattern'], payload):
                resultsx.append(True)
                if "Break out of" in requirement['name']:
                    context_bypass_count += 1
            else:
                resultsx.append(False)
        elif 'custom_check' in requirement:
            if requirement['custom_check'] == 'check_payload_length':
                resultsx.append(payload_length <= 1024)
            elif requirement['custom_check'] == 'check_network_requests':
                if re.search(r'fetch\(|XMLHttpRequest\(|<img ', payload):
                    resultsx.append(False)
                else:
                    resultsx.append(True)
        else:
            resultsx.append(False)

    xss_valid = context_bypass_count >= 2 and alert_count >= 1

    if not xss_valid:
        print(f"Payload did not break out of at least 2 contexts, count: {context_bypass_count}")
        return

    assert len(resultsx) == len(requirements), "Mismatch between results and requirements"
    
    passed_requirements = resultsx.count(True)

    leaderboard2.append({
        'username': username,
        'payload': payload,
        'characters': payload_length,
        'passed_requirements': passed_requirements,
        'results': resultsx
    })

    store_payload(username, payload, resultsx)
    leaderboard2.sort(key=lambda x: (-x['passed_requirements'], x['characters']))


# Route to display the submission form
@app.route('/')
def index():
    return render_template('form.html')


# Route to handle the form submission
@app.route('/submit', methods=['POST'])
def submit():
    username = request.form.get('name')
    payload = request.form.get('payload')

    # Evaluate the payload and update the leaderboard
    evaluate_payload(username, payload)

    # Redirect to the leaderboard page
    return redirect(url_for('leaderboard_page'))


# Route to display the leaderboard
@app.route('/leaderboard')
def leaderboard_page():  # Renamed the function to avoid conflict
    return render_template('leaderboard.html', leaderboard=leaderboard2, enumerate=enumerate, req=requirements)


# Additional routes for static pages
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/about2')
def about2():
    return render_template('about2.html')


@app.route('/where2learn')
def where2learn():
    return render_template('where2learn.html')


if __name__ == '__main__':
    app.run(debug=True)
