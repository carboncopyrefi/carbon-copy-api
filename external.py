import utils, re, feedparser, datetime, config, requests

baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_events = config.BASEROW_TABLE_EVENTS
date_format = config.DATE_FORMAT
coingecko_base_url = config.COINGECKO_BASE_URL
paragraph_rss = config.PARAGRAPH_RSS
news_category_key = config.NEWS_CATEGORY_KEY
refidao_rss = config.REFIDAO_RSS
carbon_advisor_rss = config.CARBON_ADVISOR_RSS

class Token():
    def __init__(self, symbol, price_usd, percent_change, token_id):
        self.symbol = symbol
        self.price_usd = price_usd
        self.percent_change = percent_change
        self.token_id = token_id

class Activity():
    def __init__(self, name, description, status, due_date, due_date_unix, completed_msg, type):
        self.name = name
        self.description = description
        self.status = status
        self.due_date = due_date
        self.due_date_unix = due_date_unix
        self.completed_msg = completed_msg
        self.type = type

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

class Article:
    def __init__(self, title, _path, image, publication, date):
        self.title = title
        self._path = _path
        self.mainImage = image
        self.publication = publication
        self.date = date

class Event:
    def __init__(self, title, description, start_date, end_date, location, image, link):
        self.title = title
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.image = image
        self.link = link


def token_list():
    token_list = []
    token_data_list = []
    combined_list = []
    cg_list = ""
    params = "filter__field_2250961__not_empty&filter__field_1248804__not_empty&include=Name,Slug,Token,Logo"
    data = utils.get_baserow_data(baserow_table_company, params)
    tokens = data['results']
    
    for token in tokens:
        token_id = token['Token']
        
        if re.search(r'^[^:]+:[^:]+$', token_id):
            cgt_token_dict = {'project': token['Name'], 'slug': token['Slug'], 'token_id': token_id, 'logo': token['Logo'], 'url': None}
            token_list.append(cgt_token_dict)

            network = token_id.split(':')[0]
            token_address = token_id.split(':')[1]
            r = utils.get_coingeckoterminal_data(network, token_address)
            cgt_token_data = r['data']['attributes']
            
            t = Token(cgt_token_data['symbol'].upper(), round(float(cgt_token_data['price_usd']),5), 0, token_id)
            cgt_token_dict = vars(t)
            token_data_list.append(cgt_token_dict)
            
        else:
            if re.search(r'^[a-zA-Z0-9,-]+,+[a-zA-Z0-9,-]+$', token_id):
                tokens = token_id.split(",")
                for t in tokens:
                    cg_list += t + ','
                    token_url = coingecko_base_url + t
                    token_dict = {'project': token['Name'], 'slug': token['Slug'], 'token_id': t, 'logo': token['Logo'], 'url': token_url}
                    token_list.append(token_dict)
            else:
                cg_list += token_id + ',' 
                token_url = coingecko_base_url + token_id
                token_dict = {'project': token['Name'], 'slug': token['Slug'], 'token_id': token_id, 'logo': token['Logo'], 'url': token_url}
                token_list.append(token_dict)

    token_data = utils.get_coingecko_data(cg_list)

    # Process data from CoinGecko

    for token in token_data:
        if token['price_change_percentage_24h'] is None:
            percent_change = 0
        else:
            percent_change = round(token['price_change_percentage_24h'], 2)
        t = Token(token['symbol'].upper(), round(token['current_price'],5), percent_change, token['id'])
        token_dict = vars(t)
        token_data_list.append(token_dict)

    # Combine lists

    for item1 in token_list:
        matching_item = next((item2 for item2 in token_data_list if item2['token_id'] == item1['token_id']), None)
        if matching_item:
            combined_dict = {**item1, **matching_item}  # Merge dictionaries
            combined_list.append(combined_dict)

    sorted_combined_list = sorted(combined_list, key=lambda x:x['project'].lower())
    token_count = len(token_data_list)

    result = {
        "count": token_count,
        "tokens": sorted_combined_list
    }

    return result

def refi_recap():
    refi_recap_list = []

    r = requests.get(refidao_rss)

    f = feedparser.parse(r.text)

    for article in f.entries[0:3]:
        if "ReFi Recap" in article.title:
            mainImage = ""
            date = utils.parse_datetime(article.published)
            formatted_date = date.strftime(date_format)
            for image in article.media_content:
                mainImage = image['url']

            a = Article(article.title, article.link, mainImage, formatted_date, formatted_date)
            refi_recap_list.append(vars(a))

    return refi_recap_list

def newsletter():
    newsletter_list = []

    r = requests.get(paragraph_rss)

    f = feedparser.parse(r.text)

    for article in f.entries[0:3]:
        mainImage = ""
        date = utils.parse_datetime(article.published)
        formatted_date = date.strftime(date_format)
        for link in article.links:
            if link.type == "image/jpg" or link.type == "image/jpeg":
                mainImage = link.href

        a = Article(article.title, article.link, mainImage, formatted_date, formatted_date)
        newsletter_list.append(vars(a))

    return newsletter_list

def carbon_advisor():
    carbon_advisor_list = []

    f = feedparser.parse(carbon_advisor_rss)

    for article in f.entries[0:4]:
        date = utils.parse_datetime(article.published)
        formatted_date = date.strftime(date_format)
        match = re.search(r'<img[^>]+src="([^">]+)"', article.description)
        mainImage = match.group(1)
        a = Article(article.title, article.link, mainImage, "Carbon Advisor", formatted_date)
        carbon_advisor_list.append(vars(a))

    return carbon_advisor_list

def eco_watch():
    eco_watch_feed = "https://www.ecowatch.com/rss"
    eco_watch_list = []

    f = feedparser.parse(eco_watch_feed)

    for article in f.entries[0:4]:
        a = Article(article.title, article.link, "https://carboncopy.news/images/ecowatch.png", "EcoWatch", article.published)
        eco_watch_list.append(a)

    return eco_watch_list

def coindesk():
    cd_feed = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    cd_list = []

    f = feedparser.parse(cd_feed)

    for article in f.entries:
        if hasattr(article, 'tags'):
            for tag in article.tags:
                if news_category_key in tag.term.lower():
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
    na = eco_watch()
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