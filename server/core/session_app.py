# server.py
from flask import Flask, request, jsonify
from .agent_session import Session
from .verify import ApiVerify, AgentVerify
import requests
from ..utils.db_utils import DynamoDBClient
from .generate_api_key import APIKeyManager
from dotenv import load_dotenv
import os
from .get_agents import AgentResponseParser

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
            return jsonify({"error": f"Multi-agent with name {multi_agent_main_name} already exists. Please check your dashboard for the respective agent-id"}), 403
        
        
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
    
    
@app.route("/agent_info", methods=["POST"])
def get_agents_info():
    try:
        data = request.json
        api_key, user_id = data.get("api_key"), data.get("user_id")
        
        if not api_key or not user_id:
            return jsonify({"status": "error", "message": "api_key and user_id required"}), 400

        if not ApiVerify(dynamo, os.getenv("API_TABLE")).verify(api_key):
            return jsonify({"status": "error", "message": "Invalid API key"}), 403
        else:
            print("-----API Key Verified------")
        
        response = dynamo.get_item_by_column(os.getenv("AGENT_TABLE"), "user_id", {"user_id": {"N": str(user_id)}})
        if not response:
            return jsonify({"status": "error", "message": f"No agents found for user_id {user_id}"}), 404
        
        return jsonify({"status": "success", "data": {"user_id": user_id, "agents": AgentResponseParser(response).get_id_agent_mapping()}}), 200
        
    except KeyError as e:
        return jsonify({"status": "error", "message": f"Data structure error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500
    
    
@app.route("/query", methods=["POST"])
def process_query():
    try:
        # Get data from request
        data = request.json
        query = data.get("query")
        agent_id = data.get("agent_id")

        # Validate required fields
        if not all([query, agent_id]):
            return jsonify({
                "status": "error",
                "message": "query, api_key, user_id, and agent_id are required."
            }), 400


        # Get both target API URLs from environment variables
        target_api_url_1 = os.getenv("QUERY_API_URL_1")
        target_api_url_2 = os.getenv("QUERY_API_URL_2")
        
        if not all([target_api_url_1, target_api_url_2]):
            return jsonify({
                "status": "error",
                "message": "Target API URLs not properly configured"
            }), 500

        # Prepare request payload - only sending query and agent_id
        payload = {
            "query": query,
            "agent_id": agent_id
        }
        headers = {
            "Content-Type": "application/json"
        }

        # Try first API
        try:
            response1 = requests.post(
                target_api_url_1,
                json=payload,
                headers=headers
            )
            
            if response1.status_code == 200:
                response_data = response1.json()
                if response_data is not None:
                    return jsonify({
                        "status": "success",
                        "data": response_data,
                        "source": "api_1"
                    }), 200

            # If first API returns None or fails, try second API
            response2 = requests.post(
                target_api_url_2,
                json=payload,
                headers=headers
            )
            
            if response2.status_code == 200:
                response_data = response2.json()
                if response_data is not None:
                    return jsonify({
                        "status": "success",
                        "data": response_data,
                        "source": "api_2"
                    }), 200

            # If both APIs return None or fail
            return jsonify({
                "status": "error",
                "message": "No response from either API"
            }), 404

        except requests.RequestException as e:
            return jsonify({
                "status": "error",
                "message": f"Failed to process query: {str(e)}"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

    


    

    

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
    app.run(host='0.0.0.0', port=3001, debug=True)
