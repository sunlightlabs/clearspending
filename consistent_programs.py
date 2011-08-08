from operator import attrgetter
from numpy import mean, std
from django.db.models import Sum
from metrics.models import ProgramConsistency
from cfda.models import ProgramObligation, Program
from utils import short_money
from settings import FISCAL_YEARS
import csv

writer = csv.writer(open('media/docs/consistent_programs_all_years.csv', 'w'))
consistent_allyears = []

for fy in FISCAL_YEARS:
    all_programs = ProgramObligation.objects.filter(fiscal_year=fy, type=1)
    
    under_reporting = ProgramConsistency.objects.filter(fiscal_year=fy,
                                                        type=1,
                                                        under_reported_pct__isnull=False,
                                                        under_reported_pct__lte='25',
                                                        non_reported_dollars__isnull=True)
    over_reporting = ProgramConsistency.objects.filter(fiscal_year=fy,
                                                       type=1,
                                                       over_reported_pct__isnull=False,
                                                       over_reported_pct__lte='25',
                                                       non_reported_dollars__isnull=True)
    null_reporting = ProgramConsistency.objects.filter(fiscal_year=fy,
                                                       type=1,
                                                       over_reported_pct__isnull=True,
                                                       under_reported_pct__isnull=True,
                                                       non_reported_pct__isnull=True)
    programs_with_obligations = ProgramObligation.objects.filter(fiscal_year=fy,
                                                                 type=1,
                                                                 obligation__gt='0',
                                                                 usaspending_obligation__gt='0')

    get_program_id = attrgetter('program_id')
    accurate_set = set(map(get_program_id, null_reporting)) & set(map(get_program_id, programs_with_obligations))
    under_reporting_set = set(map(get_program_id, under_reporting))
    over_reporting_set = set(map(get_program_id, over_reporting))
    consistency_set = accurate_set | under_reporting_set | over_reporting_set
  
    consistent_allyears.append(consistency_set)

    consistent_programs = ProgramObligation.objects.filter(fiscal_year=fy, type=1, program__in=consistency_set)
    consistent_dollars = sum([o.obligation for o in consistent_programs])
    consistent_mean = mean([float(o.obligation) for o in consistent_programs])
    all_grant_dollars = sum([o.obligation for o in all_programs])
    all_grant_mean = mean([float(o.obligation) for o in all_programs])

    print "%d: %d consistent programs, %.2f%% of programs (%d acccurate, %d under, %d over) / %d programs, %.2f%% of grant spending (%s / %s), mean of obligations: %s consistent vs %s all grants" % (
        fy, 
        len(consistent_programs),
        len(consistent_programs) * 100 / len(all_programs),
        len(accurate_set),
        len(under_reporting_set),
        len(over_reporting_set),
        len(all_programs),
        consistent_dollars * 100 / all_grant_dollars,
        short_money(consistent_dollars),
        short_money(all_grant_dollars),
        short_money(consistent_mean),
        short_money(all_grant_mean))


progs = consistent_allyears[0] & consistent_allyears[1] & consistent_allyears[2]
for p in progs:
    program = Program.objects.get(id=p)
    writer.writerow((program.id, program.program_number, program.program_title))
print "%s programs report consistent for all three years" % len(progs)

