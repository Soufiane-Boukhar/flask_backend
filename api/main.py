import os
import logging
from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    app.logger.debug('Index route called')
    return jsonify({'message': 'Hello, World!'})

@app.route('/data', methods=['GET'])
def get_data():
    app.logger.debug('Data route called')
    try:
        connection = mysql.connector.connect(
            host='mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
            user='avnadmin',
            password='AVNS_wWoRjEZRmFF5NgjGCcY',
            database='defaultdb'
        )
        cursor = connection.cursor()
        app.logger.debug('Database connection established')
        cursor.execute("SELECT * FROM contacts LIMIT 10") 
        result = cursor.fetchall()
        app.logger.debug('Query executed successfully')
        cursor.close()
        connection.close()
        return jsonify(result)
    except mysql.connector.Error as err:
        app.logger.error(f'Database error: {err}')
        return jsonify({'error': str(err)}), 500

if __name__ == "__main__":
    app.run()
