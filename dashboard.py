from collections import defaultdict
import utils, config, db
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
    group.sort(key=lambda x:x.date, reverse=True)
    latest_date = group[0].date
    # Filter and aggregate metric_values for items with the latest date
    latest_items = [float(item.value) for item in group if item.date == latest_date]
    return {"date": latest_date, "sum": sum(latest_items)}    

def get_dashboard_data():
    # page_size = "200"
    # impact_params = "size=" + page_size + "&order_by=-Date"
    # impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)
    # impact_records = impact_data['results']

    # if impact_data['count'] > int(page_size):
    #     impact_params += "&page=2"
    #     impact_data = utils.get_baserow_data(baserow_table_company_impact_data, impact_params)
    #     for impact_data in impact_data['results']:
    #         impact_records.append(impact_data)

    impact_records = db.getDashboardData()

    grouped_data = defaultdict(list)
    metric_list = []
    series_name = None
    chart_list = []

    for item in impact_records: 
    # Group all of the data by key
        impact_metric_key = item.metric.key
        grouped_data[impact_metric_key].append(item)

    for metric_key, items in grouped_data.items():
        metric_value = 0
        metric_name = None
        metric_unit = None
        metric_format = None
        cumulative_value = 0
        date_grouped_data = defaultdict(list)
        project_list = []

        for i in items:
            if i.metric.project not in project_list:
                project_list.append(i.metric.project)

        if items[0].metric.type == "Single":
            for item in sorted(items, key=lambda x: x.date, reverse=True):          
                metric_value += float(item.value)
                if metric_name is None:
                    metric_name = item.metric.name
                    metric_unit = item.metric.unit
                    metric_format = item.metric.format
                    metric_date = datetime.now()
                    formatted_date = metric_date.strftime(date_format)

        if items[0].metric.type == "Cumulative":
            latest_value = aggregate_latest_cumulative_metric_values(items)
            metric_value = latest_value['sum']
            metric_date = latest_value['date']
            formatted_date = metric_date.strftime(date_format)
            metric_name = items[0].metric.name
            metric_unit = items[0].metric.unit
            metric_format = items[0].metric.format

        if items[0].metric.chart == "True": 
            item_list = []
            for item in sorted(items, key=lambda x: x.date):
                impact_metric_date = item.date
                date_grouped_data[impact_metric_date].append(item)

            if series_name is None:
                series_name = items[0].metric.name

            for metric_date, i in date_grouped_data.items():
                if i[0].metric.type == "Single":
                    chart_metric_value = 0
                    for single_item in i:     
                        chart_metric_value += float(single_item.value) 

                    cumulative_value += chart_metric_value
                    item_list.append({"x": single_item.date, "y": round(cumulative_value,2)})

                if i[0].metric.type == "Cumulative":
                    cumulative_chart_value = 0
                    for cumulative_item in i:
                        cumulative_chart_value += float(cumulative_item.value)
                    
                    item_list.append({"x": cumulative_item.date, "y": round(cumulative_chart_value, 2)})

            chart_list.append({"series": metric_name, "data": item_list, "key": metric_key})

        metric_list.append(vars(DashboardMetric(metric_key,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, project_list)))

    result = {
        "aggregate": metric_list,
        "list": chart_list
    }

    return result