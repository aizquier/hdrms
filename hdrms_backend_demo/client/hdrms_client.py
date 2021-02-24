import json
import base64
import os
import requests


def new_set(params={}):
    r = requests.get("http://localhost:8000/")

    q = requests.post('http://localhost:8000/set/',
                      headers={
                          'Content-Type': 'application/json',
                          "X-CSRFToken": r.cookies['csrftoken']
                      },
                      cookies=r.cookies,
                      data=json.dumps(params)
                      )
    status = q.json()
    if status['error'] == False:
        print('A set with id "%s" has been created' % status['setid'])


def ingest_file(setid, filename):
    r = requests.get("http://localhost:8000/")
    with open(filename, 'rb') as f:
        payload = base64.b64encode(f.read()).decode('utf-8')

    data = {
        'mimetype': 'image/jpeg',
        'filename': os.path.basename(filename),
        'payload': payload
    }

    q = requests.post(
        "http://localhost:8000/set/%s" % setid,
        headers={
            'Content-Type': 'application/json',
            "X-CSRFToken": r.cookies['csrftoken']
        },
        cookies=r.cookies,
        data=json.dumps(data)
    )

    print(q.text)


def delete(setid):
    r = requests.get("http://localhost:8000/")
    q = requests.delete(
        "http://localhost:8000/set/%s" % setid,
        headers={
            'Content-Type': 'application/json',
            "X-CSRFToken": r.cookies['csrftoken']
        },
        cookies=r.cookies,
    )

    print(q.text)