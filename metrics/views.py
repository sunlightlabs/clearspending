from cfda.models import Program, ProgramObligation, Agency
from metrics.models import *
from django.shortcuts import render_to_response
from django.db.models import Count, Sum
from django.db.models.query import QuerySet
from decimal import Decimal
from django.core.mail import send_mail
from helpers.format import moneyfmt
import math
from urllib import unquote
from haystack.query import SearchQuerySet
from haystack.models import SearchResult

FISCAL_YEARS = [2007, 2008, 2009]

def contact(request):
    #submission of contact form
    name = request.POST.get('name', '')
    email = request.POST.get('email', '')
    msg = request.POST.get('message', '')
    send_mail('Clearspending Feedback from '+name, msg, email, ['klee@sunlightfoundation.com'], fail_silently=True)
    return render_to_response('contact_thankyou.html')

def search_results(request, search_string, unit='pct', fiscal_year=2009):

    search = unquote(search_string)
    programs = SearchQuerySet().filter(content=search_string)
    result_count = programs.count()
    table_data = generic_program_table(programs, fiscal_year, unit)
    
    return render_to_response('generic_program_list.html', { 'table_data': table_data, 'fiscal_year': fiscal_year, 'unit': unit, 'search_string': search, 'result_count': result_count })
    
 

def get_css_color(pct, metric):
    if metric == 'con':  #consistency
        pct = Decimal(str(math.fabs(pct)))
        if pct > Decimal('50'): return 'bad'
        elif pct > Decimal('25'): return 'warn'
        else: return 'good'
    elif metric == 'time':
        if pct > Decimal('.1'): return 'bad'
        else: return 'good'
    elif metric == 'com':
        if pct > Decimal('5'): return 'bad'
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
        return (None,'')

def get_completeness(unit, **completeness):
    if completeness:
        try:
            pct = (completeness['failed_total']/ completeness['total']) * 100
        except Exception:
            pct = 0
        if unit == 'pct':
            return (pct, get_css_color(pct, 'com'))
        else:
            return (completeness['failed_total'], get_css_color(pct, 'com'))
    else:
        return (None, '')

def get_consistency(consistency, unit):
    
    if consistency:
        over = math.fabs(consistency.__dict__['over_reported_'+unit] or 0)
        under = math.fabs(consistency.__dict__['under_reported_'+unit] or 0)
        non = math.fabs(consistency.__dict__['non_reported_'+unit] or 0)
        return (over, get_css_color(consistency.over_reported_pct or 0, 'con'), 
                under, get_css_color(consistency.under_reported_pct or 0, 'con'), 
                non, get_css_color(consistency.non_reported_pct or 0, 'con'))
    else:
        placeholders = []
        for i in range(0, 6):
            placeholders.append(None)
        return placeholders

def generic_program_table(programs, fiscal_year, unit):
    #builds a scorecard table for a generic list of programs
    table_data = []
    types = [None, "grants", "loans"]
    for p in programs:
        display_name = p.program_title
        program_number = p.program_number
         
        if p.__class__ == SearchResult:
            p = p.pk
            p_id = p
        else: 
            p_id = p.id
        consistency = ProgramConsistency.objects.filter(fiscal_year=fiscal_year, program=p)
        timeliness = ProgramTimeliness.objects.filter(fiscal_year=fiscal_year, program=p)
        completeness_totals = ProgramCompleteness.objects.filter(program=p, fiscal_year=fiscal_year).aggregate(failed_total=Sum('completeness_failed_dollars'), total=Sum('completeness_total_dollars'))
        if len(consistency) > 0:
            ob_type = "(%s)" % types[get_first(consistency).type]
        else: ob_type = ""

        #if len(display_name) > 35: display_name = "%s..." % display_name[0:32]
        row = [ program_number,
                p_id,
                "%s %s" % (display_name, ob_type),
                ]
        row.extend(get_consistency(get_first(consistency), unit))
        row.extend(get_timeliness(get_first(timeliness), unit))
        row.extend(get_completeness(unit, **completeness_totals))
        table_data.append(row)

        if len(consistency) > 1:
            for ob in consistency[1:]:
                row = [ program_number,
                        p_id,
                        "%s (%s)" % (display_name, types[ob.type]),
                        ]
                row.extend(get_consistency(ob, unit))
                row.extend(get_timeliness(get_first(timeliness), unit))
                row.extend(get_completeness(unit, **completeness_totals))
                table_data.append(row)

    return table_data

def index(request, unit='dollars', fiscal_year=2009):
    #get top level agency stats 
    consistency = AgencyConsistency.objects.filter(fiscal_year=fiscal_year).order_by('agency__name')
    timeliness = AgencyTimeliness.objects.filter(fiscal_year=fiscal_year).order_by('agency__name')
    agencies = Agency.objects.all().order_by('name')
    table_data = []
    for a in agencies:

        number_programs = Program.objects.filter(agency=a).count()
        display_name = a.name
      #  if len(display_name) > 35: display_name = "%s..." % display_name[0:35]
        a_data = [a.code,
                  number_programs, 
                  a.name,
                  display_name]

        a_data.extend(get_consistency(get_first(consistency.filter(agency=a)), unit))
        a_data.extend(get_timeliness(get_first(timeliness.filter(agency=a)), unit))
        completeness_totals = ProgramCompleteness.objects.filter(program__agency=a, fiscal_year=fiscal_year).aggregate(failed_total=Sum('completeness_failed_dollars'), total=Sum('completeness_total_dollars'))
        a_data.extend(get_completeness(unit, **completeness_totals))

        table_data.append(a_data) 

    return render_to_response('scorecard_index.html', {'table_data': table_data, 'fiscal_year': "%s" % fiscal_year, 'unit':unit})

def agencyDetail(request, agency_id, unit='dollars', fiscal_year=2009):
    
    summary_numbers = []
    summary_numbers.append(AgencyConsistency.objects.filter(agency=agency_id, fiscal_year=fiscal_year).aggregate(total=Sum('total_cfda_obligations'))['total'])
    summary_numbers.extend(get_consistency(get_first(AgencyConsistency.objects.filter(agency=agency_id, fiscal_year=fiscal_year)), 'dollars'))
    summary_numbers.extend(get_timeliness(get_first(AgencyTimeliness.objects.filter(agency=agency_id, fiscal_year=fiscal_year)), 'dollars'))
    completeness_totals = ProgramCompleteness.objects.filter(program__agency=agency_id, fiscal_year=fiscal_year).aggregate(failed_total=Sum('completeness_failed_dollars'), total=Sum('completeness_total_dollars'))
    summary_numbers.extend(get_completeness('dollars', **completeness_totals)) 
    summary_numbers = filter( lambda x: not isinstance(x, basestring) , summary_numbers) #remove css colors

    programs = Program.objects.filter(agency=agency_id)
    agency = Agency.objects.get(code=agency_id)
    table_data = generic_program_table(programs, fiscal_year, unit)

    return render_to_response('agency_detail.html', {'summary_numbers': summary_numbers, 'table_data': table_data, 'fiscal_year': fiscal_year, 'unit': unit, 'agency_name': agency.name, 'agency': agency_id, 'description': agency.description})


def programDetail(request, program_id, unit):
    program = Program.objects.get(id=program_id)
    
    program_total_number = ProgramObligation.objects.filter(program=program).aggregate(total=Sum('obligation'))['total']
    program_total = moneyfmt(Decimal(str(program_total_number)), places=0, curr='$', sep=',', dp='')

    consistency_block = programDetailConsistency(program, unit) 
    field_names = ['late_'+unit, 'avg_lag_rows']
    proper_names = ['Late Records (over 45 days after obligation)', 'Average Reporting Lag (days since obligation)']
    coll = ProgramTimeliness.objects.filter(program=program_id).order_by('fiscal_year')
    timeliness_block = programDetailGeneral(program_id, unit, field_names, proper_names, coll, 'Timeliness')

    if len(program.objectives) < 1300:
        description = program.objectives
    else: description = program.objectives[:1300] + '... <a href="http://cfda.gov">read more at CFDA.gov</a>.'

    #update these lists with all the fields we want to show
    com_field_names = ['recipient_type_is_not_empty', 'federal_agency_code_is_not_empty', 'cfda_program_num_is_descriptive', 'federal_funding_amount_is_not_empty',
                        'principal_place_code_not_empty', 'recipient_name_not_empty', 'recipient_state_code_not_empty', 'recipient_county_code_not_empty_or_too_long',
                        'recipient_county_name_not_empty', 'recipient_city_code_not_empty', 'recipient_city_name_not_empty', 'principal_place_state_not_empty', 'record_type_is_not_empty', 
                        'action_type_is_not_empty', 'recipient_cong_district_is_not_empty', 'obligation_action_date_is_properly_formatted', 
                        'assistance_type_is_not_empty', 'federal_award_id_is_not_empty']
    
    com_proper_names = ['Recipient type', 'Federal Agency', 'CFDA Program Number', 'Funding Amount',
                        'Principal Place of Grant Code',  'Recipient Name', 'Recipient State', 'Recipient County Code', 
                        'Recipient County Name', 'Recipient City Code', 'Recipient City Name', 'Principal State of Grant', 'Record Type', 
                        'Action Type', 'Recipient Congressional District', 'Obligation Action Date Formatted Correctly', 
                        'Assistance Type', 'Federal Award ID' ]
    com_coll = ProgramCompletenessDetail.objects.filter(program=program_id).order_by('fiscal_year')
    completeness_block = programDetailGeneral(program_id, unit, com_field_names, com_proper_names, com_coll, 'Completeness')
    
    return render_to_response('program_detail.html', {'consistency':consistency_block, 'timeliness': timeliness_block, 'completeness': completeness_block, 'agency_name': program.agency.name, 'program_number': program.program_number, 'title': program.program_title, 'desc': description, 'unit': unit, 'program_total': program_total}) 
    
def getRowClass(count):
    if count % 2 == 0 : row = "even"
    else: row = 'odd'
    return row

def getTrends(qset, field_name):
    first = None
    last = None
    values = []
    for q in qset: # should be ordered by fiscal year asc
        if not first and q: first = q.__dict__[field_name]
        elif q: last = q.__dict__[field_name]
        values.append(q.__dict__[field_name])

    if last > first: return (values, 'redarrow')
    elif first > last: return (values, 'greenarrow')
    else: return (values, 'arrow')
        

def getConsistencyTrends(qset, unit):
    if unit == 'pct': unit = 'weighted_delta'
    else: unit = 'delta'
    over = []
    under = []
    non = []
    trends = []
    count = 0
    for q in qset:
        while q.fiscal_year != FISCAL_YEARS[count]:
            over.append(0); under.append(0); non.append(0)
            count += 1

        if q.delta > 0:
            over.append(q.__dict__[unit]); under.append(0); non.append(0)
        elif q.weighted_delta == -1:
            non.append(math.fabs(q.__dict__[unit])); under.append(0); over.append(0)
        else:
            under.append(math.fabs(q.__dict__[unit])); over.append(0); non.append(0)

        count += 1
    #if q.fiscal_year < 2009:
    while count < 3:
        over.append(0); under.append(0); non.append(0)
        count += 1

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

def programDetailConsistency(program, unit):
    #returns a chunk of HTML showing the detailed consistency stats for this program
    types = [1, 2] # 1=grants, 2=loans,guarantees,insurance
    type_names = {1: 'Grants', 2: 'Loans'}
    program_obligations = ProgramObligation.objects.filter(program=program, fiscal_year__lte=max(FISCAL_YEARS)).order_by('fiscal_year')
    html = []
    if program_obligations.count() > 0:
        for ty in types:
            obligations = program_obligations.filter(type=ty)
            if obligations:
                    html.append('<li><table><thead>')
                    html.append('<tr><th class="arrow"></th><th class="reviewed">Consistency (%s)</th>' % type_names[ty])
                    for fy in FISCAL_YEARS: html.append('<th>' + str(fy) + '</th>')
                    html.append('</tr></thead><tbody>')
                    values, trends = getConsistencyTrends(obligations, unit)
                    count = 0
                    for metric in ['Over Reported', 'Under Reported', 'Not Reported']:
                        html.append('<tr class="%s"><td><span class="%s"></span></td>' % (getRowClass(count), trends[count] ))
                        html.append('<td class="reviewed">'+metric+'</td>')
                        for row in values[count]:
                            if row:
                                if unit == 'dollars': row = moneyfmt(Decimal(str(row)), places=0, curr='$', sep=',', dp='')
                                else: row = "%d" % (row * 100) + '%'
                                html.append('<td>%s</td>' % row ) 
                            else:
                                html.append('<td>&mdash;</td>')
                        html.append('</tr>')
                        count += 1

                    html.append('</tbody></table></li>')
                
    return ''.join(html)    

def programDetailGeneral(program_id, unit, field_names, proper_names, coll, metric):

    html = []
    com_totals = {}
    if metric == 'Completeness':
        totals = ProgramCompleteness.objects.filter(program=program_id)
        for t in totals:
            com_totals[t.fiscal_year] = t.completeness_total_dollars

    if coll:
        html.append('<li><table><thead><tr><th class="arrow"></th><th class="reviewed">'+metric+'</th>')
        for fy in FISCAL_YEARS: html.append('<th>' + str(fy) + '</th>')
        html.append('</tr></thead><tbody>')
        count = 0
        for f in field_names:
            temp_html = []
            first = None
            last = None
            temp_html.append('<td class="reviewed">%s</td>' % proper_names[count])
            year_count = 0
            for y in FISCAL_YEARS:
                item = get_first(coll.filter(fiscal_year=y))
                if item: 
                    if not first and item.__dict__[f]:
                        first = item.__dict__[f]
                    elif item.__dict__[f]:
                        last = item.__dict__[f]
                    
                    if item.__dict__[f]:
                        if unit == 'pct' and f != 'avg_lag_rows':
                            if metric == 'Completeness':
                                val = '%d' % (((item.__dict__[f] / com_totals[y]) or 0) * 100)
                                val += '%'
                            else:
                                val = str((item.__dict__[f] or 0) * 100) + '%'
                        elif f != 'avg_lag_rows':
                            val = '%s' % moneyfmt(Decimal(str(item.__dict__[f] or 0)), places=0, curr='$', sep=',', dp='')
                        else:
                            val = item.__dict__[f]
                        temp_html.append('<td>%s</td>' % val)
                    else:
                        temp_html.append('<td>&mdash;</td>')
                else:
                    temp_html.append('<td>&mdash;</td>')

                year_count += 1
            
            trend = 'arrow'
            if first and last:
                if last > first: trend = 'redarrow'
                elif first > last: trend = 'greenarrow'
            html.append('<tr class="%s"><td><span class="%s"></span></td>%s</tr>' % (getRowClass(count), trend, ''.join(temp_html) ))
            count += 1 

        html.append('</tbody></table></li>')
    
    return ''.join(html)





