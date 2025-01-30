import utils, datetime, config, projects
from flask import current_app as app, request

baserow_table_company_news = config.BASEROW_TABLE_COMPANY_NEWS
baserow_table_company_founder = config.BASEROW_TABLE_COMPANY_FOUNDER
baserow_table_company_opportunity = config.BASEROW_TABLE_COMPANY_OPPORTUNITY
baserow_table_knowledge = config.BASEROW_TABLE_KNOWLEDGE
date_format = config.DATE_FORMAT

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

class Opportunity:
    def __init__(self, name, company, company_logo, link, expiry_date):
        self.name = name
        self.company = company
        self.company_logo = company_logo
        self.link = link
        self.expiry_date = expiry_date

class Knowledge:
    def __init__(self, title, link, company, medium, date, topic):
        self.title = title
        self.link = link
        self.company = company
        self.medium = medium
        self.date = date
        self.topic = topic

def knowledge_list():
    knowledge_list = []
    params = "order_by=Title&Company__join=Slug"
    data = utils.get_baserow_data(baserow_table_knowledge, params)

    for item in data['results']:
        medium_list = []
        date = datetime.datetime.strptime(item['Date Published'], "%Y-%m-%d")
        formatted_date = date.strftime(date_format)

        for medium in item['Medium']:
            icon = utils.medium_icon(medium['value'].lower())
            medium_dict = { "medium": medium['value'], "icon": icon }
            medium_list.append(medium_dict)
            
        company_dict = { "name": item['Company'][0]['value'], "slug": item['Company'][0]['Slug'] }
        knowledge = Knowledge(item['Title'], item['Link'], company_dict, medium_list, formatted_date, item['Category'][0]['value'])
        knowledge_list.append(vars(knowledge))
    
    return knowledge_list

def opportunity_list():
    opportunity_list = []
    formatted_date = ""
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    params = "&filter__field_3335752__date_after_or_equal=" + current_date + "&filter_type=OR&filter__field_3335752__empty&order_by=-Expiring on&Company__join=Logo"
    data = utils.get_baserow_data(baserow_table_company_opportunity, params)

    for item in data['results']:
        if item['Expiring on'] is None:
            formatted_date = "Ongoing"
        else:
            expiry_date = datetime.datetime.strptime(item['Expiring on'], "%Y-%m-%d")
            formatted_date = expiry_date.strftime(date_format)
        opportunity = Opportunity(item['Name'], item['Company'][0]['value'], item['Company'][0]['Logo'], item['Link'], formatted_date)
        opportunity_list.append(vars(opportunity))

    return opportunity_list

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