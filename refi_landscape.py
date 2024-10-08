import utils, datetime, config, projects
from flask import current_app as app, request

baserow_table_company_news = config.BASEROW_TABLE_COMPANY_NEWS
baserow_table_company_founder = config.BASEROW_TABLE_COMPANY_FOUNDER

class Person:
    def __init__(self, name, contacts, projects):
        self.name = name
        self.contacts = contacts
        self.projects = projects

class News:
    def __init__(self, title, company, link, date):
        self.title = title
        self.company = company
        self.link = link
        self.date = date

def news_list():
    news_list = []
    formatted_time = ""
    start = request.args.get('startDate')
    end = request.args.get('endDate')

    if start is not None or end is not None:
        params = "&filter__field_1156936__date_after_or_equal=" + start + "T00:00:01Z" + "&filter__field_1156936__date_before_or_equal=" + end + "T23:59:59Z" + "&filter_type=AND&order_by=-Created on"
        data = utils.get_baserow_data(baserow_table_company_news, params)

    else:
        params = "&size=50&order_by=-Created on"
        data = utils.get_baserow_data(baserow_table_company_news, params)

    for item in data['results']:
        if item['Display'] is True:
            published_time = datetime.datetime.strptime(item['Created on'], "%Y-%m-%dT%H:%M:%S.%fZ")
            news = News(item['Headline'], item['Company'][0]['value'], item['Link'], published_time)
            news_dict = vars(news)
            news_list.append(news_dict)
        else:
            continue

    return news_list

def people_list():
    person_list = []
    page_size = "200"
    params = "filter__field_2569042__has_not_empty_value&size=" + page_size
    data = utils.get_baserow_data(baserow_table_company_founder, params)
    people = data['results']
    people_count = data['count']

    if data['count'] > int(page_size):
        params += "&page=2"
        data = utils.get_baserow_data(baserow_table_company_founder, params)
        for person in data['results']:
            people.append(person)

    for person in people:
        project_list = [
            {
                'company': c.get('value', None),
                'slug': s.get('value', None)
            }
            for c, s in zip(person['Company'], person['Company Slug'])]

        link_list = [
            {
                'platform': p.get('value', None),
                'link': l.get('value', None),
                'icon': utils.contact_icon(p.get('value', None).lower())
            }
            for p, l in zip(person['Links'], person['Contact Link'])]


        p = Person(person['Name'], link_list, project_list)
        person_dict = vars(p)
        person_list.append(person_dict)
    
    sorted_person_list = sorted(person_list, key=lambda x:x['name'].lower())

    result = {
        "count": people_count,
        "people": sorted_person_list
    }
    return result

def landscape():
    landscape_list = projects.projects_list()

    categories_dict = {}

    for project in landscape_list['projects']:
        # Iterate over each category in the project's categories
        for category in project['categories']:
            # If the category is not already in the dictionary, add it with an empty list
            if category not in categories_dict:
                categories_dict[category] = []
            # Add the project to the category's list
            categories_dict[category].append(project)
    
    categories_list = [{'category': category, 'projects': landscape_list} for category, landscape_list in categories_dict.items()]

    sorted_categories_list = sorted(categories_list, key=lambda x:x['category'].lower())

    return sorted_categories_list