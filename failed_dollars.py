from metrics.models import *
from cfda.models import *
from django.db.models import Sum
from helpers.charts import Line
import csv

def find_possible_mistakes():
    fins = Program.objects.filter(types_of_assistance__financial=True).distinct().order_by('agency')
    csv_out = csv.writer(open('greater_than_50_pct_change.csv', 'w'))

    for f in fins:
        obs = ProgramObligation.objects.filter(type=1, program=f).order_by('fiscal_year').exclude(fiscal_year=2010).exclude(fiscal_year=2007)
        if obs:
            current = obs[0]
            for o in obs:
                if current == o: continue
                if not current.obligation: continue
                pct_change = float(o.obligation - current.obligation) / float(current.obligation)
                if pct_change < -.5 or pct_change > .5:
                    csv_out.writerow((o.program.program_number, o.program.program_title.encode('ascii', 'ignore'), current.fiscal_year, current.obligation, o.fiscal_year, o.obligation ))
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
    TYPE = sys.argv[1]
over_std = [85.610, 23.2192, 9565.752]
under_std = [0.40094, 0.4099, .4046]

under_avg = [0.65786, .56732, .5955]
over_avg = [11.3492, 3.65377, 522.86656]

fins = Program.objects.filter(types_of_assistance__financial=True).distinct().order_by('agency')
count = 0
agency_totals = {}
for fy in [2007, 2008, 2009]:
    total = 0
    for program in fins:
        ob = ProgramObligation.objects.filter(program=program, fiscal_year=fy, type=TYPE)
        if len(ob) > 0: 
            ob = ob[0]
            cons = ProgramConsistency.objects.filter(program=program, fiscal_year=fy)
            if len(cons) > 0:
                cons_single = cons[0]
                if cons_single.non_reported_dollars > 0 or cons_single.under_reported_pct > .50 or cons_single.over_reported_pct > 1.50:
                    total += ob.obligation
                    agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                    continue

        #fail timeliness?
            time = ProgramTimeliness.objects.filter(program=program, fiscal_year=fy)
            if len(time) > 0:
                time = time[0]
                if time.total_dollars and (time.late_dollars / time.total_dollars  > .9):
                    total += ob.obligation
                    agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                    continue

            comp = ProgramCompleteness.objects.filter(program=program, fiscal_year=fy)
            if len(comp) > 0:
                comp = comp[0]
                if comp.completeness_total_dollars and (comp.completeness_failed_dollars / comp.completeness_total_dollars > .95):
                    total += ob.obligation
                    agency_totals = add_to_agency(agency_totals, program.agency.name, fy, ob.obligation)
                    continue
        # fail completeness?


    count += 1
    all = ProgramObligation.objects.filter(program__in=fins, fiscal_year=fy).aggregate(summ=Sum('obligation'))['summ']
    print "%s - Total failed obligations: %s out of total obligations: %s" % (fy, total, all)

data = []
agency_names = []
for k in agency_totals.keys():
    points = []
    for fy in [2007, 2008, 2009]:
        if agency_totals[k].has_key(fy):
            points.append((fy, float(agency_totals[k][fy])))
        else:
            points.append((fy, 0))
    data.append(points)
    agency_names.append(k)

chart = Line(900, 500, data, "/home/kaitlin/envs/faads_scorecard/media/styles/agency_chart.css", label_intervals=1, units=True, currency=True, x_padding=35)
chart.output("/home/kaitlin/envs/faads_scorecard/media/images/agency_comparison.svg")

#    print "%s - %s" % (k, points)

find_possible_mistakes()
