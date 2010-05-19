from cfda.models import Program, ProgramObligation, Agency
from metrics.models import *
from django.shortcuts import render_to_response

FISCAL_YEARS = [2009, 2008, 2007]

def agencyDetail(request, agency_id, unit, fiscal_year):
    agency = Agency.objects.get(code=agency_id)
    programs = Program.objects.filter(agency=agency)
    consistency = AgencyConsistency.objects.filter(agency=agency, fiscal_year=fiscal_year)
    if len(consistency) == 2: consistency = consistency[0].combine(consistency[1])
    else: consistency = consistency[0]
    timeliness = AgencyTimeliness.objects.filter(agency=agency, fiscal_year=fiscal_year)
    #completeness

    top_level_numbers = {'underreported': consistency.__dict__['under_reported_' + unit],
                         'overreported': consistency.__dict__['over_reported_' + unit],
                         'nonreported': consistency.__dict__['non_reported_' + unit],
                        }
    if len(timeliness) > 0:
        top_level_numbers['late'] = timeliness[0].__dict__['late' + unit]
    
    #build data structure to easily display in template 
    table_data = []
    for p in programs:
        obligation = ProgramConsistency.objects.filter(fiscal_year=fiscal_year, program=p)
        timeliness = ProgramTimeliness.objects.filter(fiscal_year=fiscal_year, program=p)
        completeness = ProgramCompleteness.objects.filter(fiscal_year=fiscal_year, program=p)
        for ob in obligation:
            row = ["%s (%s)" % (p.program_title, ob.type), ob.__dict__['over_reported_'+unit], ob.__dict__['under_reported_'+unit], ob.__dict__['non_reported_'+unit]]
            if len(timeliness) > 0:
               row.append(timeliness[0].__dict__['late_'+unit])
            if len(completeness) > 0:
               row.append(completeness[0].__dict__['completeness_'+unit])

            table_data.append(row)

    return render_to_response('agency_detail.html', {'top_level_numbers': top_level_numbers, 'table_data': table_data})

def programDetail(request, program_id, unit):
    consistency_block = programDetailConsistency(program_id, unit)
    #TO DO:  get html block for consistency and timeliness
    return render_to_response('program_detail.html', {'consistency':consistency_block}) 
    


def getConsistencyDisplay(obligation, unit):
    if unit == 'percent':
        return '%s' % obligation.weighted_delta
    else:
        return '%s' % obligation.delta

def programDetailConsistency(program_id, unit):
    #returns a chunk of HTML showing the detailed consistency stats for this program
    types = [1, 2] # 1=grants, 2=loans,guarantees,insurance
    program = Program.objects.get(id=program_id)
    program_obligations = ProgramObligation.objects.filter(program=program).order_by('fiscal_year')
    html = []
    if program_obligations:
        for ty in types:
            obligations = program_obligations.filter(type=ty)
            if obligations:
                    html.append('<table class="consistency">')
                    html.append('<tr><td>Metric</td>')
                    for fy in FISCAL_YEARS: html.append('<th>' + str(fy) + '</th>')
                    html.append('</tr><tr><td>Overreported</td>')
                    for fy in FISCAL_YEARS:
                        #use predefined FY so it all looks standard
                        try:
                            p = obligations.filter(fiscal_year=fy)[0]
                        except Exception:
                            html.append('<td>&mdash;</td>')
                            continue
                        html.append('<td>')
                        if p.delta > 0:
                            html.append(getConsistencyDisplay(p, unit))
                        else:
                            html.append('&mdash;')
                        html.append('</td>')

                    html.append('</tr><tr><td>Underreported</td>')
                    for fy in FISCAL_YEARS:
                        try:
                            p = obligations.filter(fiscal_year=fy)[0]
                        except Exception:
                            html.append('<td>&mdash;</td>')
                            continue
                        html.append('<td>')
                        if -1 < p.delta < 0:
                            html.append(getConsistencyDisplay(p, unit))
                        else:
                            html.append('&mdash;')
                    
                    html.append('</tr><tr><td>Not reported</td>')
                    for fy in FISCAL_YEARS:
                        try:
                            p = obligations.filter(fiscal_year=fy)[0]
                        except Exception:
                            html.append('<td>&mdash;</td>')
                            continue
                        html.append('<td>')
                        if p.delta == -1:
                            html.append(getConsistencyDisplay(p, unit))
                        else:
                            html.append('&mdash;')

                    html.append('</tr></table>')
                
    return ''.join(html)    
