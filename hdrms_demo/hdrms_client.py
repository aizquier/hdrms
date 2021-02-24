import json
import base64
import os
import requests
import json
import pysolr
import api
from lxml import etree
from IPython.display import HTML, display


SetML1 = api.SetManagerL1()
SetML2 = api.SetManagerL2()
SetML3 = api.SetManagerL3()


def list_sets():
    #r = requests.get("http://localhost:8000/set").json()
    global SetML1
    r = SetML1.get()

    #print(r)

    html="<table><tr><th>SetID</th><th>Title</th></tr>%s</table>" % "".join(
         [
            "<tr><td>%s</td><td>%s</td></tr>" % (_m['setid'].split('#')[1], _m['title'])
             for _m in r['setlist']
         ]
    )
    display(HTML(html))

def show_set(setid):
    #r = requests.get("http://localhost:8000/set/%s" % setid)
    report = SetML2.get(setid)
    table = "<table><tr><th>ResID</th><th>Filename</th></tr>"
    # try:
    #     report = r.json()
    # except:
    #     print(r.text)
    #     return

    for _m in report:
        resid = _m['resid'].split('#')[1]
        table += '<tr><td>%s</td><td><a href="http://localhost:8080/rest/%s/%s" target="_blank">%s</a></td></tr>' % (resid, setid, resid, _m['filename'])
    table += "</table>"
    table += "</table>"
    display(HTML(table))


def create_set(title, setid=None):
    global SetML1
    params = {
        'title': title,
        'setid': setid
    }

    r = SetML1.set_l1_post(params)
    print(r)

    # r = requests.get("http://localhost:8000/")
    # q = requests.post(
    #     'http://localhost:8000/set/',
    #     headers={
    #       'Content-Type': 'application/json',
    #       "X-CSRFToken": r.cookies['csrftoken']
    #     },
    #     cookies=r.cookies,
    #     data=json.dumps(params)
    # )

    #print(q.text)
    # try:
    #     status = q.json()
    # except:
    #     print(status.text)
    #     return
    #
    # if status['error'] == False:
    #     print('A set with id "%s" has been created' % status['setid'])
    #
    # return status['setid']

def add_to_set(setid, filename):
    global SetML2
    #r = requests.get("http://localhost:8000/")
    with open(filename, 'rb') as f:
        # payload = base64.b64encode(f.read()).decode('utf-8')
        payload = f.read()

    data = {
        'mimetype': 'image/jpeg',
        'filename': os.path.basename(filename),
        'payload': payload
    }

    q = SetML2.post(setid, data)
    # q = requests.post(
    #     "http://localhost:8000/set/%s" % setid,
    #     headers={
    #         'Content-Type': 'application/json',
    #         "X-CSRFToken": r.cookies['csrftoken']
    #     },
    #     cookies=r.cookies,
    #     data=json.dumps(data)
    # )

    #print(q)
    return q


def delete(setid):
    global SetML2
    # r = requests.get("http://localhost:8000/")
    # q = requests.delete(
    #     "http://localhost:8000/set/%s" % setid,
    #     headers={
    #         'Content-Type': 'application/json',
    #         "X-CSRFToken": r.cookies['csrftoken']
    #     },
    #     cookies=r.cookies,
    # )

    q = SetML2.delete(setid)
    print(q.text)


def list_trCollections():
    r = requests.post(
        'https://transkribus.eu/TrpServer/rest/auth/login',
        data={
            'user': 'user@mail.com',
        'pw': base64.b64decode('XXXXXXXXX==').decode()
        }
    )

    q = requests.get('https://transkribus.eu/TrpServer/rest/collections/list', cookies=r.cookies)
    table = "<table><tr><th>ColID</th><th>Title</th></tr>"
    for _m in q.json():
        table += "<tr><td>%s</td><td>%s</td></tr>" % (_m['colId'], _m['colName'])
    table += "</table>"
    display(HTML(table))


def list_trDocs(colID):
    r = requests.post(
        'https://transkribus.eu/TrpServer/rest/auth/login',
        data={
            'user': 'user@mail.com',
            'pw': base64.b64decode('XXXXXX==').decode()
        }
    )

    q = requests.get('https://transkribus.eu/TrpServer/rest/collections/%d/list' % colID, cookies = r.cookies)

    table = "<table>"
    table += "<tr><th>DocID</th><th>Title</th></tr>"
    for _m in q.json():
        table += "<tr><td>%s</td><td>%s</td></tr>" % (_m['docId'], _m['title'])
    table += "</table>"
    display(HTML(table))


def showTr(url):
    ns = {'pp': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
    trans = requests.get(url)
    root = etree.fromstring(trans.text.encode('utf-8'))
    text = ""
    for a in root.findall('.//pp:Page/pp:TextRegion/pp:TextEquiv/pp:Unicode', namespaces=ns):
        text += a.text
    return text

def extractTr(trans):
    ns = {'pp': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
    root = etree.fromstring(trans.text.encode('utf-8'))
    text = ""
    for a in root.findall('.//pp:Page/pp:TextRegion/pp:TextEquiv/pp:Unicode', namespaces=ns):
        text += a.text
    return text

def show_trDoc(colID, docID):
    r = requests.post(
        'https://transkribus.eu/TrpServer/rest/auth/login',
        data={
            'user': 'user@mail.com',
            'pw': base64.b64decode('XXXXXXX==').decode()
        }
    )

    q = requests.get('https://transkribus.eu/TrpServer/rest/collections/%s/%s/fulldoc' % (colID, docID), cookies=r.cookies)

    pages = q.json()

    table = "<table>"
    table += "<tr><th></th><th>PageNo</th><th>Filename</th><th>Last transcription</th><th>Text</th></tr>"

    for page in pages['pageList']['pages']:
        thumbnail = '<a href="%s" target="_blank"><img src="%s" /></a>' % (page['url'], page['thumbUrl'])
        # for transcript in page['tsList']['transcripts']:
        #     print("   ", transcript['timestamp'], transcript['status'], transcript['url'])

        timestamps = {_m['timestamp']: _m for _m in page['tsList']['transcripts']}
        maxts = max([_m for _m in timestamps])
        last_transcription = timestamps[maxts]
        tr_html = '<a href="%s" target="_blank">%s</a>' % (last_transcription['url'], last_transcription['status'])
        pageurl = '<a href="%s" target="_blank">%s</a>' % (page['url'], page['imgFileName'])
        trans = showTr(last_transcription['url'])
        table += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (thumbnail, page['pageNr'], pageurl, tr_html, trans)

    table += "</table>"
    display(HTML(table))

def importDoc(colID, docID):
    mysolr = pysolr.Solr('http://localhost:8983/solr/hdrms/')
    #csrf = requests.get("http://localhost:8000/")
    setid = 'setid.%s' % colID
    resid = 'resid.%s' % docID

    print("Getting doc metadata...")
    r = requests.post(
        'https://transkribus.eu/TrpServer/rest/auth/login',
        data={
            'user': 'aizquier@gmail.com',
            'pw': base64.b64decode('XXXXX==').decode()
        }
    )

    q = requests.get(
        'https://transkribus.eu/TrpServer/rest/collections/%s/%s/fulldoc' % (colID, docID),
        cookies=r.cookies
    )

    doc = q.json()

    create_set(doc['md']['title'], setid=setid)

    for page in doc['pageList']['pages']:
        #print("Importing %s..." % (page['imgFileName']))
        timestamps = {_m['timestamp']: _m for _m in page['tsList']['transcripts']}
        maxts = max([_m for _m in timestamps])
        last_transcription = timestamps[maxts]

        transcript = requests.get(last_transcription['url'])
        #print(transcript.text)
        #payload = base64.b64encode(transcript.text.encode('utf-8')).decode('utf-8')
        payload = transcript.text.encode('utf-8')
        data = {
            'mimetype': 'application/xml',
            'filename': page['imgFileName'].split('.')[0],
            'payload': payload
        }

        # resid = q.json()['resid']

        q = SetML2.post(setid, data)
        resid = q['resid']

        newid = "%s-%s" % (setid, resid)
        mysolr.add(
            [
                {
                    "id": newid,
                    "pid": newid,
                    "title": "%s/%s" %(doc['md']['title'], page['imgFileName'].split('.')[0]),
                    "text": extractTr(transcript).split(' '),
                },
            ]
        )

        #print(transcript.text.split(' '))

