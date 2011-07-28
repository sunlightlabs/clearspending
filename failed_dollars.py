from metrics.models import *
from settings import FISCAL_YEARS
from cfda.models import *
from django.db.models import Sum
from helpers.charts import Line
from utils import pretty_money
import csv

def find_possible_mistakes():
    fins = Program.objects.filter(types_of_assistance__financial=True).distinct().order_by('agency')
    csv_out = csv.writer(open('greater_than_50_pct_change.csv', 'w'))

    for f in fins:
        obs = ProgramObligation.objects.filter(type=1, program=f).order_by('fiscal_year')
        if obs:
            current = obs[0]
            for o in obs:
                if current == o: continue
                if not current.obligation: continue
                pct_change = float(o.obligation - current.obligation) / float(current.obligation)
                if pct_change < -.5 or pct_change > .5:
                    csv_out.writerow((o.program.program_number, "%s" % o.program.program_title.encode('ascii', 'ignore'), current.fiscal_year, current.obligation, o.fiscal_year, o.obligation ))
                current = o    


def add_to_agency(agency_totals, agency_name, fy, obligation):
    
    if agency_totals.has_key(agency_name):
        if agency_totals[agency_name].has_key(fy):
            agency_totals[agency_name][fy] += obligation
        else:
            agency_totals[agency_name][fy] = obligation
    else:
        agency_totals[agency_name] = { fy: obligation }

    return agency_totals


TYPE = 1
if len(sys.argv) > 1:
    TYPE = int(sys.argv[1])
if len(sys.argv) > 2:
    metric = sys.argv[2]
else:
    metric = 'all'

print "Failed obligations for %s" % metric
 
fins = Program.objects.filter(types_of_assistance__financial=True).distinct().order_by('agency')
count = 0
types = [None, 'grants', 'loans']
agency_totals = {}
for fy in FISCAL_YEARS:
    writer = csv.writer(open('./media/docs/failed_programs_%s_%s.csv' % (types[TYPE], fy), 'w'), delimiter=',', quotechar='"')
    writer.writerow(('CFDA number', 'CFDA Program Title', 'Failed Metric', 'CFDA Program Obligation', 'USASpending Obligation'))
    total = 0
    for program in fins:
        ob = ProgramObligation.objects.filter(program=program, fiscal_year=fy, type=TYPE)
        if len(ob) > 0: 
            ob = ob[0]
            if metric == 'all' or metric == 'consistency':
                cons = ProgramConsistency.objects.filter(program=program, fiscal_year=fy, type=TYPE)
                if len(cons) > 0:
                    cons_single = cons[0]
                    if cons_single.non_reported_dollars > 0 or cons_single.under_reported_pct > 50 or cons_single.over_reported_pct > 50:
                        total += ob.obligation
                        agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                        writer.writerow((program.program_number, "%s" % program.program_title.encode('ascii', 'ignore'), 'consistency', ob.obligation, ob.usaspending_obligation))
                        continue

        #fail timeliness?
            if metric == 'all' or metric == 'timeliness':
                time = ProgramTimeliness.objects.filter(program=program, fiscal_year=fy)
                if len(time) > 0:
                    time = time[0]
                    if time.total_dollars and (float(time.late_dollars / time.total_dollars)  > .5):
                        total += ob.obligation
                        agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                        writer.writerow((program.program_number, "%s" % program.program_title.encode('ascii', 'ignore'), 'timeliness', ob.obligation))
                        continue

        # fail completeness?
            if metric == 'all' or metric == 'completeness':
                comp = ProgramCompleteness.objects.filter(program=program, fiscal_year=fy)
                if len(comp) > 0:
                    comp = comp[0]
                    if comp.completeness_total_dollars and (float(comp.completeness_failed_dollars / comp.completeness_total_dollars) > .5):
                        total += ob.obligation
                        agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                        writer.writerow((program.program_number, "%s" % program.program_title.encode('ascii', 'ignore'), 'completeness', ob.obligation))
                        continue


    count += 1
    all_obs = ProgramObligation.objects.filter(program__in=fins, fiscal_year=fy, type=TYPE).aggregate(summ=Sum('obligation'))['summ']
    if all_obs:
        print "%s - Total failed obligations: %s out of total obligations: %s (%s%%)" % (fy, pretty_money(total), 
                                                                                     pretty_money(all_obs),
                                                                                     round(total * 100 / all_obs, 2))
    else:
        print "No obligations for %s " % fy

data = []
agency_names = []
for k in agency_totals.keys():
    points = []
    for fy in FISCAL_YEARS:
        if agency_totals[k].has_key(fy):
            points.append((fy, float(agency_totals[k][fy])))
        else:
            points.append((fy, 0))
    data.append(points)
    agency_names.append(k)

#chart = Line(900, 500, data, "/home/kaitlin/envs/faads_scorecard/media/styles/agency_chart.css", label_intervals=1, units=True, currency=True, x_padding=35)
#chart.output("/home/kaitlin/envs/faads_scorecard/media/images/agency_comparison.svg")

#    print "%s - %s" % (k, points)

#find_possible_mistakes()
