import os
from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})

@app.route('/data',methods=['GET'])
def get_data():
    connection = mysql.connector.connect(
        host='mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
        user='avnadmin',
        password='AVNS_wWoRjEZRmFF5NgjGCcY',
        database='defaultdb'
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM contacts")
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(result)

if __name__ == "__main__":
    app.run()
