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
from .agent_map import AgentToolMapper
from .memory import retrieve_relevant
from .router import AgentRouter
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
        print(data.get("api_key"))
        print(data.get("env_json"))
        print(data.get("multi_agent_main_name"))
        print(data.get("multiple_agents_name"))
        

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
        payload = {"characterJson": character_json}
        tools_payload = {"api_keys": api_key}

        # Get environment variables for URLs
        eliza_start_url = os.getenv("ELIZA_CREATE")
        tools_url = os.getenv("TOOLS_SET")

        print(f"Character JSON: {character_json}")
        print(f"Eliza Start URL: {eliza_start_url}")

        # Validate if URLs exist
        if not eliza_start_url or not tools_url:
            return jsonify({"error": "Missing required environment variables"}), 500

        # Make API requests
        eliza_response = requests.post(eliza_start_url, json=payload)
        print(f"eliza response: {eliza_response.json()}")
        tools_response = requests.post(tools_url, json=tools_payload)
        print(f"tools response: {tools_response.json()}")
        
        mapper = AgentToolMapper(dynamo, "agent_tool_id")

        if eliza_response.status_code == 200:
            agent_verify_obj.save_agent_to_db(multi_agent_main_name, api_key, multiple_agents_name)

            
        if tools_response.status_code == 200: 
            #saving the agnet and other tools mapping in DB.
            response = mapper.save_agent_tool_mapping(multi_agent_main_name, eliza_response, tools_response, api_key)
            
        
        # Check if both requests were successful
        if eliza_response.status_code == 200 and tools_response.status_code == 200:
            return jsonify({
                "eliza_response": eliza_response.json(),
                "tools_response": tools_response.json(),
                "multi_agent_name": multi_agent_main_name
            }), 201
        
        elif eliza_response.status_code != 200 or tools_response!= 200:
            return jsonify({
                "error": f"Either of agents failed to create among {multiple_agents_name}",
                "eliza_details": eliza_response.text if eliza_response.status_code != 200 else None,
                "tools_details": tools_response.text if tools_response.status_code != 200 else None
            }), 400  # Changed to 400 (Bad Request) since it's an external failure

            
        else:
            return jsonify({
                "error": "Failed to create session on external server.",
                "eliza_details": eliza_response.text if eliza_response.status_code != 200 else None,
                "tools_details": tools_response.text if tools_response.status_code != 200 else None
            }), 400  # Changed to 400 (Bad Request) since it's an external failure


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
        agent_name = data.get("agent_name")
        extra_tool_key=data.get("extra_tool_key")
        
        primary_key = {"multi_agent_main_name": {"S": agent_name}}
        response = dynamo.get_item("agent_tool_id", primary_key)
        # response = {'agent_id': {'S': '3fb55a72-6b74-0fbe-b3ae-5d6de38b3616'}, 'multi_agent_main_name': {'S': 'demo4'}, 'tools_agent_id': {'S': 'd5900b5b-8468-46ec-a226-40b6e5a51e71'}}
        
        agent_id = response['agent_id']['S']
        print(f"agent name:{agent_name}, agent id : {agent_id}")

        # Validate required fields
        if not all([query, agent_id]):
            return jsonify({
                "status": "error",
                "message": "query, api_key, user_id, and agent_id are required."
            }), 400


        # Get both target API URLs from environment variables
        eliza_start_url = os.getenv("ELIZA_QUERY") #eliza
        tools_url = os.getenv("TOOLS_QUERY") + agent_id + '/message'    #tools
        print("Eliza start url", eliza_start_url)
        print("Tools start url", tools_url)

        #tools
        tools_url = os.getenv("TOOLS_QUERY") 
        if not all([tools_url]):
            return jsonify({
                "status": "error",
                "message": "Target API URLs not properly configured"
            }), 500

        # get history
        chat_history = dynamo.get_history("agent_tool_id", primary_key)
        print("History list", chat_history)
        relevant_history = retrieve_relevant(query, chat_history)
        prompt="please answer current user query and take help from past interaction if required.\ncurrent query from user : "+query+"\nPAST INTERACTIONS:\n"+relevant_history

        payload = {
            "text": prompt,
            "user": "user"
        }
        payload2={
            "unique_id":extra_tool_key,
            "query":prompt
        }
        headers = {
            "Content-Type": "application/json"
        }
   
        router = AgentRouter(eliza_start_url, tools_url)
        address = router.route_query(query)

        if address == "eliza":
            response = requests.post(
                eliza_start_url,
                json=payload,
                headers=headers
            )
        else:
            response = requests.post(
                tools_url,
                json=payload,
                headers=headers
            )
           
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                except:
                    response_data = None

            
            sav=f"User: {query}\nAI: "+str(response_data[0]["text"])+"\n"+str(response_data["result"])
            chat_history.append(sav)
            if len(chat_history)>20:
                chat_history.pop(0)

            dynamo.update_history("agent_tool_id", primary_key, chat_history)


            return jsonify({
                "status": "success",
                "data1": response_data,
                "extra_tool_response":response_data
            }), 200


    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to analyze query: {str(e)}"
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