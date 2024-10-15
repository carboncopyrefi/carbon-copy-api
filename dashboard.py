from collections import defaultdict
import utils, config
from datetime import datetime

baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA
baserow_table_company = config.BASEROW_TABLE_COMPANY
date_format = config.DATE_FORMAT

class DashboardMetric():
    def __init__(self, key, name, value, unit, date, value_details, metric_details, projects):
        self.key = key
        self.name = name
        self.value = value
        self.unit = unit
        self.date = date
        self.value_details = value_details 
        self.metric_details = metric_details
        self.projects = projects

def aggregate_latest_cumulative_metric_values(group):
    group.sort(key=lambda x: datetime.strptime(x['Date'], '%Y-%m-%d'), reverse=True)
    latest_date = group[0]['Date']
    # Filter and aggregate metric_values for items with the latest date
    latest_items = [float(item['Value']) for item in group if item['Date'] == latest_date]
    return {"date": latest_date, "sum": sum(latest_items)}    

def get_dashboard_data():
    page_size = "200"
    impact_params = "size=" + page_size + "&order_by=-Date"
    impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)
    impact_records = impact_data['results']

    if impact_data['count'] > int(page_size):
        impact_params += "&page=2"
        impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)
        for impact_data in impact_data['results']:
            impact_records.append(impact_data)

    grouped_data = defaultdict(list)
    metric_list = []
    series_name = None
    chart_list = []

    for item in impact_records: 
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
        project_list = []

        for i in items:
            if i['Company'][0]['value'] not in project_list:
                project_list.append(i['Company'][0]['value'])

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
            latest_value = aggregate_latest_cumulative_metric_values(items)
            metric_value = latest_value['sum']
            metric_date = datetime.strptime(latest_value['date'],"%Y-%m-%d")
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
                    cumulative_chart_value = 0
                    for cumulative_item in i:
                        cumulative_chart_value += float(cumulative_item['Value'])
                    
                    item_list.append({"x": cumulative_item['Date'], "y": round(cumulative_chart_value, 2)})

            chart_list.append({"series": metric_name, "data": item_list, "key": metric_key})

        metric_list.append(vars(DashboardMetric(metric_key,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, project_list)))

    result = {
        "aggregate": metric_list,
        "list": chart_list
    }

    return result