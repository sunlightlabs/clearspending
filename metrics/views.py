from cfda.models import Program, ProgramObligation, Agency
from metrics.models import *
from django.shortcuts import render_to_response
from django.db.models import Count
from django.db.models.query import QuerySet
from decimal import Decimal
from helpers.format import moneyfmt
import math

FISCAL_YEARS = [2007, 2008, 2009]

def get_css_color(pct, metric):
    if metric == 'con':  #consistency
        if pct > Decimal('50'): return 'bad'
        elif pct > Decimal('25'): return 'warn'
        else: return 'good'
    elif metric == 'time':
        if pct < Decimal('.9'): return 'bad'
        else: return 'good'
    elif metric == 'com':
        if pct < Decimal('.95'): return 'bad'
        else: return 'good'
    
def get_first(set):
    if isinstance(set, QuerySet) and len(set) > 0:
        return set[0]
    else: return None

def get_timeliness(timeliness, unit):
    if timeliness:
        try:
            pct = timeliness.late_dollars / timeliness.total_dollars
        except Exception:
            pct = 0
        if unit == 'pct':
            return (pct*100, get_css_color(pct, 'time'))
        else:
            return (timeliness.late_dollars, get_css_color(pct, 'time'))
    else:
        return (None,)

def get_completeness(completeness, unit):
    if completeness:
        try:
            pct = completeness.completeness_failed_dollars / completeness.completeness_total_dollars
        except Exception:
            pct = 0
        if unit == 'pct':
            return (pct, get_css_color(pct, 'com'))
        else:
            return (completeness.completeness_failed_dollars, get_css_color(pct, 'com'))
        return completeness.__dict__['complete_'+unit]
    else:
        return (None, )

def get_consistency(consistency, unit):
    
    if consistency:
        over = consistency.__dict__['over_reported_'+unit]
        under = consistency.__dict__['under_reported_'+unit]
        non = consistency.__dict__['non_reported_'+unit]
        return (over, get_css_color(consistency.over_reported_pct, 'con'), 
                under, get_css_color(consistency.under_reported_pct, 'con'), 
                non, get_css_color(consistency.non_reported_pct, 'con'))
    else:
        placeholders = []
        for i in range(0, 6):
            placeholders.append(None)
        return placeholders

def index(request, unit='dollars', fiscal_year=2009):
    #get top level agency stats 
    consistency = AgencyConsistency.objects.filter(fiscal_year=fiscal_year).order_by('agency__name')
    timeliness = AgencyTimeliness.objects.filter(fiscal_year=fiscal_year).order_by('agency__name')
    completeness = AgencyCompleteness.objects.filter(fiscal_year=fiscal_year).order_by('agency__name')
    agencies = Agency.objects.all().order_by('name')
    table_data = []
    for a in agencies:

        number_programs = len(Program.objects.filter(agency=a))
        display_name = a.name
      #  if len(display_name) > 35: display_name = "%s..." % display_name[0:35]
        a_data = [a.code,
                  number_programs, 
                  a.name,
                  display_name]

        a_data.extend(get_consistency(get_first(consistency.filter(agency=a)), unit))
        a_data.extend(get_timeliness(get_first(timeliness.filter(agency=a)), unit))
        a_data.extend(get_completeness(get_first(completeness.filter(agency=a)), unit))

        table_data.append(a_data) 

    return render_to_response('scorecard_index.html', {'table_data': table_data, 'fiscal_year': "%s" % fiscal_year, 'unit':unit})

def agencyDetail(request, agency_id, unit='dollars', fiscal_year=2009):
    
    summary_numbers = []
    summary_numbers.extend(get_consistency(get_first(AgencyConsistency.objects.filter(agency=agency_id)), 'dollars'))
    summary_numbers.extend(get_timeliness(get_first(AgencyTimeliness.objects.filter(agency=agency_id)), 'dollars'))
    summary_numbers.extend(get_completeness(get_first(AgencyCompleteness.objects.filter(agency=agency_id)), 'dollars'))
    summary_numbers = filter( lambda x: not isinstance(x, basestring) , summary_numbers) #remove css colors

    programs = Program.objects.filter(agency=agency_id)
    agency = Agency.objects.get(code=agency_id)
    table_data = []
    types = [None, "grants", "loans"]
    for p in programs:
        consistency = ProgramConsistency.objects.filter(fiscal_year=fiscal_year, program=p)
        timeliness = ProgramTimeliness.objects.filter(fiscal_year=fiscal_year, program=p)
        completeness = ProgramCompleteness.objects.filter(fiscal_year=fiscal_year, program=p)
        for ob in consistency:
            display_name = p.program_title
            #if len(display_name) > 35: display_name = "%s..." % display_name[0:32]
            row = [ p.program_number,
                    p.id,
                    "%s (%s)" % (display_name, types[ob.type]),
                    ]
            row.extend(get_consistency(ob, unit))
            row.extend(get_timeliness(get_first(timeliness), unit))
            row.extend(get_completeness(get_first(completeness), unit))

            table_data.append(row)

    return render_to_response('agency_detail.html', {'summary_numbers': summary_numbers, 'table_data': table_data, 'fiscal_year': fiscal_year, 'unit': unit, 'agency_name': agency.name})

def programDetail(request, program_id, unit):
    program = Program.objects.get(id=program_id)
    consistency_block = programDetailConsistency(program_id, unit)  
    #TO DO:  get html block for consistency and timeliness
    return render_to_response('program_detail.html', {'consistency':consistency_block, 'agency_name': program.agency.name, 'program_number': program.program_number, 'title': program.program_title, 'desc': program.objectives, 'unit': unit}) 
    

def getTrends(qset, unit):
    if unit == 'pct': unit = 'weighted_delta'
    else: unit = 'delta'
    over = []
    under = []
    non = []
    trends = []
    for q in qset:
        if q.delta > 0:
            over.append(q.__dict__[unit]); under.append(0); non.append(0)
        elif q.weighted_delta == -1:
            non.append(q.__dict__[unit]); under.append(0); over.append(0)
        else:
            under.append(q.__dict__[unit]); over.append(0); non.append(0)

    for t in (over, under, non):
        first = None
        last = None
        for yr in t:
            if not first and yr: first = yr
            if yr: last = yr
        if last > first: trends.append('redarrow')
        elif last < first: trends.append('greenarrow')
        else: trends.append('arrow')

    return ((over, under, non), trends)


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
                    html.append('<li><table><thead>')
                    html.append('<tr><th class="arrow"></th><th class="reviewed">Consistency</th>')
                    for fy in FISCAL_YEARS: html.append('<th>' + str(fy) + '</th>')
                    html.append('</tr></thead><tbody>')

                            # bad trend
                    values, trends = getTrends(obligations, unit)
                    count = 0
                    for metric in ['Over Reported', 'Under Reported', 'Not Reported']:
                        html.append('<tr><td><span class="%s"></span></td>' % trends[count] )
                        html.append('<td class="reviewed">'+metric+'</td>')
                        for row in values[count]:
                            if row:
                                if unit == 'dollars': row = moneyfmt(row, places=0, curr='$', sep=',', dp='')
                                else: row = str(row) + '%'
                                html.append('<td>%s</td>' % row ) 
                            else:
                                html.append('<td>&mdash;</td>')
                        html.append('</tr>')
                        count += 1

                    html.append('</tbody></table></li>')
                
    return ''.join(html)    
