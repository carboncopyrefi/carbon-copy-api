import requests
from flask import json

baserow_api = "https://api.baserow.io/api/database/rows/table/"
baserow_token = 'Token RPlLXKDgBX8TscVGjKjI33djLk89X1qf'

gitcoin_graphql = "https://grants-stack-indexer-v2.gitcoin.co/graphql"

def get_baserow_data(table_id, params):
    url = baserow_api + table_id + "/?user_field_names=true&" + params
    headers = {
        'Authorization': baserow_token,
        'Content-Type' : 'application/json'

    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Baserow data with status {response.status_code}. {response.text}")
    

def execute_graphql_query(query):
    response = requests.post(gitcoin_graphql, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run with a {response.status_code}. {response.text}")