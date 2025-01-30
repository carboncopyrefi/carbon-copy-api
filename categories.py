import utils, datetime, config
from flask import current_app as app

baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_company_category = config.BASEROW_TABLE_COMPANY_CATEGORY
baserow_table_company_news = config.BASEROW_TABLE_COMPANY_NEWS
baserow_table_company_fundraising = config.BASEROW_TABLE_COMPANY_FUNDRAISING
date_format = config.DATE_FORMAT
coingecko_base_url = config.COINGECKO_BASE_URL

class Category:
    def __init__(self, metadata, projects, tokens, news, fundraising):
        self.metadata = metadata
        self.projects = projects
        self.tokens = tokens
        self.news = news
        self.fundraising = fundraising

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

    cat_params = "filter__field_2275917__equal=" + slug
    cat_data = utils.get_baserow_data(baserow_table_company_category, cat_params)['results'][0]
    
    cat_dict = {"name": cat_data['Name'], "slug": cat_data['Slug'], "description": cat_data['Description'], "count": data['count']}    

    for p in data["results"]:
        comp_list.append(p['Name'])
        p_dict = {"name": p['Name'], "slug": p["Slug"], "short_description": p['One-sentence Description'], "logo": p['Logo'], "location": p['Location'] }
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
                "date": f["Date"],
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
        if token['price_change_percentage_24h'] is None:
            percent_change = 0
        else:
            percent_change = round(token['price_change_percentage_24h'], 2)
        url = coingecko_base_url + token['id']
        token_dict = {"image": token['image'], "symbol": token['symbol'].upper(), "price_usd": round(token['current_price'],5), "percent_change": percent_change, "url": url}
        token_list.append(token_dict)
    
    return token_list