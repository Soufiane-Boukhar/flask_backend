from flask import Flask, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = "mysql-1fb82b3b-boukhar-d756.e.aivencloud.com"
app.config['MYSQL_USER'] = "avnadmin"
app.config['MYSQL_PASSWORD'] = "AVNS_wWoRjEZRmFF5NgjGCcY"
app.config['MYSQL_DB'] = "defaultdb"

mysql = MySQL(app)

@app.route('/contacts', methods=['GET'])
def get_contacts():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM contacts')
        data = cur.fetchall()  
        cur.close()
        return jsonify({'contacts': data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
