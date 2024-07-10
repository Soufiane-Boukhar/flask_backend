from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER', 'avnadmin')}:"
    f"{os.getenv('MYSQL_PASSWORD', 'AVNS_wWoRjEZRmFF5NgjGCcY')}@"
    f"{os.getenv('MYSQL_HOST', 'mysql-1fb82b3b-boukhar-d756.e.aivencloud.com')}:"
    f"{os.getenv('MYSQL_PORT', '20744')}/"
    f"{os.getenv('MYSQL_DB', 'defaultdb')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from .views import *

if __name__ == '__main__':
    app.run(debug=True)
