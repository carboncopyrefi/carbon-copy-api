import markdown, external, requests, utils, os, config
from flask import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

baserow_table_company = config.BASEROW_TABLE_COMPANY
date_format = config.DATE_FORMAT

file_path = "projects.json"
with open(file_path, "r") as _file:
    data = json.load(_file)

result = [project for project in data if project.get("karma_slug")]

current_timestamp = datetime.now()
three_months_ago = current_timestamp - timedelta(days=90)

def fetch_updates(project):
    local_updates = []
    slug = project['karma_slug']
    api = f"https://gapapi.karmahq.xyz/projects/{slug}"
    
    try:
        response = requests.get(api, timeout=20)
        response.raise_for_status()
    except Exception as e:
        print(f"Request failed for {slug}: {e}")
        return []

    updates = response.json() or []
    
    for update in updates['updates']:
        data = update.get('data', {})
        end_date_str = data.get('endDate')
        if not end_date_str:
            continue

        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            continue

        if not (three_months_ago <= end_date <= current_timestamp):
            continue

        id = update['uid']
        name = data.get('title', 'Untitled')
        date = end_date.strftime(date_format)
        details = markdown.markdown(data.get('text', '') + '<p class="fw-bold">Deliverables</p>')

        for deliverable in data.get('deliverables', []):
            details += markdown.markdown(f"- [{deliverable['name']}]({deliverable['proof']})")

        item = external.Impact(id, name, project['name'], end_date_str, date, details, None, "text")
        local_updates.append(vars(item))
    
    return local_updates

# Run in parallel
updates_list = []
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(fetch_updates, project) for project in result]
    for future in as_completed(futures):
        try:
            updates = future.result()
            if updates:
                updates_list.extend(updates)
        except Exception as e:
            print(f"Error in future: {e}")

# Sort the final list
sorted_updates_list = sorted(updates_list, key=lambda d: d['unit'], reverse=True)

output_file = "impact_feed.json"
os.remove(output_file)

with open("impact_feed.json", "w") as _file:
    json.dump(sorted_updates_list, _file)