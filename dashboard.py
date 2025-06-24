from collections import defaultdict
import utils, config, db
from datetime import datetime

baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA
baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_company_fundraising = config.BASEROW_TABLE_COMPANY_FUNDRAISING
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
    latest_by_metric = {}

    for item in group:
        metric_id = item.metric.id
        current_latest = latest_by_metric.get(metric_id)

        if not current_latest or item.date > current_latest.date:
            latest_by_metric[metric_id] = item

    latest_items = latest_by_metric.values()
    total_sum = sum(float(item.value) for item in latest_items)
    latest_date = max(item.date for item in latest_items)

    return {"date": latest_date, "sum": total_sum}   

def get_dashboard_data():
    chart_list = []
    metric_list = []

# Fundraising data
    metric_key = "venture-capital-amount"
    year_group = defaultdict(list)
    fundraising_cumulative_value = 0
    fundraising_project_list = []

    page_size = "200"
    fundraising_params = "size=" + page_size + "&order_by=-Date&filter__field_2209786__single_select_is_any_of=1686865,1688192"
    fundraising_data = utils.get_baserow_data(baserow_table_company_fundraising, fundraising_params)
    fundraising_records = fundraising_data['results']

    if fundraising_data['count'] > int(page_size):
        fundraising_params += "&page=2"
        fundraising_data = utils.get_baserow_data(baserow_table_company_impact_data, fundraising_params)
        for fundraising_data in fundraising_data['results']:
            fundraising_records.append(fundraising_data)

    for item in fundraising_records:
        if item['Company'][0]['value'] not in fundraising_project_list:
            fundraising_project_list.append(item['Company'][0]['value'])
        fundraising_cumulative_value += float(item['Amount'])
        fundraising_date = datetime.strptime(item['Date'], "%Y-%m-%d")
        year = fundraising_date.year
        year_group[year].append(item)

    fundraising_list = []

    for year, items in year_group.items():
        fundraising_value = 0
        for i in items:
            fundraising_value += float(i['Amount']) 
        
        fundraising_list.append({"x": year, "y": fundraising_value})
    
    chart_list.append({"series": "Venture Funding", "data": fundraising_list, "key": metric_key})

    metric_list.append(vars(DashboardMetric(metric_key, "Venture Funding Received", '{:,.0f}'.format(fundraising_cumulative_value), "USD", None, None, None, fundraising_project_list)))

    metric_list.append(vars(DashboardMetric("venture-capital-deals", "Venture Funding Deals", fundraising_data['count'], "", None, None, None, fundraising_project_list)))

# Impact data
    impact_records = db.getDashboardData()
    grouped_data = defaultdict(list)
    series_name = None
    

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
        item_list = []

        for i in items:
            if i.metric.project not in project_list:
                project_list.append(i.metric.project)

            if i.metric.type == "Single":         
                metric_value += float(i.value)
                if metric_name is None:
                    metric_name = i.metric.name
                    metric_unit = i.metric.unit
                    metric_format = i.metric.format
                    metric_date = datetime.now()
                    formatted_date = metric_date.strftime(date_format)

            if i.metric.type == "Cumulative":
                item_list.append(i)

        if len(item_list) > 0:        
            latest_value = aggregate_latest_cumulative_metric_values(item_list)
            metric_value += latest_value['sum']
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

            for metric_date, items_on_date in sorted(date_grouped_data.items()):
                daily_total = 0
                for item in items_on_date:
                    daily_total += float(item.value)

                cumulative_value += daily_total
                item_list.append({"x": metric_date, "y": round(cumulative_value, 2)})

            chart_list.append({"series": metric_name, "data": item_list, "key": metric_key})

        metric_list.append(vars(DashboardMetric(metric_key,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, project_list)))

    result = {
        "aggregate": metric_list,
        "list": chart_list
    }

    return result