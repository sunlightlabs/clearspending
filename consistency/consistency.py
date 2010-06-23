
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
from metrics.models import AgencyConsistency, ProgramConsistency
from django.db.models import Avg, Sum
import csv
import numpy as np
import math
from decimal import Decimal

def main():
    
    assistance_type = 1 #default to grants and direct assistance
    if len(sys.argv) > 1:
        assistance_type = sys.argv[1]
    
    nonreporting = 0
    underreporting = 0
    overreporting = 0
    
    agency_writer = csv.writer(open('csv/agency_stats_%s.csv' % assistance_type, 'w'))
    program_writer = csv.writer(open('csv/program_stats_%s.csv' % assistance_type, 'w'))

    agency_writer.writerow(('Agency Name', 'Fiscal Year', 'CFDA Obligations', 'USASpending Obligations', 'Avg underreporting %', 'underreporting % std', 'Avg overreporting %', 'overreporting % std', 'Non-reporting Programs', 'Non-reporting obligations', '% of obligations NOT reported', 'Total programs'))
    program_writer.writerow(('Program Number', 'Program Name', 'Fiscal Year', 'Agency', 'CFDA Obligations', 'USASpending Obligations', 'Delta', 'Percent under/over reported'))

    fin_programs = Program.objects.filter(types_of_assistance__financial=True ).distinct()
    fin_obligations = ProgramObligation.objects.filter(program__in=fin_programs, type=assistance_type)

    for fy in FISCAL_YEARS:
        nr_programs = fin_obligations.filter(usaspending_obligation=None, fiscal_year=fy, type=assistance_type)
        nonreporting = len(nr_programs)

        under_programs = fin_obligations.filter(fiscal_year=fy, weighted_delta__lt=0).exclude(program__in=nr_programs)
        under_floats = [float(v) for v in under_programs.values_list('weighted_delta', flat=True)]
        underreporting = len(under_programs)

        over_programs = fin_obligations.filter(fiscal_year=fy, weighted_delta__gt=0)
        over_floats = [float(v) for v in over_programs.values_list('weighted_delta', flat=True)]
        overreporting = len(over_programs)

        exact = fin_obligations.filter(fiscal_year=fy, weighted_delta=0)
        
        #calc some basic stats
        under_stats = calc_stats(under_floats)
        over_stats = calc_stats(over_floats)

        #The student loan program is totally screwing up finding less obscene outliers. Here's a hack:
        #calculate new stats with outliers > 5 standard deviations left out
        new_under = under_programs.filter(weighted_delta__gte=str(-5*under_stats['std']))
        new_over = over_programs.filter(weighted_delta__lte=str((5*over_stats['std'])))
        under_stats = calc_stats([float(v) for v in new_under.values_list('weighted_delta', flat=True)])
        over_stats = calc_stats([float(v) for v in new_over.values_list('weighted_delta', flat=True)])

        under_outliers = [ under_programs.filter(weighted_delta__lte=str(-under_stats['std']), weighted_delta__gte=str(-2*under_stats['std'])), 
                        under_programs.filter(weighted_delta__lte=str(-2*under_stats['std']), weighted_delta__gte=str(-3*under_stats['std'])), 
                        under_programs.filter(weighted_delta__lte=str(-3*under_stats['std']))]

        over_outliers = [over_programs.filter(weighted_delta__gte=str(over_stats['std']), 
                        weighted_delta__lte=str(2*over_stats['std'])), 
                        over_programs.filter(weighted_delta__gte=str(2*over_stats['std']), weighted_delta__lte=str(3*over_stats['std'])), 
                        over_programs.filter(weighted_delta__gte=str(3*over_stats['std']))]
        
        print fy
        print "\nNumber of non reporting programs: %s\nNumber of underreporting programs: %s\nNumber of overreporting programs: %s\nExact:%s" % (nonreporting, underreporting, overreporting, len(exact))
        
        print "STD of underreported values:%s\nSTD of overreported values:%s\n" % (under_stats['std'], over_stats['std'])
        print "weighted avg of underreporting programs:%s\nweighted average of overreporting programs:%s\n" % (under_stats['avg'], over_stats['avg'])
        
        #convert to float from weirdo numpy float format
        under_std = float(under_stats['std'])
        under_avg = float(under_stats['avg'])
        over_std = float(over_stats['std'])
        over_avg = float(over_stats['std'])
        
        good = 0
        bad = 0
        ok = 0

        for agency in Agency.objects.all():
            score_agency(agency, fin_obligations, fy, agency_writer, assistance_type)

        for prog in fin_programs:
            obs = ProgramObligation.objects.filter(program=prog, fiscal_year=fy, type=assistance_type)
            for p in obs:
		
                #add program consistency metric
                try:
                    pcm = ProgramConsistency.objects.get(fiscal_year=fy, program=prog, type=assistance_type)
                except ProgramConsistency.DoesNotExist:    
                    pcm = ProgramConsistency(fiscal_year=fy, program=prog, type=assistance_type, agency=prog.agency)

                    if p.delta < 0:
                        if p.weighted_delta == -1:
                            pcm.non_reported_dollars = Decimal(str(math.fabs(p.delta)))
                            pcm.non_reported_pct = -100
                        else:
                            pcm.under_reported_dollars = Decimal(str(math.fabs(p.delta)))
                            pcm.under_reported_pct = Decimal(str(math.fabs(p.weighted_delta * 100)))

                    elif p.delta > 0:
                        pcm.over_reported_dollars = p.delta
                        pcm.over_reported_pct = p.weighted_delta * 100

                    p.save()
                    pcm.save() 
                    program_writer.writerow((p.program.program_number, p.program.program_title.replace(u'\u2013', "").replace(u'\xa0', ''), fy, p.program.agency.name, p.obligation, p.usaspending_obligation, p.delta, p.weighted_delta)) 
                except UnicodeEncodeError, e:
                    print e
                    print "%s - %s" % (p.program.program_number, p.program.program_title)

        #temp hack to show a summary of what programs would be excluded
        #program_writer.writerow(('',fy, "good:", good, "ok: ", ok, "bad: ", bad))

def score_agency(agency, fin_obligations, fiscal_year, writer, type):

    #obligations from financial programs
    obs = fin_obligations.filter(program__agency=agency,fiscal_year=fiscal_year, type=type)
    total_misreported = Decimal('0')
    total = Decimal('0')
    for o in obs:
        if o.delta:
            total_misreported += Decimal(str(math.fabs(o.delta)))
        if o.obligation:
            total += o.obligation

    ac_collection = AgencyConsistency.objects.filter(fiscal_year=fiscal_year, type=type, agency=agency)
    if len(ac_collection) > 0:
        ac = ac_collection[0]
    else:
        ac = AgencyConsistency(agency=agency, fiscal_year=fiscal_year, type=type)

    ac.total = str(total)
    ac.total_misreported = str(total_misreported )
    ac.total_cfda_obligations = obs.aggregate(cfda_sum=Sum('obligation'))['cfda_sum']
    if not ac.total_cfda_obligations:
        ac.total_cfda_obligations = 0
    ac.total_usa_obligations = obs.aggregate(usa_sum=Sum('usaspending_obligation'))['usa_sum']
    if not ac.total_usa_obligations:
        ac.total_usa_obligations = 0
    ac.non_reported_dollars = Decimal(str(math.fabs(obs.filter(weighted_delta=-1).aggregate(nr_sum=Sum('obligation'))['nr_sum'] or 0)))
    if ac.non_reported_dollars:
        ac.non_reported_pct = (ac.non_reported_dollars / ac.total_cfda_obligations) * 100
    else: 
        ac.non_reported_pct = 0
    
    ac.under_reported_dollars = Decimal(str(math.fabs(obs.filter(delta__lt=0, weighted_delta__gt=-1).aggregate(under_sum=Sum('delta'))['under_sum'] or 0)))
    ac.over_reported_dollars =  obs.filter(delta__gt=0).aggregate(over_sum=Sum('delta'))['over_sum'] or 0
    
    if total:
        ac.over_reported_pct = (ac.over_reported_dollars / total) * 100
        ac.under_reported_pct = (ac.under_reported_dollars / total) * 100
        
    else:
        ac.over_reported_pct = 0
        ac.under_reported_pct = 0
    ac.save() 
   
def calc_stats(float_array):
    stats = {}
    stats['avg'] = np.average(float_array)
    stats['std'] = np.std(float_array)
    stats['var'] = np.var(float_array)

    return stats

if __name__ == '__main__':
    main()
    
         

