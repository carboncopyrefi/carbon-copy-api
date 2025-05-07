import requests, keys, config
from flask import json
from collections import defaultdict
from datetime import datetime
from farcaster import Warpcast
from dotenv import load_dotenv

# Farcaster initialization
load_dotenv()
client = Warpcast(mnemonic=keys.WARPCAST_KEY)

baserow_api = "https://api.baserow.io/api/database/rows/table/"
baserow_token = keys.BASEROW_TOKEN
date_format = config.DATE_FORMAT

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
    header = {
        'x_cg_demo_api_key': keys.COINGECKO_KEY
    }
    api = "https://api.coingecko.com/api/v3/coins/markets?ids=" + token_ids + "&vs_currency=usd"
    response = requests.get(api, header)
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

def get_karma_gap_data(karma_slug):

    api = "https://gapapi.karmahq.xyz/projects/" + karma_slug
    response = requests.get(api)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Karma GAP data with status {response.status_code}. {response.text}")

def get_giveth_data(slug):
    query = f"""
        query {{
            projectBySlug(slug:"{ slug }") {{
                id
                totalDonations
                status {{
                    name
                }}
                adminUser {{
                    walletAddress
                }}
            }}
        }}
        """
    api = "https://mainnet.serve.giveth.io/graphql"
    response = requests.post(api, json={'query': query})

    if response.status_code == 200:
        result = response.json()
        total_donations = float(result['data']['projectBySlug']['totalDonations'])
        formatted_total_donations = '{:,.2f}'.format(total_donations)
        formatted_response = {
            "round": "Donations & Matching",
            "amount": formatted_total_donations,
            "funding_type": "Giveth",
            "url": "https://giveth.io/project/" + slug,
            "date": None,
            "year": None
        }
        return formatted_response
    else:
        raise Exception(f"Query failed to run with a {response.status_code}. {response.text}")
    
def get_giveth_qf_fundraising_data(slug):
    f_list = []
    query = f"""
        query {{
            projectBySlug(slug:"{ slug }") {{
                id
                adminUser {{
                    walletAddress
                }}
                qfRounds {{
                    id
                    name
                    endDate
                    isActive
                }}
            }}
        }}
        """

    api = "https://mainnet.serve.giveth.io/graphql"
    response = requests.post(api, json={'query': query})

    if response.status_code == 200:
        result = response.json()
        id = result['data']['projectBySlug']['id']
        qf_rounds = result['data']['projectBySlug']['qfRounds']

        for round in qf_rounds:
            if round['isActive'] == False:
                round_name = round['name']
                round_date = parse_datetime(round['endDate'])
                formatted_round_date = round_date.strftime(date_format)
                round_id = round['id']
                qf_query = f"""
                    query {{
                        getQfRoundHistory(projectId: { id }, qfRoundId: { round_id } ) {{
                            matchingFundAmount
                        }}
                    }}
                    """
                qf_response = requests.post(api, json={'query': qf_query})
                
                if qf_response.status_code == 200:
                    qf_result = qf_response.json()
                    if qf_result['data']['getQfRoundHistory']['matchingFundAmount'] is not None:
                        matching_amount = float(qf_result['data']['getQfRoundHistory']['matchingFundAmount'])
                        formatted_matching_amount = '{:,.2f}'.format(matching_amount)

                        f_item = {
                            "round_id": round_id,
                            "round_name": round_name,
                            "round_date": round_date,
                            "round_display_date": formatted_round_date,
                            "matching_amount": formatted_matching_amount
                        }
                        f_list.append(f_item)
                    else:
                        pass
                    

                    
            else:
                pass

        return f_list
    
    else:
        raise Exception(f"Query failed to run with a {response.status_code}. {response.text}")
    
def calculate_dict_sums(data):
    amounts_by_type = defaultdict(lambda: {'total_amount': 0, 'details': []})

    for entry in data:
        funding_type = entry["funding_type"]
        amount = float(entry["amount"].replace(',', ''))
        amounts_by_type[funding_type]['total_amount'] += amount
        amounts_by_type[funding_type]['details'].append(entry)

    for funding_type in amounts_by_type:
        amounts_by_type[funding_type]['details'].sort(key=lambda x: (x['date'] is None, x['date']), reverse=True)

    grouped_data = [{"funding_type": funding_type, "amount": '{:,.2f}'.format(info['total_amount']), "details": info['details']}
                for funding_type, info in amounts_by_type.items()]

    return grouped_data

def parse_datetime(datetime_str):
    formats = [
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%B %d, %Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Time data '{datetime_str}' does not match any format")

def contact_icon(contact):
    icons = {
        "website": "globe",
        "x": "twitter-x",
        "facebook": "facebook",
        "linkedin": "linkedin",
        "medium": "medium",
        "instagram": "instagram",
        "tiktok": "tiktok",
        "discord": "discord",
        "github": "github",
        "whitepaper": "file-text-fill",
        "blog": "pencil-square",
        "podcast": "broadcast-pin",
        "telegram": "telegram",
        "youtube": "youtube",
        "dao": "bounding-box-circles",
    }
    
    if contact in icons.keys():
        icon = icons[contact]
    
    return icon

def medium_icon(medium):
    icons = {
        "audio": "mic-fill",
        "video": "camera-video-fill",
        "text": "file-text-fill",
    }
    
    if medium in icons.keys():
        icon = icons[medium]
    
    return icon

def cast_to_farcaster(content):
    for item in content['items']:
        if len(item['Headline']) > 1 and len(item['Link']) > 1 and len(item['Snippet']) >1 and item['Display'] is True:
            cast_body = item['Headline'] + "\n\n" + item['Snippet']
            embed = item['Link']

            response = client.post_cast(cast_body, [embed], None, None)

            return response.cast.hash
        else:
            
            return "Ignore", 200        

def get_formatted_date():
    date = datetime.now()
    formatted_date = date.strftime("%Y-%m-%d")

    return formatted_date

def get_nested_value(data, key_path):
    keys = key_path.split('.')  # Split the key path string by dots
    for key in keys:
        data = data.get(key)  # Access the next level in the nested dict
        if data is None:  # If the key doesn't exist, return None
            return None
    return data