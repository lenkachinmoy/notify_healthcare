import ConfigParser
import datetime
import json
import os
import time
from bson import json_util
from flask import Flask, request, render_template, jsonify
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from libs.reconnect import autoreconnect_retry

db_config = ConfigParser.RawConfigParser()
db_config.read('config/db.cfg')

# MONGODB_HOST = "localhost"
MONGODB_HOST = os.environ['MONGODB_HOST']  # TODO: read from config?
MONGODB_PORT = db_config.getint('MONGODB', 'PORT_NO')

app = Flask(__name__)
app.config.from_object(__name__)

connection = MongoClient(MONGODB_HOST, MONGODB_PORT)
for i in range(100):
    try:
        connection.admin.command('ismaster')
        break
    except ConnectionFailure:
        time.sleep(pow(2, i))
        connection = MongoClient(MONGODB_HOST, MONGODB_PORT)
        print("Connection to db failed. Start MongoDB instance.")

db = connection[db_config.get('MONGODB', 'DATABASE_NAME')]
collection = db[db_config.get('MONGODB', 'COLLECTION_NAME')]


# TODO: make use of
def max_length(length):
    def validate(value):
        if len(value) <= length:
            return True
        # must have %s in error format string to have mongokit place key in there
        raise ValidationError('%s must be at most {} characters long'.format(length))

    return validate


@app.route('/')
def form():
    return render_template('form_sumbit.html')


@autoreconnect_retry
@app.route('/get_info', methods=['GET'])
def get_info():
    name = request.args.get('name')
    d = []
    for patient in connection.Patient.find({'name': name}):
        for med in patient.medicines:
            d.append(med['time'])
    return json_util.dumps(d)


@autoreconnect_retry
@app.route('/save', methods=['POST'])
def save():
    # get data from form
    name = request.form['name']
    ph_no = request.form['ph_no']
    med_name = request.form['med_name']
    med_qty = request.form['med_qty']
    try:
        med_time = datetime.datetime.strptime(request.form['time'], '%H:%M')
    except ValueError:
        print("time field empty")

    # construct document from data
    patient = {"name": name,
               "ph_no": ph_no,
               "medicines": [{"name": med_name,
                              "qty": med_qty,
                              "time": [med_time]
                              }]
               }
    collection.insert_one(patient)

    sanitized = json.loads(json_util.dumps(patient))
    return jsonify(sanitized)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
