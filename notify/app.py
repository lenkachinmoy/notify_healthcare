import ConfigParser
import os
import sched
import time
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from libs.reconnect import autoreconnect_retry

db_config = ConfigParser.RawConfigParser()
sms_config = ConfigParser.RawConfigParser()
db_config.read('config/db.cfg')
sms_config.read('config/hsp.cfg')

MONGODB_HOST = os.environ['MONGODB_HOST']  # TODO: read from config?
# MONGODB_HOST = '172.17.0.2'
MONGODB_PORT = db_config.getint('MONGODB', 'PORT_NO')
HSP_API_KEY = sms_config.get('HSPSMS', 'API_KEY')
hsp_user = sms_config.get('HSPSMS', 'USERNAME')
hsp_sender = sms_config.get('HSPSMS', 'SENDER_NAME')
sched_interval = eval(sms_config.get('HSPSMS', 'INTERVAL'))
s = sched.scheduler(time.time, time.sleep)

client = MongoClient(MONGODB_HOST, MONGODB_PORT)
for i in range(100):
    try:
        client.admin.command('ismaster')
        break
    except ConnectionFailure:
        time.sleep(pow(2, i))
        client = MongoClient(MONGODB_HOST, MONGODB_PORT)
        print("Connection to db failed. Start Mongodb instance.")

db = client[db_config.get('MONGODB', 'DATABASE_NAME')]
# db = client['healthcare']
collection = db[db_config.get('MONGODB', 'COLLECTION_NAME')]


@autoreconnect_retry
def send_sms():
    print "Looking up db at: ", datetime.now()
    for patient in collection.find():
        for med in patient['medicines']:
            for t in med['time']:
                time_now = datetime.now()
                if time_now.hour == t.hour:
                    message = patient['name'] + ", time for " + med['name'] + " quantity:" + med[
                        'qty'] + " at time: " + str(t.hour) + ':' + str(t.minute)
                    url = "http://sms.hspsms.com/sendSMS?username=" + hsp_user + "&message=" \
                    + message + "&sendername=" + hsp_sender + "&smstype=TRANS&numbers=" + \
                          patient['ph_no'] + "&apikey=" + HSP_API_KEY
                    # r = requests.get(url)
                    #print r.text
                    print message


if __name__ == "__main__":
    while True:
        s.enter(1, 1, send_sms, ())
        s.enter(sched_interval, 1, send_sms, ())
        s.run()
