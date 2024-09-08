import utils, requests, os, config
from flask import current_app as app, json, jsonify

baserow_table_company = config.BASEROW_TABLE_COMPANY
baserow_table_survey_question = config.BASEROW_TABLE_SURVEY_QUESTION

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

def save_assessment(data, _name, _company, _survey, _email, _answers, _questions):
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