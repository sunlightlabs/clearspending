from cfda.models import ProgramObligation, Agency
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render_to_response


def scorecard(request):
    
    agencies = Agency.objects.all().order_by('name')
    consistency = Consistency.objects.all().order_by('agency')
    #add timeliness and completeness

    return render_to_response('scorecard.html', {'agencies': agencies})

def get_agency_detail(request, agency_id, fiscal_year):
    
    #bring back a list of programObligation objects for this agency and fiscal year
    programs = ProgramObligation.objects.filter(program__types_of_assistance__financial=True, program__agency=agency_id, fiscal_year=fiscal_year )
    
    return render_to_response( 'agency_detail.html',{'programs': programs})

def get_program_detail(request, program_id):

    program = Program.objects.get(id=program_id)
    obligations = ProgramObligation.objects.filter(program=program)
    metric = ProgramMetric.objects.get(program=program)
    corrections = ProgramCorrection.objects.filter(program=program)

    return render_to_response( 'program_detail.html', {'program': program, 'obligations': obligations, 'metric': metric, 'corrections':corrections})


