# server.py
from flask import Flask, request, jsonify
from .agent_session import Session
from .verify import ApiVerify, AgentVerify
import requests
from ..utils.db_utils import DynamoDBClient
from .generate_api_key import APIKeyManager
from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)

dynamo = DynamoDBClient()

@app.route("/create_api_key", methods=["POST"])
def create_api_key():
    try:
        data = request.json
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required."}), 400

        # Generate API key
        api_key_manager = APIKeyManager(dynamo, os.getenv("API_TABLE"))
        new_api_key = api_key_manager.create_api_key(user_id)

        return jsonify({"api_key": new_api_key}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create_session", methods=["POST"])
def create_session():
    try:
        # Parse the incoming JSON data
        data = request.json
        print(data.get("character_file"))
        

        # Extract characterJson and api_key from the payload
        character_json = data.get("character_file")
        api_key = data.get("api_key")
        env_json = data.get("env_json")
        multi_agent_main_name = data.get("multi_agent_main_name")
        multiple_agents_name = data.get("multiple_agents_name")

        # Validate required fields
        if not (character_json and api_key):
            return jsonify({"error": "characterJson and api_key are required."}), 400

        # Verify the API key
        verify_obj = ApiVerify(dynamo, os.getenv("API_TABLE"))
        if not verify_obj.verify(api_key):
            return jsonify({"error": "Invalid API key."}), 403
        
        print("--------- API Key verified ---------")

        
        agent_verify_obj = AgentVerify(dynamo, os.getenv("AGENT_TABLE"))
        agent_exist = agent_verify_obj.verify_agent_name(multi_agent_main_name, api_key, multiple_agents_name)
        print("### ", agent_exist)
        if agent_exist:
            return jsonify({"error": f"Multi-agent with name {multi_agent_main_name} already exists."}), 403
        
        
        # Prepare the payload for the external API (only characterJson)
        payload = {
            "characterJson": character_json
        }
        
        print(character_json)
        # Make a POST request to the predefined URL
        eliza_start_url = os.getenv("ELIZA_CREATE")
        print(eliza_start_url)
        
        #
        response = requests.post(eliza_start_url, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            return jsonify(response.json()), 201
        else:
            return jsonify({"error": "Failed to create session on external server.", "details": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route("/close_session", methods=["POST"])
# def close_session():
#     try:
#         data = request.json
#         api_key = data.get("api_key")

#         if not api_key:
#             return jsonify({"error": "api_key is required."}), 400

#         session = Session(None, None, api_key)
#         result = session.close_session()
#         return jsonify(result), 200

#     except FileNotFoundError as e:
#         return jsonify({"error": str(e)}), 404
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Ensure the sessions directory exists
    if not os.path.exists("sessions"):
        os.makedirs("sessions")

    app.run(debug=True)
