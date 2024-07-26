from flask import Flask, jsonify, request, json
import feedparser, requests, random, datetime, os, re, utils, markdown
from flask_cors import CORS
from feedwerk.atom import AtomFeed
from urllib.request import urlopen 

app = Flask(__name__)
CORS(app, resources={r"/response*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['TOKEN'] = 'PS91RoTw8hOvLgK4TyeTsEKv13ZFUhQR'

access_control_origin_header = "Access-Control-Allow-Origin"
access_control_origin_value = "*"
baserow_token = 'Token RPlLXKDgBX8TscVGjKjI33djLk89X1qf'

date_format = "%B %d, %Y"
category = "environment"

baserow_table_company = "171320"
baserow_table_company_news = "173781"
baserow_table_company_links = "171328"
baserow_table_company_coverage = "171322"
baserow_table_company_response = "265286"
baserow_table_company_fundraising = "306630"
baserow_table_company_category = "314288"
baserow_table_company_founder = "171321"
baserow_table_events = "203056"
baserow_table_survey_question = "265287"

class TopProject:
    def __init__(self, name, description, categories, id, slug, logo):
        self.name = name
        self.description = description
        self.categories = categories
        self.id = id
        self.slug = slug
        self.logo = logo

class Project:
    def __init__(self, id, slug, name, description_short, links, sectors, description_long, categories, logo, founder, coverage, news, top16, location, protocol, responses,fundraising):
        self.id = id
        self.slug = slug
        self.name = name
        self.description_short = description_short
        self.links = links
        self.sectors = sectors
        self.description_long = description_long
        self.categories = categories
        self.logo = logo
        self.founder = founder
        self.coverage = coverage
        self.news = news
        self.top16 = top16
        self.location = location
        self.protocol = protocol
        self.response = responses
        self.fundraising = fundraising

class Category:
    def __init__(self, metadata, projects, tokens, news, fundraising):
        self.metadata = metadata
        self.projects = projects
        self.tokens = tokens
        self.news = news
        self.fundraising = fundraising

def project_details(slug):

    # Get company_id from Baserow to use in other requests
    company_params = "filter__field_1248804__equal=" + slug
    company_data = utils.get_baserow_data(baserow_table_company, company_params)
    result = company_data['results'][0]
    company_id = str(result['id'])
    
    # Get data from CompanyFundraising table
    fundraising_params = "filter__field_2209789__link_row_has=" + company_id
    fundraising_data = utils.get_baserow_data(baserow_table_company_fundraising, fundraising_params)

    fundraising_dict = {}
    fundraising_list = []
    
    for entry in fundraising_data['results']:
        if entry['Project ID'] is None or len(entry['Project ID']) < 1:
            amount = float(entry["Amount"])
            formatted_amount = '{:,.2f}'.format(amount)
            if entry['Round'] is None:
                round = ""
            else:
                round = entry['Round']['value']
            fundraising_dict = {"funding_type": entry['Type']['value'], "round": round, "amount": formatted_amount, "year": entry["Date"].split('-')[0], "url": entry["Link"]}
            fundraising_list.append(fundraising_dict) 

        # Get Giveth data
        elif entry['Project ID'] is not None and entry['Type']['value'] == "Giveth":          
            giveth_data = utils.get_giveth_data(entry['Project ID'])                
            fundraising_list.append(giveth_data)
        else:
            pass
    
    fundraising_sums = utils.calculate_dict_sums(fundraising_list)

    # Get data from Link table
    l_dict = {}
    l_list = []
    links_params = "filter__field_1139485__link_row_has=" + company_id
    links_data = utils.get_baserow_data(baserow_table_company_links, links_params)

    for l in links_data['results']:
        platform = l['Platform']['value']
        icon = utils.contact_icon(platform.lower())
        l_dict = {"platform": platform, "url": l['URL'], "icon": icon}
        l_list.append(l_dict)

    # Get data from Founder and link tables
    f_list = []
    f_dict = {}
    founder_params = "filter__field_1139228__link_row_has=" + company_id
    founder_data = utils.get_baserow_data(baserow_table_company_founder, founder_params)

    for f in founder_data['results']:
        founder_name = f['Name']
        url = None
        founder_link_list = []

        if len(f['Links']) > 0:
            for l in f['Links']:
                founder_links_table_id = baserow_table_company_links + "/" + str(l['id'])
                founder_links_data = utils.get_baserow_data(founder_links_table_id, "")
                url = founder_links_data['URL']
                platform = utils.contact_icon(founder_links_data['Platform']['value'].lower())
                founder_link_dict = {"platform": platform, "url": url}
                founder_link_list.append(founder_link_dict)

        else:
            pass

        f_dict = {"name": founder_name, "platforms": founder_link_list}
        f_list.append(f_dict)

    # Get data from Category table
    cat_dict = {}
    cat_list = []

    for cat in result['Category']:
        table_id = baserow_table_company_category + "/" + str(cat['id'])
        cat_data = utils.get_baserow_data(table_id, "")
        cat_dict = {"name": cat_data['Name'], "slug": cat_data['Slug']}
        cat_list.append(cat_dict)

    # Get data from Coverage table
    c_dict = {}
    c_list = []
    coverage_params = "filter__field_1139490__link_row_has=" + company_id
    coverage_data = utils.get_baserow_data(baserow_table_company_coverage, coverage_params)

    for a in coverage_data['results']:
        published_time = datetime.datetime.strptime(a['Publish Date'], "%Y-%m-%d")
        formatted_time = published_time.strftime(date_format)
        c_dict = {"headline": a['Headline'], "publication": a['Publication']['value'], "url": a['Link'], "date": formatted_time, "sort_date": published_time}
        c_list.append(c_dict)

    sorted_c_list = sorted(c_list, key=lambda d: d['sort_date'], reverse=True)

    # Get data from News table
    n_dict = {}
    n_list = []
    news_params = "filter__field_1156934__link_row_has=" + company_id
    news_data = utils.get_baserow_data(baserow_table_company_news, news_params)

    for n in news_data['results']:
        published_time = datetime.datetime.strptime(n['Created on'], "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_time = published_time.strftime(date_format)
        n_dict = {"headline": n['Headline'], "snippet": n['Snippet'], "url": n['Link'], "date": formatted_time, "sort_date": published_time}
        n_list.append(n_dict)

    sorted_n_list = sorted(n_list, key=lambda d:d['sort_date'], reverse=True)

    # Get data from RegenSurveyResponse table
    r_dict = {}
    r_list = []
    response_params = "filter__field_1887993__link_row_has=" + company_id
    response_data = utils.get_baserow_data(baserow_table_company_response, response_params)

    for r in response_data['results']:
        r_dict = {"survey": r['Survey'][0]['value']}
        r_list.append(r_dict)

    sorted_r_list = sorted(r_list, key=lambda d:d['survey'], reverse=True)

    # Create project object and return
    project = Project(company_id, result['Slug'], result['Name'], result['One-sentence Description'], l_list, result['Sector'], result['Description'], cat_list, result['Logo'], f_list, sorted_c_list, sorted_n_list, result['Top 16'], result['Location'], result['Protocol'], sorted_r_list, fundraising_sums)
    project_dict = vars(project)

    return project_dict

def top_projects_list():
    p_list = []
    params = "filter__field_1147468__boolean=true"
    data = utils.get_baserow_data(baserow_table_company, params)

    for item in data['results']:
        project = TopProject(item['Name'], item['One-sentence Description'], item['Category'], item['id'], item['Slug'], item['Logo'])
        project_dict = vars(project)
        p_list.append(project_dict)

    return p_list

def projects_list():
    p_list = []
    page_size = "200"
    params = "filter__field_1248804__not_empty&size=" + page_size + "&include=Name,One-sentence Description,Category,id,Slug,Logo"
    data = utils.get_baserow_data(baserow_table_company, params)
    projects = data['results']

    if data['count'] > int(page_size):
        params += "&page=2"
        data = utils.get_baserow_data(baserow_table_company, params)
        for project in data['results']:
            projects.append(project)

    for item in projects:
        c_list = []

        for category in item['Category']:
            c_list.append(category['value'])

        project = TopProject(item['Name'], item['One-sentence Description'], c_list, item['id'], item['Slug'], item['Logo'])
        project_dict = vars(project)
        p_list.append(project_dict)

    sorted_p_list = sorted(p_list, key=lambda x:x['name'].lower())

    return sorted_p_list

def landscape():
    projects = projects_list()

    categories_dict = {}

    for project in projects:
        # Iterate over each category in the project's categories
        for category in project['categories']:
            # If the category is not already in the dictionary, add it with an empty list
            if category not in categories_dict:
                categories_dict[category] = []
            # Add the project to the category's list
            categories_dict[category].append(project)
    
    categories_list = [{'category': category, 'projects': projects} for category, projects in categories_dict.items()]

    sorted_categories_list = sorted(categories_list, key=lambda x:x['category'].lower())

    return sorted_categories_list

def category_projects(slug):
    name = slug.replace("-"," ")
    p_list = []
    comp_list = []
    category_news_list = []
    category_fundraising_list = []
    filter_string = ""
    tokens = ""
    params = "filter__field_2275918__link_row_contains=" + name + "&filter__field_1248804__not_empty"
    data = utils.get_baserow_data(baserow_table_company, params)

    table_id = baserow_table_company_category + "/" + str(data['results'][0]['Category'][0]['id'])
    cat_data = utils.get_baserow_data(table_id, "")
    cat_dict = {"name": cat_data['Name'], "slug": cat_data['Slug'], "description": cat_data['Description'], "count": data['count']}    

    for p in data["results"]:
        comp_list.append(p['Name'])
        p_dict = {"name": p['Name'], "slug": p["Slug"], "short_description": p['One-sentence Description'], "description": p['Description'], "logo": p['Logo'], "location": p['Location'] }
        p_list.append(p_dict)

        if p['Token']:
            tokens += p['Token'] + ","

    sorted_p_list = sorted(p_list, key=lambda x:x['name'].lower())

    # Get a list of news items related to projects in the category
    news_data = utils.get_baserow_data(baserow_table_company_news,"size=50&order_by=-Created on")
    news_list = [
        news_item for news_item in news_data['results']
        if any(project['value'] in comp_list for project in news_item["Company"])
    ]

    # Create a list of news item dicts
    for item in news_list:
        published_time = datetime.datetime.strptime(item['Created on'], "%Y-%m-%dT%H:%M:%S.%fZ")
        formatted_time = published_time.strftime(date_format)
        category_news_dict = {"title": item['Headline'], "snippet": item['Snippet'], "date": formatted_time, "link": item['Link'], "company": item['Company']}
        category_news_list.append(category_news_dict)

    # Get fundraising data
    for p in comp_list:
        filter_string += "filter__field_2209789__link_row_contains=" + p + "&"

    fundraising_params = "filter_type=OR&" + filter_string
    fundraising_data = utils.get_baserow_data(baserow_table_company_fundraising, fundraising_params)
    fundraising_list = [
        fundraising_item for fundraising_item in fundraising_data['results']
        if any(project['value'] in comp_list for project in fundraising_item["Company"])
    ]

    for f in fundraising_list:
        if f['Project ID'] is None or len(f['Project ID']) < 1:
            funding_type = f['Type']['value']
            fundraising_dict = {
                "funding_type": funding_type,
                "amount": f['Amount'],
                "round": None if f['Round'] is None else f['Round']['value'],
                "year": f["Date"].split('-')[0],
                "url": f['Link']
            }
            category_fundraising_list.append(fundraising_dict)

        # Get Giveth data
        if f['Project ID'] is not None and f['Type']['value'] == "Giveth":          
            giveth_data = utils.get_giveth_data(f['Project ID'])                
            category_fundraising_list.append(giveth_data)
        else:
            pass

    fundraising_sums = utils.calculate_dict_sums(category_fundraising_list)

    category = vars(Category(cat_dict, sorted_p_list, tokens, category_news_list, fundraising_sums))

    return category

def category_project_tokens(token_ids):
    token_list = []
    token_data = utils.get_coingecko_data(token_ids)

    for token in token_data:
        url = "https://www.coingecko.com/en/coins/" + token['id']
        token_dict = {"image": token['image'], "symbol": token['symbol'].upper(), "price_usd": round(token['current_price'],5), "percent_change": round(token['price_change_percentage_24h'],2), "url": url}
        token_list.append(token_dict)
    
    return token_list

class News:
    def __init__(self, title, snippet, company, link, date):
        self.title = title
        self.snippet = snippet
        self.company = company
        self.link = link
        self.date = date

def news_list():
    news_list = []
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
            news = News(item['Headline'], item['Snippet'], item['Company'][0]['value'], item['Link'], published_time)
            news_dict = vars(news)
            news_list.append(news_dict)
        else:
            continue

    return news_list


class Article:
    def __init__(self, title, _path, image, publication, date):
        self.title = title
        self._path = _path
        self.mainImage = image
        self.publication = publication
        self.date = date

def nasa():
    nasa_feed = "https://climate.nasa.gov/news/rss.xml"
    nasa_list = []

    f = feedparser.parse(nasa_feed)

    for article in f.entries[0:4]:
        a = Article(article.title, article.link, "https://carboncopy.news/images/nasa_logo.png", "NASA", article.published)
        nasa_list.append(a)

    return nasa_list

def coindesk():
    cd_feed = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    cd_list = []

    f = feedparser.parse(cd_feed)

    for article in f.entries:
        if hasattr(article, 'tags'):
            for tag in article.tags:
                if category in tag.term.lower():
                    a = Article(article.title, article.link, article.media_content[0]['url'], "CoinDesk", article.published)
                    cd_list.append(a)
                else:
                    continue
        else:
            continue

    return cd_list

def sciencedaily():
    sc_feed = "https://www.sciencedaily.com/rss/earth_climate/environmental_awareness.xml"
    sc_list = []

    f = feedparser.parse(sc_feed)

    for article in f.entries[0:4]:
        a = Article(article.title, article.link, "https://carboncopy.news/images/science-daily.png", "ScienceDaily", article.published)
        sc_list.append(a)

    return sc_list

def feed():
    na = nasa()
    cd = coindesk()
    sd = sciencedaily()

    feed = []

    for item in cd:
        item_dict = vars(item)
        feed.append(item_dict)

    for item in na:
        item_dict = vars(item)
        feed.append(item_dict)

    for item in sd:
        item_dict = vars(item)
        feed.append(item_dict)

    return feed

class Event:
    def __init__(self, title, description, start_date, end_date, location, image, link):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.image = image
        self.link = link

def upcoming_events():
    e_list = []
    params = "&filter__field_1394864__date_after=" + str(datetime.date.today())
    data = utils.get_baserow_data(baserow_table_events, params)
    
    for item in data['results']:
        event = Event(item['Name'], item['Description'], item['Start Date'], item['End Date'], item['Location']['value'], item['Image'], item['Website'])
        event_dict = vars(event)
        e_list.append(event_dict)

    sorted_e_list = sorted(e_list, key=lambda d: d['start_date'])

    return sorted_e_list

class SurveyQuestion:
    def __init__(self, name, text, category, tip, answerOne, answerTwo, answerThree):
        self.name = name
        self.text = text
        self.category = category
        self.tip = tip
        self.answerOne = answerOne
        self.answerTwo = answerTwo
        self.answerThree = answerThree

def survey_questions():
    q_list = []
    p_list = []
    page_size = '200'

    p_params = "?user_field_names=true&include=Name&size=" + page_size
    p_data = utils.get_baserow_data(baserow_table_company, p_params)

    for p in p_data['results']:
        p_list.append(p['Name'])

    if p_data['count'] > int(page_size):
        p2_params = "include=Name&page=2&size=200"
        p2_data = utils.get_baserow_data(baserow_table_company, p2_params)

        for p in p2_data['results']:
            p_list.append(p['Name'])

    sorted_p_list = sorted(p_list, key=str.casefold)

    data = utils.get_baserow_data(baserow_table_survey_question,"")

    for item in data['results']:
        question = SurveyQuestion(item['Name'], item['Text'], item['Category']['value'], item['Tip'], item['Answer 1'], item['Answer 2'], item['Answer 3'])
        question_dict = vars(question)
        q_list.append(question_dict)

    sorted_q_list = sorted(q_list, key=lambda d: d['name'])

    return jsonify({
        'projects': sorted_p_list,
        'questions': sorted_q_list
    })

class Token():
    def __init__(self, symbol, price_usd, percent_change):
        self.symbol = symbol
        self.price_usd = price_usd
        self.percent_change = percent_change

class Milestone():
    def __init__(self, name, description, status, due_date, due_date_unix, completed_msg):
        self.name = name
        self.description = description
        self.status = status
        self.due_date = due_date
        self.due_date_unix = due_date_unix
        self.completed_msg = completed_msg

class Impact():
    def __init__(self, id, name, metric, unit, date, details, status, type):
        self.id = id
        self.name = name
        self.metric = metric
        self.unit = unit
        self.date = date
        self.details = details 
        self.status = status
        self.type = type

def project_content(slug):
    impact_list = []
    # RSS feed content
    generator = ""   
    params = "?user_field_names=true&filter__field_1248804__equal=" + slug
    data = utils.get_baserow_data(baserow_table_company, params)
    result = data['results'][0]

    if result['Content feed'] == "":
        content_list = None        
    else:
        content_feed_url = str(result['Content feed'])
        article_list = []
        content_list = []

        f = feedparser.parse(content_feed_url)
        if hasattr(f.feed,'generator'): 
            if f.feed['generator'] == 'Medium':
                generator = 'Medium'
        else:
            generator = None

        for article in f.entries[0:3]:
            mainImage = f.feed['image']['href']
            link = ""
            date = utils.parse_datetime(article.published)
            formatted_date = date.strftime(date_format)
            if generator == 'Medium':
                match = re.search(r'<img[^>]+src="([^">]+)"', article.content[0]['value'])
                mainImage = match.group(1)
            if hasattr(article, 'media_content'):
                mainImage = article.media_content[0]['url']
            if hasattr(article,'image'):
                mainImage = article.image['href']
            if hasattr(article, 'links'):
                for link in article.links:
                    if link.type == "image/jpg":
                        mainImage = link.href
                    if link.type == 'audio/mpeg':
                        link = link.href
                    else:
                        link = article.link
                        continue
            else:
                continue
        
            a = Article(article.title, link, mainImage, formatted_date, formatted_date)
            article_list.append(a)

        for item in article_list:
            item_dict = vars(item)
            content_list.append(item_dict)

    # Token data
    if result['Token'] is None or len(result['Token']) < 1:
        token = None
    else:
        token_id = result['Token']

        if re.search(r'^[^:]+:[^:]+$', token_id):
            network = token_id.split(':')[0]
            token_address = token_id.split(':')[1]
            r = utils.get_coingeckoterminal_data(network, token_address)
            token_data = r['data']['attributes']

            token = Token(token_data['symbol'].upper(), round(float(token_data['price_usd']),5), 0)
        else:
            r = utils.get_coingecko_data(token_id)
            token_data = r[0]

            token = Token(token_data['symbol'].upper(), round(token_data['current_price'],5), round(token_data['price_change_percentage_24h'],2))
        
        token = vars(token)

    # Karma GAP milestone data
    if result['Karma slug'] is None or len(result['Karma slug']) < 1:
        sorted_milestone_list = None
    else:
        milestone_list = []
        completed_msg = None
        karma_slug = result['Karma slug']
        milestone_data = utils.get_karma_gap_data(karma_slug, "milestones")

        for m in milestone_data:
            due_date = datetime.datetime.fromtimestamp(m['data']['endsAt']).strftime(date_format)
            description = markdown.markdown(m['data']['description'])
            if "completed" in m.keys():
                status = "Completed"
                completed_msg = markdown.markdown(m['completed']['data']['reason'])
            elif datetime.datetime.fromtimestamp(m['data']['endsAt']) > datetime.datetime.now():
                status = "In Progress"
            elif datetime.datetime.fromtimestamp(m['data']['endsAt']) < datetime.datetime.now():
                status = "Overdue"
            else:
                status = "In Progress"

            milestone = Milestone(m['data']['title'], description, status, due_date, m['data']['endsAt'], completed_msg)
            milestone_list.append(vars(milestone))
        
        sorted_milestone_list = sorted(milestone_list, key=lambda d: d['due_date_unix'], reverse=True)

        # Get Karma GAP impact data
        impact_data = utils.get_karma_gap_data(karma_slug, "impacts")

        for impact in impact_data:
            if datetime.datetime.fromtimestamp(impact['data']['completedAt']).strftime('%Y') != str(datetime.datetime.now().year):
                pass
            else:
                id = impact['id']
                date = datetime.datetime.fromtimestamp(impact['data']['completedAt']).strftime(date_format)
                details = markdown.markdown(impact['data']['impact'] + "<br /><br />" + impact['data']['proof'])
                if len(impact['verified']) < 1:
                    status = "Unverified"
                else:
                    status = "Verified"

                item = Impact(id, impact['data']['work'], None, None, date, details, status, "text")
                impact_list.append(vars(item))
    
    # Get Impact data
    if len(result['Impact Metrics JSON']) == 0:
        pass
    else:
        json_url = result['Impact Metrics JSON'][0]['url']
        response = urlopen(json_url)
        data = json.loads(response.read())

        if data['method'] == "POST":
            post_body_json = json.dumps(data['body'])
            post_body = json.loads(post_body_json)
            response = requests.post(data['api'], json=post_body)
            metric_data = response.json()[data['result_key']][data['result_index']]

            for metric in data['metrics']:
                metric_date = utils.parse_datetime(metric_data[data['date_key']])
                formatted_metric_date = metric_date.strftime(date_format)
                if metric['type'] == "numeric":
                    value = metric_data[metric['key']]
                    formatted_value = round(float(value) / data['global_denominator'], 2) if data['global_operator'] == "divide" else round(float(value), 2)
                    if metric['operator'] == "multiply":
                        formatted_value = round(formatted_value * metric['denominator'], 2)
                    if metric['operator'] == "divide":
                        formatted_value = round(formatted_value / metric['denominator'], 2)

                    impact_list.append(vars(Impact(None, metric['name'], '{:,.2f}'.format(formatted_value), metric['unit'], formatted_metric_date, None, None, metric['type'])))

    content = {
            'feed': content_list,
            'token': token,
            'milestones': sorted_milestone_list,
            'impact': impact_list
            }

    return content

# Routes
@app.route('/articles', methods=['GET'])
def articles():
    data = feed()
    random.shuffle(data)
    response = jsonify(data[0:6])
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/projects/<slug>', methods=['GET'])
def projectDetails(slug):
    data = project_details(slug)
    response = jsonify(data)

    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/projects/<slug>/content', methods=['GET'])
def projectContent(slug):
    data = project_content(slug)
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response, 200

@app.route('/projects/top', methods=['GET'])
def top_projects():
    data = top_projects_list()
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/projects', methods=['GET'])
def projects():
    data = projects_list()
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/projects/categories/<slug>', methods=['GET'])
def categoryProjects(slug):
    data = category_projects(slug)
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/projects/categories/tokens', methods=['GET'])
def categoryProjectTokens():
    tokens = request.args.getlist('ids')[0]
    if tokens != "":
        data = category_project_tokens(tokens)
        response = jsonify(data)
        response.headers.add(access_control_origin_header, access_control_origin_value)
        return response
    else:
        return ""
    
@app.route('/landscape', methods=['GET'])
def refiLandscape():
    data = landscape()
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/news', methods=['GET'])
def news():
    data = news_list()
    response = jsonify(data[0:10])
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/feed', methods=['GET'])
def refi_feed():
    data = news_list()
    news_feed = AtomFeed(title='ReFi News', feed_url=request.url, url=request.url_root)
    for item in data:
        news_feed.add(item['title'],item['snippet'],content_type='html',author=item['company'],url=item['link'],updated=item['date'],published=item['date'])
    return news_feed.get_response()

@app.route('/events', methods=['GET'])
def events():
    data = upcoming_events()
    response = jsonify(data)
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/questions', methods=['GET'])
def questions():
    response = survey_questions()
    response.headers.add(access_control_origin_header, access_control_origin_value)
    return response

@app.route('/response', methods=['POST'])
def response():
    if request.method == 'POST' and request.headers.get('token') == app.config['TOKEN'] and request.data is not None:
        data = json.loads(request.data)
        _name = data['name']
        _company = data['company']
        _survey = str(datetime.date.today().year)
        _email = data['email']
        _answers = data['picked']
        _questions = data['questions']

        answers = []
        scores = []
        sum_scores = 0
        impact_sum = 0
        org_sum = 0

        for answer in _answers:
            a = answer.split(';')
            answers.append(a[0])
            scores.append(int(a[1]))

        sum_scores = sum(scores)

        questions = []
        for question in _questions:
            q_dict = {'Name': _company, 'Response': _company, 'Question': question['name'], 'questionText': question['text'], 'category': question['category'] }
            questions.append(q_dict)

        K = "Answer"
        L = "Score"
        for dic, lis, s in zip(questions, answers, scores):
            dic[K] = lis
            dic[L] = s

        for q in questions:
            if q['category'] == "Regenerative Impact":
                impact_sum += q['Score']
            else:
                org_sum += q['Score']

        with open(_company + ".json", "w") as _file:
            json.dump(questions, _file)

        try:
            file = requests.post(
                'https://api.baserow.io/api/user-files/upload-file/',
                headers={
                    'Authorization': baserow_token
                },
                files={
                    'file': open(_file.name, 'rb')
                }
            )
            try:
                row = requests.post(
                    "https://api.baserow.io/api/database/rows/table/265286/?user_field_names=true",
                    headers={
                        'Authorization': 'Token gp4qn547MSjgnoQ5VrA2n37BDtN4B3KR',
                        'Content-Type': 'application/json'
                    },
                    json={
                        "Name": _name,
                        "Company": [
                            _company
                        ],
                        "Survey": [
                            _survey
                        ],
                        "JSON": [
                            file.json()
                        ],
                        "Email": _email,
                        "Regenerative Impact Score": impact_sum,
                        "Regenerative Organisation Score": org_sum,
                        "Total Score": sum_scores
                    }
                )
            except:
                return "", 500
        except:
            return "", 500

        os.remove(_file.name)

        response = jsonify({
            'scores': {
                'total': sum_scores,
                'impact': impact_sum,
                'organisation': org_sum
            },
            'answers': questions
            })

        return response, 200
    else:
        return "", 400

if __name__ == "__main__":
    app.run()




