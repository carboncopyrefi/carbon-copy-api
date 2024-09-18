from collections import defaultdict
import utils, requests, keys, external, config
from datetime import datetime

baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA
date_format = config.DATE_FORMAT

def aggregate_latest_cumulative_metric_values(group):
    group.sort(key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), reverse=True)
    latest_date = group[0]['Date']
    # Filter and aggregate metric_values for items with the latest date
    latest_items = [float(item['Value']) for item in group if item['Date'] == latest_date]
    return sum(latest_items)

def get_dashboard_data():
    impact_params = "size=200"
    impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)

    grouped_data = defaultdict(list)
    metric_list = []
    series_name = None
    chart_list = []

    for item in impact_data['results']: 
        # Group all of the data by key
        if item['Key'][0]['value'] is not None:
            impact_metric_key = item['Key'][0]['value']['value']
            grouped_data[impact_metric_key].append(item)
        else:
            pass

    for metric_key, items in grouped_data.items():
        metric_value = 0
        metric_name = None
        metric_unit = None
        metric_format = None
        cumulative_value = 0
        date_grouped_data = defaultdict(list)

        if items[0]['Type'][0]['value']['value'] == "Single":
            for item in sorted(items, key=lambda x: x['Date'], reverse=True):          
                metric_value += float(item['Value'])
                if metric_name is None:
                    metric_name = item['Name'][0]['value']
                    metric_unit = item['Unit'][0]['value']
                    metric_format = item['Format'][0]['value']['value']
                    metric_date = datetime.now()
                    formatted_date = metric_date.strftime(date_format)

        if items[0]['Type'][0]['value']['value'] == "Cumulative":
            metric_value = aggregate_latest_cumulative_metric_values(items)
            metric_date = datetime.now()
            formatted_date = metric_date.strftime(date_format)
            metric_name = items[0]['Name'][0]['value']
            metric_unit = items[0]['Unit'][0]['value']
            metric_format = items[0]['Format'][0]['value']['value']

        if items[0]['Chart'][0]['value'] == True: 
            item_list = []
            for item in sorted(items, key=lambda x: x['Date']):
                impact_metric_date = item['Date']
                date_grouped_data[impact_metric_date].append(item)

            if series_name is None:
                series_name = items[0]['Name'][0]['value']

            for metric_date, i in date_grouped_data.items():
                if i[0]['Type'][0]['value']['value'] == "Single":
                    chart_metric_value = 0
                    for single_item in i:     
                        chart_metric_value += float(single_item['Value']) 

                    cumulative_value += chart_metric_value
                    item_list.append({"x": single_item['Date'], "y": round(cumulative_value,2)})

                if i[0]['Type'][0]['value']['value'] == "Cumulative":
                    for cumulative_item in i:
                        item_list.append({"x": cumulative_item['Date'], "y": round(float(cumulative_item['Value']),2)})

            chart_list.append({"series": metric_name, "data": item_list})

        metric_list.append(vars(external.Impact(None,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, "numeric")))

    result = {
        "aggregate": metric_list,
        "list": chart_list   
    }

    return result