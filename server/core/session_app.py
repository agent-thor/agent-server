import sys
import os
# Add the server directory to Python path
server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(server_dir)

# server.py
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from server.core.agent_session import Session
from server.core.verify import ApiVerify, AgentVerify
import requests
from server.utils.db_utils import DynamoDBClient
from server.core.generate_api_key import APIKeyManager
from server.core.get_agents import AgentResponseParser
from server.core.agent_map import AgentToolMapper
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

app = FastAPI(title="Agent API Server")

dynamo = DynamoDBClient()

# Define Pydantic models for request validation
class CreateAPIKeyRequest(BaseModel):
    user_id: str

class CreateSessionRequest(BaseModel):
    character_file: Dict[str, Any]
    api_key: str
    env_json: Optional[Dict[str, Any]] = None
    multi_agent_main_name: Optional[str] = None
    multiple_agents_name: Optional[str] = None

class AgentInfoRequest(BaseModel):
    api_key: str
    user_id: str

class QueryRequest(BaseModel):
    query: str
    agent_name: str

@app.post("/create_api_key", status_code=201)
async def create_api_key(request: CreateAPIKeyRequest):
    try:
        # Generate API key
        api_key_manager = APIKeyManager(dynamo, os.getenv("API_TABLE"))
        new_api_key = api_key_manager.create_api_key(request.user_id)

        return {"api_key": new_api_key}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_session", status_code=201)
async def create_session(request: CreateSessionRequest):
    try:
        # Extract data from the validated request
        character_json = request.character_file
        api_key = request.api_key
        env_json = request.env_json
        multi_agent_main_name = request.multi_agent_main_name
        multiple_agents_name = request.multiple_agents_name

        print(character_json)  # Log character file

        # Verify the API key
        verify_obj = ApiVerify(dynamo, os.getenv("API_TABLE"))
        if not verify_obj.verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key.")
        
        print("--------- API Key verified ---------")

        agent_verify_obj = AgentVerify(dynamo, os.getenv("AGENT_TABLE"))
        agent_exist = agent_verify_obj.verify_agent_name(multi_agent_main_name, api_key, multiple_agents_name)
        print("### ", agent_exist)
        if agent_exist:
            raise HTTPException(
                status_code=403, 
                detail=f"Multi-agent with name {multi_agent_main_name} already exists. Please check your dashboard for the respective agent-id"
            )
        
        # Prepare the payload for the external API (only characterJson)
        payload = {"characterJson": character_json}
        tools_payload = {"api_keys": env_json}

        # Get environment variables for URLs
        eliza_start_url = os.getenv("ELIZA_CREATE")
        tools_url = os.getenv("TOOLS_SET")

        # Validate if URLs exist
        if not eliza_start_url or not tools_url:
            raise HTTPException(status_code=500, detail="Missing required environment variables")

        # Make API requests
        eliza_response = requests.post(eliza_start_url, json=payload)
        print(f"eliza response: {eliza_response.json()}")

        print("\n\n tools payload", tools_payload)

        tools_response = requests.post(tools_url, json=tools_payload)
        print(f"\n\n tools response: {tools_response.json()}")
        
        mapper = AgentToolMapper(dynamo, "agent_tool_id")
        print("\n\n", eliza_response.status_code, tools_response.status_code)


        if tools_response.status_code and eliza_response.status_code == 200: 
            # Save the agent and other tools mapping in DB
            agent_verify_obj.save_agent_to_db(multi_agent_main_name, api_key, multiple_agents_name)
            #save the eliza and extra tools agent id in DB
            response = mapper.save_agent_tool_mapping(multi_agent_main_name, eliza_response, tools_response, api_key)
        
        # Check if both requests were successful
        if eliza_response.status_code == 200 and tools_response.status_code == 200:
            return {
                "eliza_response": eliza_response.json(),
                "tools_response": tools_response.json(),
                "multi_agent_name": multi_agent_main_name
            }
        
        elif eliza_response.status_code != 200 or tools_response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Either of agents failed to create among {multiple_agents_name}",
                    "eliza_details": eliza_response.text if eliza_response.status_code != 200 else None,
                    "tools_details": tools_response.text if tools_response.status_code != 200 else None
                }
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Failed to create session on external server.",
                    "eliza_details": eliza_response.text if eliza_response.status_code != 200 else None,
                    "tools_details": tools_response.text if tools_response.status_code != 200 else None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/agent_info")
async def get_agents_info(request: AgentInfoRequest):
    try:
        api_key, user_id = request.api_key, request.user_id
        
        if not ApiVerify(dynamo, os.getenv("API_TABLE")).verify(api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")
        else:
            print("-----API Key Verified------")
        
        response = dynamo.get_item_by_column(os.getenv("AGENT_TABLE"), "user_id", {"user_id": {"N": str(user_id)}})
        if not response:
            raise HTTPException(status_code=404, detail=f"No agents found for user_id {user_id}")
        
        return {
            "status": "success", 
            "data": {
                "user_id": user_id, 
                "agents": AgentResponseParser(response).get_id_agent_mapping()
            }
        }
        
    except HTTPException:
        raise
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Data structure error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        # Get data from request
        query = request.query
        agent_name = request.agent_name
        function_name = request.function_name
        
        primary_key = {"multi_agent_main_name": {"S": agent_name}}
        response = dynamo.get_item("agent_tool_id", primary_key)
        
        agent_id = response['eliza_agent_id']['S']
        print(f"agent name:{agent_name}, agent id : {agent_id}")

        # Get both target API URLs from environment variables
        eliza_address = os.getenv("ELIZA_QUERY")  # eliza
        if not eliza_address:
            raise HTTPException(status_code=500, detail="Target API URLs not properly configured")
            
        eliza_address = eliza_address + agent_id + '/message'    
        print("target_api_url1", eliza_address)

        # Prepare request payload - only sending query and agent_id
        payload = {
            "text": query,
            "user": "user"
        }
        headers = {
            "Content-Type": "application/json"
        }

        # Try API
        try:
            response1 = requests.post(
                eliza_address,
                json=payload,
                headers=headers
            )
            
            if response1.status_code == 200:
                response_data = response1.json()
                if response_data is not None:
                    return {
                        "status": "success",
                        "data": response_data,
                        "source": "api_1"
                    }

            # If API returns None or fails
            raise HTTPException(status_code=404, detail="No response from API")

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Uncomment if you need to implement close_session
# class CloseSessionRequest(BaseModel):
#     api_key: str
#
# @app.post("/close_session")
# async def close_session(request: CloseSessionRequest):
#     try:
#         api_key = request.api_key
#
#         session = Session(None, None, api_key)
#         result = session.close_session()
#         return result
#
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Ensure the sessions directory exists
    import os
    if not os.path.exists("sessions"):
        os.makedirs("sessions")
    
    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host='0.0.0.0', port=3001)