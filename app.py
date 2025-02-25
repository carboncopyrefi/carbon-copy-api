from flask import Flask, jsonify, request, json
import random, datetime, categories, projects, assessment, refi_landscape, external, utils, dashboard, keys, config, os
from flask_cors import CORS
from feedwerk.atom import AtomFeed

app = Flask(__name__)
CORS(app, resources={r"/response*": {"origins": "*"}})

# Routes
@app.route('/articles', methods=['GET'])
def articles():
    data = external.feed()
    random.shuffle(data)
    response = jsonify(data[0:8])
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/articles/partner', methods=['GET'])
def partnerArticles():
    data = external.carbon_advisor()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/projects/<slug>', methods=['GET'])
def projectDetails(slug):
    data = projects.project_details(slug)
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/projects/<slug>/content', methods=['GET'])
def projectContent(slug):
    data = projects.project_content(slug)
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response, 200

@app.route('/projects/top', methods=['GET'])
def topProjects():
    data = projects.top_projects_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/projects', methods=['GET'])
def projectsList():
    data = projects.projects_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/project-json', methods=['GET'])
def projectsJson():
    data = projects.project_json()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/projects/categories/<slug>', methods=['GET'])
def categoryProjects(slug):
    data = categories.category_projects(slug)
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/projects/categories/tokens', methods=['GET'])
def categoryProjectTokens():
    tokens = request.args.getlist('ids')[0]
    if tokens != "":
        data = categories.category_project_tokens(tokens)
        response = jsonify(data)
        response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
        return response
    else:
        return ""

@app.route('/dashboard', methods=['GET'])
def refiDashboard():
    data = dashboard.get_dashboard_data()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/landscape', methods=['GET'])
def refiLandscape():
    data = refi_landscape.landscape()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/people', methods=['GET'])
def peopleList():
    data = refi_landscape.people_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/tokens', methods=['GET'])
def tokenList():
    data = external.token_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/news', methods=['GET'])
def news():
    data = refi_landscape.news_list()
    response = jsonify(data[0:10])
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/feed', methods=['GET'])
def refiFeed():
    data = refi_landscape.news_list()
    news_feed = AtomFeed(title='ReFi News', feed_url=request.url, url=request.url_root)
    for item in data:
        news_feed.add(item['title'],content_type='html',author=item['company'],url=item['link'],updated=item['date'],published=item['date'])
    return news_feed.get_response()

@app.route('/newsletter', methods=['GET'])
def newsletterParagraph():
    data = external.newsletter()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/refirecap', methods=['GET'])
def refiRecap():
    data = external.refi_recap()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/events', methods=['GET'])
def events():
    data = external.upcoming_events()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/opportunities', methods=['GET'])
def opportunities():
    data = refi_landscape.opportunity_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/knowledge', methods=['GET'])
def knowledge():
    data = refi_landscape.knowledge_list()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/refi-weekly', methods=['GET'])
def refiWeekly():
    data = refi_landscape.refi_weekly()
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/refi-weekly/<slug>', methods=['GET'])
def refiWeeklyEpisode(slug):
    data = refi_landscape.refi_weekly_episode(slug)
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/impact/feed', methods=['GET'])
def impactFeed():
    file_path = os.path.join(os.getcwd(), 'api', 'assets', 'impact_feed.json')
    with open(file_path, "r") as _file:
        data = json.load(_file)
    response = jsonify(data)
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response


@app.route('/cast/news', methods=['POST'])
def castNews():
    if request.method == 'POST' and request.data is not None:

        content = json.loads(request.data)

        return utils.cast_to_farcaster(content)
    else:
        return "Error", 403


@app.route('/questions', methods=['GET'])
def questions():
    response = assessment.survey_questions()
    response.headers.add(config.ACCESS_CONTROL_ORIGIN_HEADER, config.ACCESS_CONTROL_ORIGIN_VALUE)
    return response

@app.route('/response', methods=['POST'])
def response():
    if request.method == 'POST' and request.headers.get('token') == keys.SURVEY_ACCESS_TOKEN and request.data is not None:
        data = json.loads(request.data)
        _name = data['name']
        _company = data['company']
        _survey = str(datetime.date.today().year)
        _email = data['email']
        _answers = data['picked']
        _questions = data['questions']

        result = assessment.save_assessment(data, _name, _company, _survey, _email, _answers, _questions)

        if result != "Error":
            return result, 200
        else:
            return result, 500

    else:
        return "", 400

if __name__ == "__main__":
    app.run()
