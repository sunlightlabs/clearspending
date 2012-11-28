from metrics.models import *
from settings import FISCAL_YEARS
from cfda.models import *
from django.db.models import Sum
from helpers.charts import Line
from utils import pretty_money


fins = Program.objects.filter(types_of_assistance__financial=True).distinct().order_by('agency')
TYPE=1

failed_all = {}
failed_tim_con = {}
failed_tim_com = {}
failed_com_con = {}
failed_tim_only = {}
failed_con_only = {}
failed_com_only = {}

totals = {}

for fy in FISCAL_YEARS:

    failed_all[fy] = 0
    failed_tim_con[fy] = 0
    failed_tim_com[fy] = 0
    failed_com_con[fy] = 0
    failed_tim_only[fy] = 0
    failed_con_only[fy] = 0
    failed_com_only[fy] = 0

    for program in fins:
            
        fail_con = False
        fail_com = False
        fail_tim = False


        #fail consistency?
        ob = ProgramObligation.objects.filter(program=program,
                                              fiscal_year=fy,
                                              obligation_type=TYPE)
        if len(ob) > 0: 
            ob = ob[0]
            cons = ProgramConsistency.objects.filter(program=program, fiscal_year=fy, type=TYPE)
            if len(cons) > 0:
                cons_single = cons[0]
                if cons_single.non_reported_dollars > 0 or cons_single.under_reported_pct > 50 or cons_single.over_reported_pct > 50:
                    fail_con = True

        #fail timeliness?
            time = ProgramTimeliness.objects.filter(program=program, fiscal_year=fy)
            if len(time) > 0:
                time = time[0]
                if time.total_dollars and (float(time.late_dollars / time.total_dollars)  > .5):
                    fail_tim = True

        # fail completeness?
            comp = ProgramCompleteness.objects.filter(program=program, fiscal_year=fy)
            if len(comp) > 0:
                comp = comp[0]
                if comp.completeness_total_dollars and (float(comp.completeness_failed_dollars / comp.completeness_total_dollars) > .5):
                    fail_com = True

        if fail_con and fail_tim and fail_com:
            failed_all[fy] += ob.obligation

        elif fail_tim and fail_con:
            failed_tim_con[fy] += ob.obligation

        elif fail_tim and fail_com:
            failed_tim_com[fy] += ob.obligation

        elif fail_com and fail_con:
            failed_com_con[fy] += ob.obligation

        elif fail_tim and not fail_con and not fail_com:
            failed_tim_only[fy] += ob.obligation

        elif fail_con and not fail_tim and not fail_com:
            failed_con_only[fy] += ob.obligation

        elif fail_com and not fail_tim and not fail_con:
            failed_com_only[fy] += ob.obligation

        #reset 
        fail_con = False
        fail_com = False
        fail_tim = False

    totals[fy] = ProgramObligation.objects.filter(program__in=fins,
                                               fiscal_year=fy,
                                               obligation_type=TYPE).aggregate(summ=Sum('obligation'))['summ']
        
        
for fy in FISCAL_YEARS:
    print "FISCAL YEAR %s NUMBERS" % fy       
    print "failed all metrics: %s" % (pretty_money(failed_all[fy]) )
    print "failed timeliness/consistency: %s" % pretty_money(failed_tim_con[fy])
    print "failed timeliness/completeness: %s" % pretty_money(failed_tim_com[fy])
    print "failed consistency/completeness: %s" % pretty_money(failed_com_con[fy])
    print "failed timeliness only: %s" % pretty_money(failed_tim_only[fy])
    print "failed consistency only: %s" % pretty_money(failed_con_only[fy])
    print "failed completeness only: %s" % pretty_money(failed_com_only[fy])

