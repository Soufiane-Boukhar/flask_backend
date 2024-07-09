import os
import logging
import time
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
        start_time = time.time()
        
        # Establish database connection
        connection = mysql.connector.connect(
            host='mysql-1fb82b3b-boukhar-d756.e.aivencloud.com',
            user='avnadmin',
            password='AVNS_wWoRjEZRmFF5NgjGCcY',
            database='defaultdb'
        )
        app.logger.debug(f'Database connection established in {time.time() - start_time} seconds')
        
        cursor = connection.cursor()
        
        # Execute the query
        query_start_time = time.time()
        cursor.execute("SELECT * FROM contacts LIMIT 10")
        result = cursor.fetchall()
        app.logger.debug(f'Query executed in {time.time() - query_start_time} seconds')
        
        cursor.close()
        connection.close()
        
        app.logger.debug(f'Total time for /data route: {time.time() - start_time} seconds')
        return jsonify(result)
    except mysql.connector.Error as err:
        app.logger.error(f'Database error: {err}')
        return jsonify({'error': str(err)}), 500

if __name__ == "__main__":
    app.run()
