import utils, requests, keys, config, base64, binascii, regen_pb2
from flask import json
from urllib.request import urlopen
from dune_client.client import DuneClient

baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_company_impact_metric = config.BASEROW_TABLE_COMPANY_IMPACT_METRIC
baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA
date_format = config.DATE_FORMAT

# Dune initialization
dune = DuneClient(keys.DUNE_KEY)

metric_list = []
params = "filter__field_2405062__not_empty&include=Impact Metrics JSON"
impact_data = utils.get_baserow_data(baserow_table_company, params)

for json_file in impact_data['results']:
    json_url = json_file['Impact Metrics JSON'][0]['url']
    response = urlopen(json_url)
    data = json.loads(response.read())

    for impact in data['impact_data']:
        if impact['source'] == "dune":
            for metric in impact['metrics']:
                metric_name = metric['db_id']
                date = utils.get_formatted_date()
                query = dune.get_latest_result(metric['query'], max_age_hours=int(metric['max_age']))
                value = round(float(query.result.rows[int(metric['result_index'])][metric['result_key']]), 2)
                if metric['denominator'] is not None:
                    value = value / int(metric['denominator'])
                
                i = {"Impact Metric": metric_name, "Value": value, "Date": date}

                metric_list.append(i)
                
        if impact['source'] == "client":
            if impact['method'] == "POST":
                post_body_json = json.dumps(impact['body'])
                post_body = json.loads(post_body_json)
                response = requests.post(impact['api'], json=post_body)
                metric_data = response.json()[impact['result_key']][impact['result_index']]

                for metric in impact['metrics']:
                    metric_name = metric['db_id']
                    date = utils.get_formatted_date()
                    value = metric_data[metric['result_key']]
                    formatted_value = round(float(value) / impact['global_denominator'], 2) if impact['global_operator'] == "divide" else round(float(value), 2)
                    if metric['operator'] == "multiply":
                        formatted_value = round(formatted_value * metric['denominator'], 2)
                    if metric['operator'] == "divide":
                        formatted_value = round(formatted_value / metric['denominator'], 2)

                    i = {"Impact Metric": metric_name, "Value": formatted_value, "Date": date}

                    metric_list.append(i)

            if impact['method'] == "GET":
                date = utils.get_formatted_date()

                if impact['result_key'] is not None:
                    response = requests.get(impact['api'])
                    for metric in impact['metrics']:
                        metric_name = metric['db_id']
                        value_path = impact['result_key'] + "." + metric['result_key']
                        value = round(float(utils.get_nested_value(response.json(), value_path)), 2)
                        if metric['denominator'] is not None:
                            value = value / int(metric['denominator'])
                    
                        i = {"Impact Metric": metric_name, "Value": value, "Date": date}

                        metric_list.append(i)
                else:
                    for metric in impact['metrics']:
                        metric_name = metric['db_id']
                        api = impact['api'] + metric['query']
                        response = requests.get(api)                           
                        value = response.json()
                        if type(value) == dict:
                            value = value[metric['result_key']]
                        if metric['denominator'] is not None:
                            value = response.json() / int(metric['denominator'])
                    
                        i = {"Impact Metric": metric_name, "Value": value, "Date": date}

                        metric_list.append(i)
            
            else:
                pass
        
        if impact['source'] == "subgraph":
            date = utils.get_formatted_date()
            for metric in impact['metrics']:
                metric_name = metric['db_id']
                cumulative_value = 0
                base_url = impact['api'].replace('{api_key}',keys.SUBGRAPH_API_KEY)
                for q in metric['query']:
                    api = base_url + q
                    response = requests.post(api, json={'query': metric["graphql"]})
                    if response.status_code == 200:
                        result = response.json()['data'][impact['result_key']]
                        for r in result:
                            if r['key'] == metric['result_key']:
                                cumulative_value += float(r['value'])
        
                i = {"Impact Metric": metric_name, "Value": cumulative_value, "Date": date}

                metric_list.append(i)

        if impact['source'] == "regen":
            date = date = utils.get_formatted_date()
            denom_list = []
            hex_denom_list = []
            cumulative_retired_amount = 0
            bridged_amount = 0
            onchain_issued_amount = 0

            row = requests.post(
                impact['api'],
                headers={
                    'Content-Type': 'application/json'
                },
                json={
                    'jsonrpc':'2.0',
                    'id':176347957138,
                    'method':'abci_query',
                    'params':{
                        'path':'/regen.ecocredit.v1.Query/Batches',
                        'prove':False
                    }
                }
            )

            value = row.json()['result']['response']['value']

            decoded_bytes = base64.b64decode(value)

            message = regen_pb2.QueryBatchesResponse()
            message.ParseFromString(decoded_bytes)

            for batch in message.batches:
                denom_list.append(batch.denom)

            for denom in denom_list:
                byte_denom = denom.encode("utf-8")
                length_hex = hex(len(denom))[2:].zfill(2)
                prefix = "0a" + length_hex
                hex_denom = prefix + binascii.hexlify(byte_denom).decode('utf-8')
                hex_denom_list.append({"hex": hex_denom, "string": denom})

            for item in hex_denom_list:
                result = requests.post(
                    impact['api'],
                    headers={
                        'Content-Type': 'application/json'
                    },
                    json={
                        'jsonrpc':'2.0',
                        'id':717212259568,
                        'method':'abci_query',
                        'params':{
                            'path':'/regen.ecocredit.v1.Query/Supply',
                            'data': item['hex'],
                            'prove':False
                        }
                    }
                )

                value = result.json()['result']['response']['value']
                decoded_bytes = base64.b64decode(value)

                message = regen_pb2.QuerySupplyResponse()
                message.ParseFromString(decoded_bytes)

                cumulative_retired_amount += float(message.retired_amount)

                credit_class = item['string'].split("-")[0]

                if credit_class != "KSH01" and credit_class != "C03":
                    bridged_amount += float(message.retired_amount) + float(message.tradable_amount)

                if credit_class == "KSH01":
                    onchain_issued_amount += float(message.retired_amount) + float(message.tradable_amount)

            for metric in impact['metrics']:
                metric_name = metric['db_id']
                if metric['result_key'] == "cumulative_retired_amount":
                    value = cumulative_retired_amount

                if metric['result_key'] == "bridged_amount":
                    value = bridged_amount
                                
                if metric['result_key'] == "onchain_issued_amount":
                    value = onchain_issued_amount                
                
                i = {"Impact Metric": metric_name, "Value": round(value, 2), "Date": date}
                    
                metric_list.append(i)

        if impact['source'] == "near":
            cumulative_value = 0
            date = utils.get_formatted_date()
            post_body_json = json.dumps(impact['body'])
            post_body = json.loads(post_body_json)
            response = requests.post(impact['api'], headers={'Content-Type': 'application/json'}, json=post_body)
            result = response.json()[impact['result_key']][impact['result_index']]
            decoded_response = ''.join([chr(value) for value in result])
            data = json.loads(decoded_response)

            for metric in impact['metrics']:
                metric_name = metric['db_id']
                for item in data:
                    value = float(item[metric['result_key']])

                    if metric['denominator'] is not None:
                        value = value / int(metric['denominator'])

                    if metric['type'] == "cumulative":
                        cumulative_value += value

            i = {"Impact Metric": metric_name, "Value": round(cumulative_value, 2), "Date": date}
            metric_list.append(i)

        else:
            pass

# try:
#     row = requests.post(
#         "https://api.baserow.io/api/database/rows/table/349685/batch/?user_field_names=true",
#         headers={
#             'Authorization': keys.IMPACT_METRICS_BASEROW_TOKEN,
#             'Content-Type': 'application/json'
#         },
#         json={
#             "items": metric_list
#         }
#     )
# except:
#     print("Could not update metrics")

print(metric_list)