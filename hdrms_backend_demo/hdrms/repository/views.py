from django.views.decorators.http import require_http_methods

from . import api


@require_http_methods(["GET"])
def issue_csrf_key(request, *args, **kwargs):
    return api.issue_csrf_key(request, *args, **kwargs)


@require_http_methods(["GET", "POST"])
def hdrms_sets_level_one(request, *args, **kwargs):
    mgr = api.SetManagerL1()
    return {
        "GET": mgr.get,
        "POST": mgr.post,
    }[request.method](request, *args, **kwargs)


@require_http_methods(["GET", "POST", "DELETE"])
def hdrms_sets_level_two(request, *args, **kwargs):
    mgr = api.SetManagerL2()
    return {
        "GET": mgr.get,
        "POST": mgr.post,
        "DELETE": mgr.delete
    }[request.method](request, *args, **kwargs)


@require_http_methods(["GET", "POST", "DELETE"])
def hdrms_sets_level_three(request, *args, **kwargs):
    mgr = api.SetManagerL3()
    return {
        "GET": mgr.get,
        "POST": mgr.post,
        "DELETE": mgr.delete
    }[request.method](request, *args, **kwargs)