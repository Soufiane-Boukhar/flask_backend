from flask import Flask, jsonify
from flask_mysqldb import MySQL
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'mysql-1fb82b3b-boukhar-d756.e.aivencloud.com')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 20744))
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'avnadmin')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'AVNS_wWoRjEZRmFF5NgjGCcY')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'defaultdb')


mysql = MySQL(app)

from .views import *

if __name__ == '__main__':
    app.run(debug=True)
