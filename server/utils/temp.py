#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  8 20:38:41 2025

@author: krishnayadav
"""

# def extract_field(data: dict, field: str) -> list:
#     """
#     Extracts values of a specified field from the given dictionary.
    
#     :param data: Dictionary containing items.
#     :param field: The field to extract values for.
#     :return: List of values corresponding to the specified field.
#     """
#     items = data.get("Items", [])
    
#     extracted_values = []
#     for item in items:
#         if field in item:
#             value_dict = item[field]
#             # Extract the actual value based on its type
#             if "S" in value_dict:
#                 extracted_values.append(value_dict["S"])
#             elif "N" in value_dict:
#                 extracted_values.append(int(value_dict["N"]))
#             elif "BOOL" in value_dict:
#                 extracted_values.append(value_dict["BOOL"])
    
#     return extracted_values

# result = {'Items': [{'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '3'}, 'date_created': {'S': '2025-02-08 18:46:13'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent'}}, {'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '2'}, 'date_created': {'S': '2025-02-08 18:45:52'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent1'}}, {'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '4'}, 'date_created': {'S': '2025-02-08 18:53:58'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent'}}, {'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '6'}, 'date_created': {'S': '2025-02-08 18:57:39'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent'}}, {'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '1'}, 'date_created': {'S': '2025-02-08 18:41:05'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent'}}, {'user_id': {'N': '123'}, 'is_active': {'BOOL': True}, 'id': {'N': '5'}, 'date_created': {'S': '2025-02-08 18:55:37'}, 'agent_list': {'S': 'binance/web-search'}, 'agent_main_name': {'S': 'meta-agent'}}], 'Count': 6, 'ScannedCount': 7, 'ResponseMetadata': {'RequestId': 'A4VOTP4JIHOHTF9E302DL6VR37VV4KQNSO5AEMVJF66Q9ASUAAJG', 'HTTPStatusCode': 200, 'HTTPHeaders': {'server': 'Server', 'date': 'Sat, 08 Feb 2025 13:33:00 GMT', 'content-type': 'application/x-amz-json-1.0', 'content-length': '1149', 'connection': 'keep-alive', 'x-amzn-requestid': 'A4VOTP4JIHOHTF9E302DL6VR37VV4KQNSO5AEMVJF66Q9ASUAAJG', 'x-amz-crc32': '373122216'}, 'RetryAttempts': 0}}
# key = 'agent_main_name'

# agent_list = extract_field(result, key)