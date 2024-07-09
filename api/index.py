from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    subject = db.Column(db.String(255))
    message = db.Column(db.String(255))

@app.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        contacts = Contact.query.all()
        return jsonify({'contacts': [{'id': contact.id, 'full_name': contact.full_name, 'email': contact.email, 'subject': contact.subject, 'message': contact.message} for contact in contacts]})
    except Exception as e:
        return jsonify({'error': 'Database query error', 'details': str(e)}), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method Not Allowed'}), 405

@app.route('/', methods=['GET'])
def home():
    return "hello world"

if __name__ == '__main__':
    app.run(debug=True)
