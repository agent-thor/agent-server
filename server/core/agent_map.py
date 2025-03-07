class AgentToolMapper:
    def __init__(self, dynamo, table_name):
        self.dynamo = dynamo
        self.table_name = table_name

    def save_agent_tool_mapping(self, multi_agent_main_name, eliza_response, tools_response, api_key):
        try:
            eliza_agent_id = eliza_response.json().get('id')
            tools_agent_id = tools_response.json().get('unique_id')

            if not eliza_agent_id or not tools_agent_id:
                raise ValueError("Invalid response: Missing agent IDs")

            item = {
                "multi_agent_main_name" : {"S": str(multi_agent_main_name)},
                "agent_id": {"S": str(eliza_agent_id)},
                "tools_agent_id": {"S": str(tools_agent_id)}
            }

            self.dynamo.add_item(self.table_name, item)
            print(f"--- Agent and tools ID for api_key {api_key} written to DB ---")

            return {"status": "success", "message": "Agent and tools mapping saved"}

        except Exception as e:
            return {"status": "error", "message": f"Failed to save mapping: {str(e)}"}
