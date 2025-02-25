import utils, feedparser, external, re, markdown, config, db, requests, os, json
from collections import defaultdict
from datetime import datetime, timedelta

date_format = config.DATE_FORMAT
baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_company_links = config.BASEROW_TABLE_COMPANY_LINKS
baserow_table_company_founder = config.BASEROW_TABLE_COMPANY_FOUNDER
baserow_table_company_category = config.BASEROW_TABLE_COMPANY_CATEGORY
baserow_table_company_coverage = config.BASEROW_TABLE_COMPANY_COVERAGE
baserow_table_company_response = config.BASEROW_TABLE_COMPANY_RESPONSE
baserow_table_company_news = config.BASEROW_TABLE_COMPANY_NEWS
baserow_table_company_opportunity = config.BASEROW_TABLE_COMPANY_OPPORTUNITY
baserow_table_company_fundraising = config.BASEROW_TABLE_COMPANY_FUNDRAISING
baserow_table_company_impact_data = config.BASEROW_TABLE_COMPANY_IMPACT_DATA

class TopProject:
    def __init__(self, name, description, categories, id, slug, logo, location):
        self.name = name
        self.description = description
        self.categories = categories
        self.id = id
        self.slug = slug
        self.logo = logo
        self.location = location

class Project:
    def __init__(self, id, slug, name, description_short, links, sectors, categories, logo, founder, coverage, news, top16, location, protocol, responses):
        self.id = id
        self.slug = slug
        self.name = name
        self.description_short = description_short
        self.links = links
        self.sectors = sectors
        self.categories = categories
        self.logo = logo
        self.founder = founder
        self.coverage = coverage
        self.news = news
        self.top16 = top16
        self.location = location
        self.protocol = protocol
        self.response = responses


def project_json():
    
    page_size = 200

    # Get survey responses
    response_data = utils.get_baserow_data(baserow_table_company_response, "")
    responses = response_data['results']

    # Get founders
    founder_params = "Links__join=URL&filter__field_1139228__not_empty"
    founder_data = utils.get_baserow_data(baserow_table_company_founder, founder_params)
    founders = founder_data['results']

    total_founder_pages = (founder_data['count'] + page_size - 1) // page_size

    for founder_page in range(2, total_founder_pages + 1):
        founder_new_params = founder_params + f"&page={founder_page}"
        data = utils.get_baserow_data(baserow_table_company_founder, founder_new_params)
        founders.extend(data['results'])

    # Get news
    news_data = utils.get_baserow_data(baserow_table_company_news, "")
    news = news_data['results']

    total_news_pages = (news_data['count'] + page_size - 1) // page_size

    for news_page in range(2, total_news_pages + 1):
        news_params = f"&page={news_page}"
        data = utils.get_baserow_data(baserow_table_company_news, news_params)
        news.extend(data['results'])

    
    # Get projects
    p_list = []
    
    params = "filter__field_1248804__not_empty&size=" + str(page_size) + "&Links__join=URL&Category__join=Name,Slug&Coverage__join=Headline,Link,Publication,Publish Date"
    data = utils.get_baserow_data(baserow_table_company, params)
    projects = data['results']

    total_pages = (data['count'] + page_size - 1) // page_size

    for page in range(2, total_pages + 1):
        paginated_params = params + f"&page={page}"
        data = utils.get_baserow_data(baserow_table_company, paginated_params)
        projects.extend(data['results'])

    for result in projects:
        company_id = str(result['id'])
        company_name = result['Name']

        # Create link list
        l_list = []

        for l in result['Links']:
            platform = l['value']
            icon = utils.contact_icon(platform.lower())
            l_dict = {"platform": platform, "url": l['URL'], "icon": icon}
            l_list.append(l_dict)

        # Get data from Founder and link tables
        f_list = []

        for f in founders:
            if any(c['value'] == company_name for c in f['Company'] ):
                founder_name = f['Name']
                url = None
                founder_link_list = []

                if len(f['Links']) > 0:
                    for l in f['Links']:
                        url = l['URL']
                        platform = utils.contact_icon(l['value'].lower())
                        founder_link_dict = {"platform": platform, "url": url}
                        founder_link_list.append(founder_link_dict)

                else:
                    pass

                f_dict = {"name": founder_name, "platforms": founder_link_list}
                f_list.append(f_dict)

        # Create Category list
        cat_list = []

        for cat in result['Category']:
            cat_dict = {"name": cat['Name'], "slug": cat['Slug']}
            cat_list.append(cat_dict)

        # Get data from Coverage table
        c_list = []

        for a in result['Coverage']:
            published_time = datetime.strptime(a['Publish Date'], "%Y-%m-%d")
            formatted_time = published_time.strftime(date_format)
            unix_time = int(published_time.timestamp())
            c_dict = {"headline": a['Headline'], "publication": a['Publication']['value'], "url": a['Link'], "date": formatted_time, "sort_date": unix_time}
            c_list.append(c_dict)

        sorted_c_list = sorted(c_list, key=lambda d: d['sort_date'], reverse=True)

        # Get data from News table
        n_dict = {}
        n_list = []

        for n in news:
            if any(c['value'] == company_name for c in n['Company'] ):
                published_time = datetime.strptime(n['Created on'], "%Y-%m-%dT%H:%M:%S.%fZ")
                formatted_time = published_time.strftime(date_format)
                unix_time = int(published_time.timestamp())
                n_dict = {"headline": n['Headline'], "url": n['Link'], "date": formatted_time, "sort_date": unix_time}
                n_list.append(n_dict)

        sorted_n_list = sorted(n_list, key=lambda d:d['sort_date'], reverse=True)

        # Get data from RegenSurveyResponse table
        r_dict = {}
        r_list = []

        for r in responses:
            if any(c['value'] == company_name for c in r['Company'] ):
                r_dict = {"survey": r['Survey'][0]['value']}
                r_list.append(r_dict)

        sorted_r_list = sorted(r_list, key=lambda d:d['survey'], reverse=True)

        # Create project object and return it
        project = Project(company_id, result['Slug'], result['Name'], result['One-sentence Description'], l_list, result['Sector'], cat_list, result['Logo'], f_list, sorted_c_list, sorted_n_list, result['Top 16'], result['Location'], result['Protocol'], sorted_r_list)
        p_list.append(vars(project))

    output_file = "projects.json"
    os.remove(output_file)

    with open("projects.json", "w") as _file:
        json.dump(p_list, _file)

    return "Success"


def project_details(slug):
    file_path = os.path.join(os.getcwd(), 'api', 'assets', 'projects.json')
    # file_path = "projects.json"
    with open(file_path, "r") as _file:
        data = json.load(_file)

    result = next((item for item in data if item["slug"] == slug), None)

    return result

def top_projects_list():
    p_list = []
    params = "filter__field_1147468__boolean=true"
    data = utils.get_baserow_data(baserow_table_company, params)

    for item in data['results']:
        project = TopProject(item['Name'], item['One-sentence Description'], item['Category'], item['id'], item['Slug'], item['Logo'], item['Location'])
        project_dict = vars(project)
        p_list.append(project_dict)

    return p_list

def projects_list():
    p_list = []
    page_size = "200"
    params = "filter__field_1248804__not_empty&size=" + page_size + "&include=Name,One-sentence Description,Category,id,Slug,Logo,Location"
    data = utils.get_baserow_data(baserow_table_company, params)
    projects = data['results']
    project_count = data['count']

    if data['count'] > int(page_size):
        params += "&page=2"
        data = utils.get_baserow_data(baserow_table_company, params)
        for project in data['results']:
            projects.append(project)

    for item in projects:
        c_list = []

        for category in item['Category']:
            c_list.append(category['value'])

        project = TopProject(item['Name'], item['One-sentence Description'], c_list, item['id'], item['Slug'], item['Logo'], item['Location'])
        project_dict = vars(project)
        p_list.append(project_dict)

    sorted_p_list = sorted(p_list, key=lambda x:x['name'].lower())

    result = {
        "projects": sorted_p_list,
        "count": project_count
    }

    return result


def project_content(slug):
    impact_list = []

    # RSS feed content
    generator = ""  
    params = "filter__field_1248804__equal=" + slug
    data = utils.get_baserow_data(baserow_table_company, params)
    result = data['results'][0]
    company_id = str(result['id'])
    company_name = result['Name']

    if result['Content feed'] == "":
        content_list = None        
    else:
        content_feed_url = str(result['Content feed'])
        article_list = []
        content_list = []
        mainImage = "" 

        if "paragraph" in content_feed_url:
            r = requests.get(content_feed_url)
            f = feedparser.parse(r.text)
        else:
            f = feedparser.parse(content_feed_url)
            
        if hasattr(f.feed,'generator'): 
            if f.feed['generator'] == 'Medium':
                generator = 'Medium'
        else:
            generator = None

        for article in f.entries[0:3]:
            if hasattr(f.feed, 'image'):
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
                    if link.type == "image/jpg" or link.type == "image/jpeg":
                        mainImage = link.href
                    if link.type == 'audio/mpeg':
                        link = link.href
                    else:
                        link = article.link
                        continue
            else:
                continue
        
            a = external.Article(article.title, link, mainImage, formatted_date, formatted_date)
            article_list.append(a)

        for item in article_list:
            item_dict = vars(item)
            content_list.append(item_dict)

    # Opportunities
    opportunity_list = []
    formatted_date = ""
    current_date = datetime.now().strftime("%Y-%m-%d")
    op_params = "&filter__field_3330931__link_row_has=" + company_id + "&order_by=-Expiring on"
    op_data = utils.get_baserow_data(baserow_table_company_opportunity, op_params)
    op_result = op_data['results']

    for op in op_result:
        if op['Expiring on'] is None:
            formatted_date = "Ongoing"
        elif op['Expiring on'] > current_date:
            expiry_date = datetime.strptime(op['Expiring on'], "%Y-%m-%d")
            formatted_date = expiry_date.strftime(date_format)
        else:
            pass
        opportunity_dict = {"name": op['Name'], "deadline": formatted_date, "url": op['Link']}
        opportunity_list.append(opportunity_dict)

    # Get data from CompanyFundraising table - take advantage of row link here
    fundraising_params = "filter__field_2209789__link_row_has=" + company_id
    fundraising_data = utils.get_baserow_data(baserow_table_company_fundraising, fundraising_params)

    fundraising_dict = {}
    fundraising_list = []
    
    for entry in fundraising_data['results']:
        if entry['Project ID'] is None or len(entry['Project ID']) < 1:
            amount = float(entry["Amount"])
            formatted_amount = '{:,.2f}'.format(amount)

            if entry['Round'] is None:
                fundraising_round = ""
            else:
                fundraising_round = entry['Round']['value']

            fundraising_dict = {"funding_type": entry['Type']['value'], "round": fundraising_round, "amount": formatted_amount, "date": entry["Date"], "year": entry["Date"].split('-')[0], "url": entry["Link"]}
            fundraising_list.append(fundraising_dict) 

        # Get Giveth data
        elif entry['Project ID'] is not None and entry['Type']['value'] == "Giveth":          
            giveth_data = utils.get_giveth_data(entry['Project ID'])                
            fundraising_list.append(giveth_data)
        else:
            pass
    
    fundraising_sums = utils.calculate_dict_sums(fundraising_list)

    # Token data
    token_list = []

    if result['Token'] is None or len(result['Token']) < 1:
        token = None
    else:
        token_id = result['Token']

        if re.search(r'^[^:]+:[^:]+$', token_id):
            network = token_id.split(':')[0]
            token_address = token_id.split(':')[1]
            r = utils.get_coingeckoterminal_data(network, token_address)
            token_data = r['data']['attributes']

            t = external.Token(token_data['symbol'].upper(), round(float(token_data['price_usd']),5), 0,"")
            token_list.append(vars(t))
        else:
            r = utils.get_coingecko_data(token_id)

            for token in r:
                if token['price_change_percentage_24h'] is None:
                    percent_change = 0
                else:
                    percent_change = round(token['price_change_percentage_24h'], 2)
                    
                t = external.Token(token['symbol'].upper(), round(token['current_price'],5), percent_change, token['id'])
                token_list.append(vars(t))

    # Karma GAP milestone data
    if result['Karma slug'] is None or len(result['Karma slug']) < 1:
        sorted_activity_list = None
    else:
        activity_list = []
        completed_msg = None
        karma_slug = result['Karma slug']
        karma_data = utils.get_karma_gap_data(karma_slug)

        for grant in karma_data['grants']:
            for m in grant['milestones']:
                due_date = datetime.fromtimestamp(m['data']['endsAt']).strftime(date_format)
                description = markdown.markdown(m['data']['description'])
                if "completed" in m.keys():
                    status = "Completed"
                    if "reason" in m['completed']['data'].keys():
                        completed_msg = markdown.markdown(m['completed']['data']['reason'])
                    else:
                        completed_msg = None
                elif datetime.fromtimestamp(m['data']['endsAt']) > datetime.now():
                    status = "In Progress"
                elif datetime.fromtimestamp(m['data']['endsAt']) < datetime.now():
                    status = "Overdue"
                else:
                    status = "In Progress"

                milestone = external.Activity(m['data']['title'], description, status, due_date, m['data']['endsAt'], completed_msg, "Milestone")
                activity_list.append(vars(milestone))
            
            for u in grant['updates']:
                description = markdown.markdown(u['data']['text'])
                if 'data' in u and 'proofOfWork' in u['data']:
                    description += "<a href=" + "'" + u['data']['proofOfWork'] + "'" + "target='_blank'>" + u['data']['proofOfWork'] + "</a>"
                due_date_string = datetime.strptime(u['createdAt'],"%Y-%m-%dT%H:%M:%S.%fZ")
                due_date_unix = datetime.timestamp(due_date_string) 

                update = external.Activity(u['data']['title'], description, None, None, due_date_unix, None, "Update")
                activity_list.append(vars(update))
        
        for update in karma_data['updates']:
            description = markdown.markdown(update['data']['text'])
            due_date_string = datetime.strptime(update['createdAt'],"%Y-%m-%dT%H:%M:%S.%fZ")
            due_date_unix = datetime.timestamp(due_date_string)          
            update = external.Activity(update['data']['title'], description, None, None, due_date_unix, None, "Update")
            activity_list.append(vars(update))

        sorted_activity_list = sorted(activity_list, key=lambda d: d['due_date_unix'], reverse=True)

        # Get Karma GAP impact data
        impact_data = karma_data['impacts']

        for impact in impact_data:
            current_timestamp = datetime.now()
            one_year_ago = current_timestamp - timedelta(days=365)

            if one_year_ago <= datetime.fromtimestamp(impact['data']['completedAt']) <= current_timestamp:
                id = impact['uid']
                date = datetime.fromtimestamp(impact['data']['completedAt']).strftime(date_format)
                details = markdown.markdown(impact['data']['impact'] + "<br /><br />" + impact['data']['proof'])
                if len(impact['verified']) < 1:
                    status = "Unverified"
                else:
                    status = "Verified"

                item = external.Impact(id, impact['data']['work'], None, None, date, details, status, "text")
                impact_list.append(vars(item))

            else:
                pass

    # Get Company Impact table data
    # company_impact_params = "filter__field_2601198__has_value_equal=" + company_name + "&order_by=-Date"
    # company_impact_data = utils.get_baserow_data(baserow_table_company_impact_data, company_impact_params)
    company_impact_data = db.getProjectImpactData(slug)
    
    latest_metrics = {}
    single_data = []
    single_grouped_data = defaultdict(list)

    for item in company_impact_data:
        if item.metric.type == "Cumulative":
            metric_name = item.metric.name

            if metric_name not in latest_metrics or item.date > latest_metrics[metric_name].date:
                latest_metrics[metric_name] = item
                formatted_metric_date = item.date.strftime(date_format)
                impact_list.append(vars(external.Impact(item.id, metric_name, item.metric.format.format(float(item.value)), item.metric.unit, formatted_metric_date, item.note, None, "numeric")))

        elif item.metric.type == "Single":
            single_data.append(item)
    
    for item in single_data:
        single_grouped_data[item.metric_id].append(item)

    for metric_id, items in single_grouped_data.items():
        metric_value = 0
        metric_name = None
        metric_unit = None
        metric_format = None

        for item in items:
            metric_value += float(item.value)
            if metric_name is None:
                metric_name = item.metric.name
                metric_unit = item.metric.unit
                metric_format = item.metric.format
                metric_date = datetime.now()
                formatted_date = metric_date.strftime(date_format)
        
        impact_list.append(vars(external.Impact(None,metric_name, metric_format.format(metric_value), metric_unit, formatted_date, None, None, "numeric")))

    content = {
            'feed': content_list,
            'token': token_list,
            'activity': sorted_activity_list,
            'impact': impact_list,
            'fundraising': fundraising_sums,
            'opportunities': opportunity_list
            }

    return content