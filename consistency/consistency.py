
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
from metrics.models import Consistency
from django.db.models import Avg, Sum
import csv
import numpy as np
import math


def main():
    
    nonreporting = 0
    underreporting = 0
    overreporting = 0

    fin_programs = Program.objects.filter(types_of_assistance__financial=True)
    fin_obligations = ProgramObligation.objects.filter(program__in=fin_programs)

    for fy in FISCAL_YEARS:
        nr_programs = fin_obligations.filter(usaspending_obligation=None, fiscal_year=fy)
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
        
        #show_outliers(under_outliers, over_outliers)  #this is to catch cfda obligaton errors
        print fy
        print "\nNumber of non reporting programs: %s\nNumber of underreporting programs: %s\nNumber of overreporting programs: %s\nExact:%s" % (nonreporting, underreporting, overreporting, len(exact))
        
        print "STD of underreported values:%s\nSTD of overreported values:%s\n" % (under_stats['std'], over_stats['std'])
        print "weighted avg of underreporting programs:%s\nweighted average of overreporting programs:%s\n" % (under_stats['avg'], over_stats['avg'])
        
    agency_writer = csv.writer(open('csv/agency_stats.txt', 'w'))

    agency_writer.writerow(('Agency Name', 'Fiscal Year', 'CFDA Obligations', 'USASpending Obligations', 'Avg underreporting %', 'underreporting % std', 'Avg overreporting %', 'overreporting % std', 'Non-reporting Programs', 'Non-reporting obligations', '% of obligations NOT reported', 'Total programs'))
    for agency in Agency.objects.all():
        for year in FISCAL_YEARS:
            score_agency(agency, fin_obligations, year, agency_writer)
        

def score_agency(agency, fin_obligations, fiscal_year, writer):
    
    obs = fin_obligations.filter(program__agency=agency,fiscal_year=fiscal_year)
    under = obs.filter(delta__lt=0)
    over = obs.filter(delta__gt=0)
    exact = obs.filter(delta=0)
    avg_under_pct = under.aggregate(Avg('weighted_delta'))['weighted_delta__avg'] or 0 
    avg_over_pct = over.aggregate(Avg('weighted_delta'))['weighted_delta__avg'] or 0
    unreported = obs.filter(usaspending_obligation=None)

    summary = obs.aggregate(Sum('obligation'), Sum('usaspending_obligation'))
    under_summary = under.aggregate(Sum('delta'))
    over_summary = over.aggregate(Sum('delta'))
    over_sd = np.std([float(v) for v in over.values_list('weighted_delta', flat=True)])
    under_sd = np.std([float(v) for v in under.values_list('weighted_delta', flat=True)])
    over_var = np.var([float(v) for v in over.values_list('weighted_delta', flat=True)])
    under_var = np.var([float(v) for v in under.values_list('weighted_delta', flat=True)])
    nr_sum = unreported.aggregate(Sum('obligation'))['obligation__sum'] or 0
    try:
        nr_pct = nr_sum / summary['obligation__sum']
    except Exception, e:
        nr_pct = 0

    if obs:
        ac_collection = Consistency.objects.filter(agency=agency, fiscal_year=fiscal_year)
        if len(ac_collection) == 0:
            ac = Consistency(fiscal_year=fiscal_year, agency=agency)
        else:
            ac = ac_collection[0]

        ac.total_cfda_obligations = summary['obligation__sum'] or 0
        ac.total_usa_obligations = summary['usaspending_obligation__sum'] or 0
        ac.total_programs = str(len(obs))
        ac.non_reported_obligations = str(nr_sum)
        ac.avg_under_pct = str(avg_under_pct)
        ac.avg_over_pct = str(avg_over_pct)
        ac.std_under_pct = str(under_sd)
        ac.std_over_pct = str(over_sd)
        ac.var_under_pct = str(under_var)
        ac.var_over_pct = str(over_var)
        
        ac.save() #save to be able to add to many to many
        for nr_ob in unreported:
            if nr_ob.program not in ac.non_reporting_programs.all():
                ac.non_reporting_programs.add(nr_ob.program)
        
        ac.save()

        writer.writerow((agency.name, fiscal_year, summary['obligation__sum'], summary['usaspending_obligation__sum'], avg_under_pct, under_sd, avg_over_pct, over_sd, len(unreported), nr_sum, nr_pct, len(obs)))

def calc_stats(float_array):
    stats = {}
    stats['avg'] = np.average(float_array)
    stats['std'] = np.std(float_array)
    stats['var'] = np.var(float_array)

    return stats

def show_outliers(under_outliers, over_outliers):

    print "\nUnderreporting outliers:\noutside of 3 standard deviations:"
    for o in under_outliers[2]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)

    #print "\noutside of 2 standard deviations"
    #for o in under_outliers[1]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)

    #print "\noutside of 1 standard deviation"
    #for o in under_outliers[0]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)

    print "\nOverreporting outliers:\noutside of 3 standard deviations"
    for o in over_outliers[2]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)

    print "\noutside of 2 standard deviations"
    for o in over_outliers[1]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)

    #print "\noutside of 1 standard deviation"
    #for o in over_outliers[0]: print "%s\t%s\t%s\t%s\t%s" % (o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)



if __name__ == '__main__':
    main()
    
         

