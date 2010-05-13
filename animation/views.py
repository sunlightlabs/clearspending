import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext


def main(request):

    return render_to_response('animation/map.html', {}, context_instance=RequestContext(request))