from flask import jsonify, request, make_response
from . import app, mysql

@app.route('/contacts', methods=['GET', 'OPTIONS'])
def get_contacts():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET,OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM contacts")
    rows = cur.fetchall()
    cur.close()

    contacts = []
    for row in rows:
        contacts.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3]
        })

    response = jsonify({'contacts': contacts})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
