from flask import jsonify, request, make_response
from . import app, db

@app.route('/contacts', methods=['GET', 'OPTIONS'])
def get_contacts():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    result = db.engine.execute("SELECT * FROM contacts")
    contacts = [
        {'id': row['id'], 'name': row['name'], 'email': row['email'], 'phone': row['phone']}
        for row in result
    ]

    response = jsonify({'contacts': contacts})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/', methods=['GET'])
def Home():
    return 'Home page'