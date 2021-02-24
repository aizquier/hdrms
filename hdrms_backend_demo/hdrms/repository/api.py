import io
import json
import uuid
import base64
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.http import JsonResponse
from hdrms import settings
from .models.SemanticWeb import Fedora4
from .models.SemanticWeb import Blazegraph
from .models.SemanticWeb import Exceptions as SWExceptions

UNIQID_MAXDIGITS = 10

def issue_csrf_key(request, *args, **kwargs):
    return render(request, 'csrf.html', {})


def HDRMSJsonResponse(*args, **kwargs):
    res = JsonResponse(*args, **kwargs)
    res['Access-Control-Allow-Origin'] = '*'
    return res


def HDRMSHttpResponse(*args, **kwargs):
    res = HttpResponse(*args, **kwargs)
    res['Access-Control-Allow-Origin'] = '*'
    return res


class HDRMSRepository(object):

    def uniqid(self):
        return "".join(str(uuid.uuid4()).split('-'))[0:UNIQID_MAXDIGITS]

    def __init__(self):
        hdrms_rdf_namespaces = {
            'setid': 'http://hdrms.org/setid#',
            'resid': 'http://hdrms.org/resid#',
            'hdrmsPred': 'http://hdrms.org/predicates#',
            'hdrmsDefs': 'http://hdrms.org/definitions#'
        }

        self.fcrepo = Fedora4.Repository(settings.credentials.FEDORA_ROOT)
        self.blazegraph = Blazegraph.TripleStore(settings.credentials.BLAZEGRAPH_ROOT, 'hdrms')

        for prefix, ns in hdrms_rdf_namespaces.items():
            self.blazegraph.RDFNamespaces.add(prefix, ns)



class SetManagerL1(HDRMSRepository):

    def get(self, request, *args, **kwargs):
        query = '''
        select ?setid  ?title where { 
            ?setid a hdrmsDefs:set .
            ?setid hdrmsPred:has-title ?title .
        }
        '''
        r = self.blazegraph.query(query).json()
        setlist = {
            'setlist': [
                {'setid': _m['setid']['value'], 'title': _m['title']['value']}
                for _m in r['results']['bindings']
            ]
        }
        return HDRMSJsonResponse(setlist)

        # mock_data = {
        #     'setid': '47c15fae-775f-11e8-bddc-5f78499fac5d',
        #     'title': 'A title',
        #     'items': [
        #         {
        #             'resid': '1',
        #             'mimetype': 'image/jpeg',
        #             'filename': 'scan_001.jpg',
        #             'payload': 'qwertyuiop[]'
        #         },
        #         {
        #             'resid': '2',
        #             'mimetype': 'image/jpeg',
        #             'filename': 'scan_002.jpg',
        #             'payload': 'qwertyuiop[]'
        #         },
        #     ]
        # }
        #
        # return HDRMSJsonResponse({'method': 'get', 'level': 1})


    def post(self, request, *args, **kwargs):
        set_properties = {
            **{
                'setid': None,
                'title': 'Unknown %s'
            },
            **json.loads(request.body.decode('utf-8'))
        }

        if set_properties['setid'] is None:
            set_properties['setid'] = "id.%s" % self.uniqid()

        try:
            self.fcrepo.create_container(set_properties['setid'])
        except SWExceptions.ResourceAlreadyExists:
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s already exists' % set_properties['setid']},
                status=406
            )

        ttl = self.blazegraph.RDFNamespaces.as_turtle()
        ttl += 'setid:%s a hdrmsDefs:set .\n' % set_properties['setid']
        ttl += 'setid:%s hdrmsPred:has-title "%s" . \n' % (set_properties['setid'], set_properties['title'])

        self.blazegraph.send_ttl(ttl)

        return HDRMSJsonResponse(
            {
                'setid': set_properties['setid'],
                'error': False,
                'message': 'Resource %s created' % set_properties['setid']
            }
        )


class SetManagerL2(HDRMSRepository):
    def get(self, request, *args, **kwargs):
        setid = args[0]
        return HDRMSJsonResponse({'action': 'get', 'level': 2, 'setid': setid})

    def post(self, request, *args, **kwargs):
        # * data must have this schema:
        # {
        #     'mimetype': 'image/jpeg',
        #     'filename': 'scan_001.jpg',
        #     'payload': 'base64 data...'
        # },

        setid = args[0]

        if not self.fcrepo.resource_exists(self.fcrepo.addtorest(setid)):
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s does not exist' % setid},
                status=404
            )

        data = json.loads(request.body.decode('utf-8'))
        datastream_fd = io.BytesIO(base64.b64decode(data['payload']))
        datastream_fd.seek(0)
        datastream_fd.name = data['filename']
        resid = 'resid.%s' % self.uniqid()
        resource_path = self.fcrepo.urlmerge(setid, resid)
        self.fcrepo.ingest_file(resource_path, datastream_fd, mimetype=data['mimetype'])


        ttl = self.blazegraph.RDFNamespaces.as_turtle()
        ttl += 'setid:%s hdrmsPred:has-resource resid:%s .\n' % (setid, resid)
        ttl += 'resid:%s hdrmsPred:has-filename "%s" .\n' % (resid, data['filename'])

        self.blazegraph.send_ttl(ttl)

        return HDRMSJsonResponse(
            {
                'setid': setid,
                'resid': resid,
                'error': False,
                'message': 'Resource %s/%s created' % (setid, resid)
            }
        )

    def delete(self, request, *args, **kwargs):
        setid = args[0]

        try:
            self.fcrepo.delete_resource(setid)
        except SWExceptions.HttpStatus404NotFound:
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s does not exist' % setid},
                status=404
            )

        return HDRMSJsonResponse(
            {
                'setid': setid,
                'error': False,
                'message': 'Resource %s deleted' % setid
            }
        )


class SetManagerL3(HDRMSRepository):
    def get(self, request, *args, **kwargs):
        resource_path = self.fcrepo.urlmerge(args[0], args[1])
        try:
            r = self.fcrepo.get(resource_path)
        except SWExceptions.ResourceDoesNotExist:
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s does not exist' % resource_path},
                status=404
            )

        contents = HDRMSHttpResponse(
            r.content,
            content_type=r.headers['Content-Type']
        )
        contents['Content-Disposition'] = r.headers['Content-Disposition']
        contents['Content-Length'] = r.headers['Content-Length']
        return contents

    def post(self, request, *args, **kwargs):
        return HDRMSJsonResponse({'action': 'post', 'level': 3})

    def delete(self, request, *args, **kwargs):
        resource_path = self.fcrepo.urlmerge(args[0], args[1])
        try:
            self.fcrepo.delete_resource(resource_path)
        except SWExceptions.HttpStatus404NotFound:
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s does not exist' % resource_path},
                status=404
            )

        return HDRMSJsonResponse(
            {
                'resource_path': resource_path,
                'error': False,
                'message': 'Resource %s deleted' % resource_path
            }
        )


