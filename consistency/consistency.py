
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
from django.db.models import Avg
import csv
#from matplotlib import pyplot 

FISCAL_YEAR = 2008

def main():
    
    nonreporting = 0
    underreporting = 0
    overreporting = 0
    avg_under = 0
    avg_over = 0

    fin_programs = Program.objects.filter(types_of_assistance__financial=True)
    nr_programs = ProgramObligation.objects.filter(usaspending_obligation=None, program__in=fin_programs, fiscal_year=FISCAL_YEAR)
    nonreporting = len(nr_programs)

    under_programs = ProgramObligation.objects.filter(fiscal_year=FISCAL_YEAR, delta__gt=0, program__in=fin_programs)
    avg_under = under_programs.aggregate(Avg('delta'))    
    under_values = under_programs.values_list('delta', flat=True)
    under_floats = [float(v) for v in under_values]
    underreporting = len(under_programs)

    over_programs = ProgramObligation.objects.filter(fiscal_year=FISCAL_YEAR, delta__lt=0, program__in=fin_programs)
    avg_over = over_programs.aggregate(Avg('delta'))
    over_values = over_programs.values_list('delta', flat=True)
    over_floats = [float(v) for v in over_values]
    overreporting = len(over_programs)

    exact = ProgramObligation.objects.filter(fiscal_year=FISCAL_YEAR, program__in=fin_programs, delta=0)
    
    print "Number of non reporting programs: %s\nNumber of underreporting programs: %s\nNumber of overreporting programs: %s\nTotal: %s\nTotal number of applicable programs: %s\nExact:%s\nAverage underreporting amount:%s\nAverage overreporting amount:%s" % (nonreporting, underreporting, overreporting, nonreporting+underreporting+overreporting, len(fin_programs), len(exact), avg_under, avg_over)

#    pyplot.hist(under_floats)
#    pyplot.show()
    print under_floats
    un = csv.writer(open('csv/under_deltas.txt', 'w'))
    ov = csv.writer(open('csv/over_deltas.txt', 'w'))

    for u in under_floats:
        un.writerow([u]) 
    for o in over_floats:
        ov.writerow([o]) 
#hist(over_floats)


if __name__ == '__main__':
    main()
    
         

