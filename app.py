from flask import Flask, jsonify, request, json
import feedparser, requests, random, datetime, os
from flask_cors import CORS
from feedwerk.atom import AtomFeed

app = Flask(__name__)
CORS(app, resources={r"/response*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['TOKEN'] = 'PS91RoTw8hOvLgK4TyeTsEKv13ZFUhQR'

category = "environment"
base_company_api = "https://api.baserow.io/api/database/rows/table/171320/"
baserow_token = 'Token RPlLXKDgBX8TscVGjKjI33djLk89X1qf'
projectnews_api= "https://api.baserow.io/api/database/rows/table/173781/?user_field_names=true"
events_api = "https://api.baserow.io/api/database/rows/table/203056/?user_field_names=true"
access_control_origin_header = "Access-Control-Allow-Origin"
access_control_origin_value = "*"
gitcoin_graphql = "https://grants-stack-indexer-v2.gitcoin.co/graphql"
# fundraising_api = "https://api.baserow.io/api/database/rows/table/306630/"
fundraising_api = "https://api.baserow.io/api/database/rows/table/306630/?user_field_names=true&filter__field_2209789__link_row_has="




def execute_graphql_query(query):
    response = requests.post(gitcoin_graphql, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run with a {response.status_code}. {response.text}")

def get_baserow_data(project_id):
    url = fundraising_api + project_id
    headers = {
        'Authorization': baserow_token,
        'Content-Type' : 'application/json'

    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch Baserow data with status {response.status_code}. {response.text}")

class TopProject:
    def __init__(self, name, description, sectors, id, slug, protocol):
        self.name = name
        self.description = description
        self.sectors = sectors
        self.id = id
        self.slug = slug
        self.protocol = protocol

class Project:
    def __init__(self, id, slug, name, description_short, links, sectors, description_long, categories, logo, team, coverage, news, top16, location, protocol, responses,fundraising):
        self.id = id
        self.slug = slug
        self.name = name
        self.description_short = description_short
        self.links = links
        self.sectors = sectors
        self.description_long = description_long
        self.categories = categories
        self.logo = logo
        self.team = team
        self.coverage = coverage
        self.news = news
        self.top16 = top16
        self.location = location
        self.protocol = protocol
        self.response = responses
        self.fundraising = fundraising


def project_details(slug):
    api = base_company_api + "?user_field_names=true&filter__field_1248804__equal=" + slug
    links_api = "https://api.baserow.io/api/database/rows/table/171328/?user_field_names=true&filter__field_1139485__link_row_has="
    l_dict = {}
    l_list = []
    coverage_api = "https://api.baserow.io/api/database/rows/table/171322/?user_field_names=true&filter__field_1139490__link_row_has="
    c_dict = {}
    c_list = []
    news_api = "https://api.baserow.io/api/database/rows/table/173781/?user_field_names=true&filter__field_1156934__link_row_has="
    n_dict = {}
    n_list = []
    response_api = "https://api.baserow.io/api/database/rows/table/265286/?user_field_names=true&filter__field_1887993__link_row_has="
    r_dict = {}
    r_list = []


    data = requests.get(
        api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    result = data.json()['results'][0]
    project_id = str(result['id'])
    
    try:
        baserow_data = get_baserow_data(project_id)
        fundraising_list = []
        fundraising_dict = {}
        getcoin_list = []
        
        for entry in baserow_data['results']:
            fundraising_dict = {"chain_id": entry['Chain ID'], "project_id": entry['Project ID']}
            fundraising_list.append(fundraising_dict)
       

        for f in fundraising_list:
            chain_id = f['chain_id']
            gitcoin_project_id = f['project_id']

            query = f"""
            query MyQuery {{
            project(
                chainId: {chain_id}
                id: "{gitcoin_project_id}"
            ) {{
                applications(filter: {{status: {{equalTo: APPROVED}}}}) {{
                id
                round {{
                    id
                    donationsStartTime
                    roundMetadata
                }}
                status
                uniqueDonorsCount
                totalDonationsCount
                totalAmountDonatedInUsd
                }}
            }}
            }}
            """
            resultql = execute_graphql_query(query)
            for app in resultql['data']['project']['applications']:
                formatted_response = [
                    {
                        "Year": app['round']['donationsStartTime'].split('-')[0],  # Assuming donationsStartTime is in format YYYY-MM-DD
                        "Round name": app['round']['roundMetadata'].get('name', 'N/A'),  # Assuming roundMetadata has a 'name' key
                        "Total donated USD": app['totalAmountDonatedInUsd'],
                        "Total contributors": app['totalDonationsCount'],
                        "Unique contributors": app['uniqueDonorsCount']
                    }
                ]
                getcoin_list.append(formatted_response)
            
      
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500






    links_data = requests.get(
        links_api + project_id,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    links_result = links_data.json()['results']

    for l in links_result:
        l_dict = {"platform": l['Platform']['value'], "url": l['URL']}
        l_list.append(l_dict)


    coverage_data = requests.get(
        coverage_api + project_id,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    coverage_result = coverage_data.json()['results']

    for a in coverage_result:
        published_time = datetime.datetime.strptime(a['Publish Date'], "%Y-%m-%d")
        c_dict = {"headline": a['Headline'], "publication": a['Publication']['value'], "url": a['Link'], "date": published_time}
        c_list.append(c_dict)

    sorted_c_list = sorted(c_list, key=lambda d: d['date'], reverse=True)

    news_data = requests.get(
        news_api + project_id,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    news_result = news_data.json()['results']

    for n in news_result[0:5]:
        published_time = datetime.datetime.strptime(n['Created on'], "%Y-%m-%dT%H:%M:%S.%fZ")
        n_dict = {"headline": n['Headline'], "snippet": n['Snippet'], "url": n['Link'], "date": published_time}
        n_list.append(n_dict)

    sorted_n_list = sorted(n_list, key=lambda d:d['date'], reverse=True)

    response_data = requests.get(
        response_api + project_id,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    response_result = response_data.json()['results']

    for r in response_result:
        r_dict = {"survey": r['Survey'][0]['value']}
        r_list.append(r_dict)

    sorted_r_list = sorted(r_list, key=lambda d:d['survey'], reverse=True)

    project = Project(project_id, result['Slug'], result['Name'], result['One-sentence Description'], l_list, result['Sector'], result['Description'], result['Category'], result['Logo'], result['Founders'], sorted_c_list, sorted_n_list, result['Top 16'], result['Location'], result['Protocol'], sorted_r_list,getcoin_list)
    project_dict = vars(project)

    return project_dict

def top_projects_list():
    p_list = []

    api = base_company_api + "?user_field_names=true&filter__field_1147468__boolean=true"
    data = requests.get(
        api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    result = data.json()
    for item in result['results']:
        project = TopProject(item['Name'], item['One-sentence Description'], item['Sector'], item['id'], item['Slug'], item['Location'])
        project_dict = vars(project)
        p_list.append(project_dict)

    return p_list

def projects_list():
    p_list = []

    api = base_company_api + "?user_field_names=true&filter__field_1248804__not_empty&size=200"

    data = requests.get(
        api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    result = data.json()
    for item in result['results']:
        s_list = []
        protocol_list = []
        for sector in item['Sector']:
            s_list.append(sector['value'])

        for protocol in item['Protocol']:
            protocol_list.append(protocol['value'])

        project = TopProject(item['Name'], item['One-sentence Description'], s_list, item['id'], item['Slug'], protocol_list)
        project_dict = vars(project)
        p_list.append(project_dict)

    sorted_p_list = sorted(p_list, key=lambda x:x['name'].lower())

    return sorted_p_list

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
        week_api = projectnews_api + "&filter__field_1156936__date_after_or_equal=" + start + "T00:00:01Z" + "&filter__field_1156936__date_before_or_equal=" + end + "T23:59:59Z" + "&filter_type=AND&order_by=-Created on"

        data = requests.get(
            week_api,
            headers={
                'Content-Type' : 'application/json',
                'Authorization': baserow_token
            }
        )

    else:
        data = requests.get(
            projectnews_api + "&size=50&order_by=-Created on",
            headers={
                'Content-Type' : 'application/json',
                'Authorization': baserow_token
            }
        )

    result = data.json()

    for item in result['results']:
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

    api = events_api + "&filter__field_1394864__date_after=" + str(datetime.date.today())
    data = requests.get(
        api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    result = data.json()
    for item in result['results']:
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

    p_api = base_company_api + '?user_field_names=true&include=Name&size=' + page_size
    p_data = requests.get(
        p_api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    p_result = p_data.json()['results']
    for p in p_result:
        p_list.append(p['Name'])

    if p_data.json()['count'] > int(page_size):
        p2_data = requests.get(
            p_data.json()['next'],
            headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
            }
        )

        p2_result = p2_data.json()['results']
        for p in p2_result:
            p_list.append(p['Name'])

    sorted_p_list = sorted(p_list, key=str.casefold)

    api = "https://api.baserow.io/api/database/rows/table/265287/?user_field_names=true"
    data = requests.get(
        api,
        headers={
            'Content-Type' : 'application/json',
            'Authorization': baserow_token
        }
    )

    result = data.json()
    for item in result['results']:
        question = SurveyQuestion(item['Name'], item['Text'], item['Category']['value'], item['Tip'], item['Answer 1'], item['Answer 2'], item['Answer 3'])
        question_dict = vars(question)
        q_list.append(question_dict)

    sorted_q_list = sorted(q_list, key=lambda d: d['name'])

    return jsonify({
        'projects': sorted_p_list,
        'questions': sorted_q_list
    })


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




