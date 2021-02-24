import io
import json
import uuid
import base64
from SemanticWeb import Fedora4
from SemanticWeb import Blazegraph
from SemanticWeb import Exceptions as SWExceptions

UNIQID_MAXDIGITS = 10

def issue_csrf_key(request, *args, **kwargs):
    return render(request, 'csrf.html', {})


def HDRMSJsonResponse(*args, **kwargs):
    # res = JsonResponse(*args, **kwargs)
    # res['Access-Control-Allow-Origin'] = '*'
    return args[0]


def HDRMSHttpResponse(*args, **kwargs):
    #res = HttpResponse(*args, **kwargs)
    #res['Access-Control-Allow-Origin'] = '*'
    return args[0]


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

        FEDORA_ROOT = "http://localhost:8080/rest/"
        BLAZEGRAPH_ROOT = 'http://localhost:9999/blazegraph'

        self.fcrepo = Fedora4.Repository(FEDORA_ROOT)
        self.blazegraph = Blazegraph.TripleStore(BLAZEGRAPH_ROOT, 'hdrms')

        for prefix, ns in hdrms_rdf_namespaces.items():
            self.blazegraph.RDFNamespaces.add(prefix, ns)



class SetManagerL1(HDRMSRepository):

    def get(self, *args, **kwargs):
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



    def set_l1_post(self, parameters):
        set_properties = {
            **{
                'setid': None,
                'title': 'Unknown-%s' % self.uniqid()
            },
            #**json.loads(request.body.decode('utf-8'))
            **parameters
        }

        if set_properties['setid'] is None:
            set_properties['setid'] = "setid.%s" % self.uniqid()

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
    def get(self, *args, **kwargs):
        setid = args[0]
        query = '''
        select ?res ?filename where { 
          setid:%s <http://hdrms.org/predicates#has-resource> ?res .
          ?res <http://hdrms.org/predicates#has-filename> ?filename .
        }
        ''' % args[0]

        r = self.blazegraph.query(query).json()

        #print(r)

        itemlist =  [
            {'resid': _m['res']['value'], 'filename': _m['filename']['value']}
            for _m in r['results']['bindings']
        ]

        return HDRMSJsonResponse(itemlist, safe=False)



    def post(self, *args, **kwargs):
        # * data must have this schema:
        # {
        #     'mimetype': 'image/jpeg',
        #     'filename': 'scan_001.jpg',
        #     'payload': 'base64 data...'
        # },

        setid = args[0]
        data = args[1]
        if not self.fcrepo.resource_exists(self.fcrepo.addtorest(setid)):
            return HDRMSJsonResponse(
                {'error': True, 'message': 'Resource %s does not exist' % setid},
                status=404
            )

        #data = json.loads(request.body.decode('utf-8'))
        #datastream_fd = io.BytesIO(base64.b64decode(data['payload']))
        datastream_fd = io.BytesIO(data['payload'])
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

    def delete(self, *args, **kwargs):
        setid = args[0]

        query = '''
                    select ?res where {
                        setid:%s ?p ?res .
                    }
                ''' % setid

        q = self.blazegraph.query(query).json()

        resources = [_m['res']['value'].split('#')[1] for _m in q['results']['bindings'] if 'resid' in _m['res']['value']]
        for _m in resources:
            query = '''
                delete where {
                    resid:%s ?p ?o .
                }
            ''' % _m
            self.blazegraph.delete(query)

        self.blazegraph.delete('delete where { setid:%s ?p ?o .}' % setid)

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
        #contents['Content-Disposition'] = r.headers['Content-Disposition']
        contents['Content-Length'] = r.headers['Content-Length']
        return contents

    def post(self, request, *args, **kwargs):
        return HDRMSJsonResponse({'action': 'post', 'level': 3})

    def delete(self, request, *args, **kwargs):
        resource_path = self.fcrepo.urlmerge(args[0], args[1])
        try:
            self.fcrepo.delete_resource(resource_path)
            # r = self.blazegraph.delete(
            #     '''delete where { cpdv-keyword:%s ?p ?o .  }''' % kw_pid
            # )
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


