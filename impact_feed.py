import markdown, external, requests, utils, os, config
from flask import json
from datetime import datetime, timedelta



baserow_table_company = config.BASEROW_TABLE_COMPANY
date_format = config.DATE_FORMAT

file_path = "projects.json"
with open(file_path, "r") as _file:
    data = json.load(_file)

result = [project for project in data if project.get("karma_slug") is not None]

impact_list = []

for project in result:
    slug = project['slug']
    api = "https://gapapi.karmahq.xyz/projects/" + slug + "/impacts"
    response = requests.get(api)
    if response.status_code == 200:
        impacts =  response.json()
        if impacts is not None:
            for i in impacts:
                current_timestamp = datetime.now()
                three_months_ago = current_timestamp - timedelta(days=90)

                if three_months_ago <= datetime.fromtimestamp(i['data']['completedAt']) <= current_timestamp:
                    id = i['uid']
                    date = datetime.fromtimestamp(i['data']['completedAt']).strftime(date_format)
                    details = markdown.markdown(i['data']['impact'] + "<br /><br />" + i['data']['proof'])
                    name = markdown.markdown(i['data']['work'])
                    if len(i['verified']) < 1:
                        status = "Unverified"
                    else:
                        status = "Verified"

                    item = external.Impact(id, name, project['name'], i['data']['completedAt'], date, details, status, "text")
                    impact_list.append(vars(item))
        else:
            pass
    else:
        raise Exception(f"Failed to fetch Karma GAP data with status {response.status_code}. {response.text}")

sorted_impact_list = sorted(impact_list, key=lambda d:d['unit'], reverse=True)

output_file = "impact_feed.json"
os.remove(output_file)

with open("impact_feed.json", "w") as _file:
    json.dump(sorted_impact_list, _file)