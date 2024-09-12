from flask import Flask, render_template, request, redirect, url_for
import re
import json

import pdb

app = Flask(__name__)

# Store the user submissions and results in memory
leaderboard2 = []  # Renamed leaderboard2 to avoid any confusion

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

# Function to evaluate the payload based on the defined requirements
def evaluate_payload(username, payload):
    # Count the number of characters in the payload
    payload_length = len(payload)
    
# Evaluate the payload for each requirement
    resultsx = []
    for requirement in requirements:
        # Check for custom checks
        if 'custom_check' in requirement:
            if requirement['custom_check'] == 'check_payload_length':
                resultsx.append(payload_length <= 1024)  # Pass if the payload is within the limit
            elif requirement['custom_check'] == 'check_network_requests':
                # Disable network requests (check for fetch(), XMLHttpRequest(), or <img>)
                if re.search(r'fetch\(|XMLHttpRequest\(|<img ', payload):
                    resultsx.append(False)  # Fail if network requests are found
                else:
                    resultsx.append(True)  # Pass if no network requests are made
        # Otherwise, use the pattern matching logic
        elif re.search(requirement['pattern'], payload):
            if 'fail_if_matches' in requirement:
                resultsx.append(False)  # Fail if condition is met
            else:
                resultsx.append(True)  # Pass if pattern is found
        else:
            resultsx.append(False)  # Fail if pattern is not found


    # Ensure that the length of results matches the number of requirements
    assert len(resultsx) == len(requirements), "Mismatch between results and requirements"
    

    # # Ensure that the results list matches the length of the requirements list
    # if len(resultsx) != len(requirements):
    #     print(f"Warning: Results length ({len(resultsx)}) does not match requirements length ({len(requirements)}).")

    
    # # Count how many times alert() is triggered in the payload
    # alert_matches = re.findall(r'alert\(\)', payload)
    # if len(alert_matches) >= 2:
    #     resultsx.append(True)  # Triggered in 2+ contexts
    # else:
    #     resultsx.append(False)
    
    # # Check payload length
    # if payload_length > 1024:
    #     resultsx.append(False)  # Payload exceeds character limit
    # else:
    #     resultsx.append(True)
    
    # Calculate the number of requirements met
    passed_requirements = resultsx.count(True)
    
    # Add the result to the leaderboard
    leaderboard2.append({
        'username': username,
        'payload': payload,
        'characters': payload_length,
        'passed_requirements': passed_requirements,
        'results': resultsx
    })
    
    # Store payload in file for future reference
    store_payload(username, payload, resultsx)
    
    # Sort the leaderboard by the number of passed requirements, then by payload length
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
def leaderboard_page():  # Renamed the function to leaderboard_page to avoid conflict
    #pdb.set_trace()
    return render_template('leaderboard.html', leaderboard=leaderboard2, enumerate=enumerate, req = requirements)

if __name__ == '__main__':
    app.run(debug=True)
