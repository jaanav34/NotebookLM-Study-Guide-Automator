from flask import Flask, request, jsonify
from notebook_automator import query_notebook
import asyncio

# Initialize the Flask application
app = Flask(__name__)

# Define the API endpoint. It will listen for POST requests at http://localhost:5000/query
@app.route('/query', methods=['POST'])
def handle_query():
    """
    Handles incoming questions, calls the scraper, and returns the answer.
    """
    # 1. Get the question from the incoming request's JSON data
    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({"error": "No question provided in the request body."}), 400

    question = data['question']
    print(f"Received question via API: '{question}'")

    try:
        # 2. Run the asynchronous query_notebook function
        # asyncio.run() is a simple way to execute an async function from a sync one.
        response = asyncio.run(query_notebook(question))
        
        # 3. Return the scraped response as JSON
        print(f"Sending response: '{response[:100]}...'") # Log the first 100 chars
        return jsonify({"response": response})

    except Exception as e:
        # If anything goes wrong in the scraper, return a server error
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An internal error occurred: {e}"}), 500

def main():
    """
    Main function to start the Flask server.
    """
    print("--- Starting Flask Server for NotebookLM Teleprompter ---")
    print("The server is running and listening for requests at http://localhost:5000/query")
    print("Press CTRL+C to stop the server.")
    # 'host="0.0.0.0"' makes the server accessible from other devices on your network.
    # 'port=5000' is the standard port for Flask development.
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()

