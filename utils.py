import requests
from flask import json
from collections import defaultdict

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
    
def get_coingecko_data(token_ids):

    api = "https://api.coingecko.com/api/v3/coins/markets?ids=" + token_ids + "&vs_currency=usd"
    response = requests.get(api)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Coingecko data with status {response.status_code}. {response.text}")
    
def get_coingeckoterminal_data(network, token_id):

    api = "https://api.geckoterminal.com/api/v2/networks/" + network + "/tokens/" + token_id
    response = requests.get(api)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Coingecko Terminal data with status {response.status_code}. {response.text}")

def execute_graphql_query(query):
    response = requests.post(gitcoin_graphql, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run with a {response.status_code}. {response.text}")
    
def calculate_dict_sums(data):
    year_round_sums = defaultdict(float)

    for entry in data:
        key = (entry['year'], entry['round'])
        year_round_sums[key] += float(entry['amount'])
        
    year_round_sums = dict(year_round_sums)

    json_compatible_sums = [
        {"round": f"{year} {round}", "amount": '{:,.2f}'.format(amount)} for (year, round), amount in year_round_sums.items()
    ]

    json_compatible_sums.sort(key=lambda x: x["round"], reverse=True)

    return json_compatible_sums