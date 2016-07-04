#!/usr/bin/python
import sys, json, xmpp, random, string
from flask import Flask, make_response, jsonify

app = Flask(__name__)

SERVER = 'gcm.googleapis.com'
PORT = 5236
USERNAME = "562766010128"
PASSWORD = "AIzaSyBUEVVKBM3L93C92QMKDY7lfEEzNYTQuas"
REGISTRATION_ID = "emkjKXey7RM:APA91bFA1DddGcSZZPr4rSqH71aQng5yelJ9lepQQS5-KZDMRMaqjAZm-2vihSMGZQqe6ef-VWWHXF250iOY21h9Q_TESu3q4L_6pAkKSq272NW0vp10I6-rVjW2m-KaaJ1-TIjU7DqO"

unacked_messages_quota = 100
send_queue = []

# Return a random alphanumerical id
def random_id():
  rid = ''
  for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
  return rid

def message_callback(session, message):
  print "inside upstream message"
  global unacked_messages_quota
  gcm = message.getTags('gcm')
  if gcm:
    gcm_json = gcm[0].getData()
    msg = json.loads(gcm_json)
    if not msg.has_key('message_type'):
      # Acknowledge the incoming message immediately.
      send({'to': msg['from'],
            'message_type': 'ack',
            'message_id': msg['message_id']})
      # Queue a response back to the server.
      if msg.has_key('from'):
        # Send a dummy echo response back to the app that sent the upstream message.
        send_queue.append({'to': msg['from'],
                           'message_id': random_id(),
                           'data': {'pong': 1}})
    elif msg['message_type'] == 'ack' or msg['message_type'] == 'nack':
      unacked_messages_quota += 1

def send(json_dict):
  print "inside sending downstream message"
  template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
  client.send(xmpp.protocol.Message(
      node=template.format(client.Bind.bound[0], json.dumps(json_dict))))

def flush_queued_messages():
  global unacked_messages_quota
  while len(send_queue) and unacked_messages_quota > 0:
    print "flushing queued messages"
    send(send_queue.pop(0))
    unacked_messages_quota -= 1

client = xmpp.Client('gcm.googleapis.com')
client.connect(server=(SERVER,PORT), secure=1, use_srv=False)
auth = client.auth(USERNAME, PASSWORD)
if not auth:
  print 'Authentication failed!'
  sys.exit(1)

print "auth success"
client.RegisterHandler('message', message_callback)
print "registered handler"

send_queue.append({'to': REGISTRATION_ID,
                   'message_id': 'reg_id',
                   'data': {'message_destination': 'RegId',
                            'message_id': random_id()}})

#while True:
#  client.Process(1)
#  flush_queued_messages()

@app.route('/')
def root():
    return make_response(jsonify({'result': 'success'}), 200)