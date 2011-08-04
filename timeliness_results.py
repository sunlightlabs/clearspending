from django.db.models import Sum
from numpy import mean, std
from metrics.models import ProgramTimeliness, AgencyTimeliness, USASpendingAggregate
from utils import pretty_money
from settings import FISCAL_YEARS


print "----- Sample Size -----"
for fy in FISCAL_YEARS:
    timeliness_sum = ProgramTimeliness.objects.filter(fiscal_year=fy).aggregate(Sum('total_dollars'))['total_dollars__sum']
    usaspending_sum = USASpendingAggregate.objects.get(fiscal_year=fy).total_federal_funding
    sample_pct = timeliness_sum * 100 / usaspending_sum
    print "%d: %.2f%% (%s / %s)" % (fy, round(sample_pct, 2),
                                    pretty_money(timeliness_sum),
                                    pretty_money(usaspending_sum))

print "----- Average Lag (program) -----"
for fy in FISCAL_YEARS:
    lag_values = [pt.avg_lag_rows for pt in ProgramTimeliness.objects.filter(fiscal_year=fy)]
    print "%d: %d mean (days), %.1f stdev" % (fy, mean(lag_values), std(lag_values))

print "----- Average Lag (agency) -----"
for fy in FISCAL_YEARS:
    lag_values = [at.avg_lag_rows for at in AgencyTimeliness.objects.filter(fiscal_year=fy)]
    print "%d: %d mean (days), %.1f stdev" % (fy, mean(lag_values), std(lag_values))
