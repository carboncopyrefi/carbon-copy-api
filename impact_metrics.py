import utils, requests, keys, external, utils, config
from flask import current_app as app, json
from urllib.request import urlopen
from dune_client.client import DuneClient
from collections import defaultdict
from datetime import datetime

baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_company_impact_metric = config.BASEROW_TABLE_COMPANY_IMPACT_METRIC
baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA
date_format = config.DATE_FORMAT

# Dune initialization
dune = DuneClient(keys.DUNE_KEY)

def update_impact_metrics():
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
                    value = float(query.result.rows[int(metric['result_index'])][metric['result_key']])
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
                    for metric in impact['metrics']:
                        metric_name = metric['db_id']
                        api = impact['api'] + metric['query']
                        response = requests.get(api)
                        date = utils.get_formatted_date()
                        value = response.json()
                        if type(value) == dict:
                            value = value[metric['result_key']]
                        if metric['denominator'] is not None:
                            value = response.json() / int(metric['denominator'])
                       
                        i = {"Impact Metric": metric_name, "Value": value, "Date": date}

                        metric_list.append(i)
                
                else:
                    pass
            
            else:
                pass

    try:
        row = requests.post(
            "https://api.baserow.io/api/database/rows/table/349685/batch/?user_field_names=true",
            headers={
                'Authorization': keys.IMPACT_METRICS_BASEROW_TOKEN,
                'Content-Type': 'application/json'
            },
            json={
                "items": metric_list
            }
        )
    except:
        return "Could not update metrics", 500

    return row.json()

def get_dashboard_data():
    impact_params = "filter_type=OR&filter__field_2606412__has_value_equal=climate-impact-grant-amount&filter__field_2606412__has_value_equal=climate-impact-grant-number"
    impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)

    grouped_data = defaultdict(list)
    date_grouped_data = defaultdict(list)
    metric_list = []
    item_list = []
    cumulative_value = 0
    series_name = None
    

    for item in sorted(impact_data['results'], key=lambda i: i['Date']):
        if item['Chart'][0]['value'] == True:  
            impact_metric_date = item['Date']
            date_grouped_data[impact_metric_date].append(item)
            
            if series_name is None:
                series_name = item['Name'][0]['value']
       
        # For aggregate data
        impact_metric_key = item['Key'][0]['value']
        grouped_data[impact_metric_key].append(item)

    for metric_date, items in date_grouped_data.items():
        chart_metric_value = 0

        for item in items:
            chart_metric_value += float(item['Value'])  

        cumulative_value += chart_metric_value        
        
        item_list.append({"x": item['Date'], "y": round(cumulative_value,2)})

    for metric_key, items in grouped_data.items():
        metric_value = 0
        metric_name = None
        metric_unit = None
        metric_format = None

        for item in items:
            metric_value += float(item['Value'])
            if metric_name is None:
                metric_name = item['Name'][0]['value']
                metric_unit = item['Unit'][0]['value']
                metric_format = item['Format'][0]['value']['value']
                metric_date = datetime.now()
                formatted_date = metric_date.strftime(date_format)
        
        metric_list.append(vars(external.Impact(None,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, "numeric")))

    sorted_item_list = sorted(item_list, key=lambda d: d['x'])

    result = {
        "grants": {
            "aggregate": metric_list,
            "list": {
                "name": series_name,
                "data": sorted_item_list
            }    
        }
    }

    return result