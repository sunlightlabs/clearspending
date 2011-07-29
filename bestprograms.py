from metrics.models import ProgramTimeliness, ProgramConsistency, ProgramCompleteness
from cfda.models import Program
from operator import attrgetter
from settings import FISCAL_YEARS
from utils import pretty_money

def main():
    timeliness = ProgramTimeliness.objects.filter(fiscal_year=max(FISCAL_YEARS),
                                                  late_dollars=0).exclude(total_dollars=0)
    under_reporting = ProgramConsistency.objects.filter(fiscal_year=max(FISCAL_YEARS),
                                                        type=1,
                                                        under_reported_pct__isnull=False,
                                                        under_reported_pct__lte='0.25')
    over_reporting = ProgramConsistency.objects.filter(fiscal_year=max(FISCAL_YEARS),
                                                       type=1,
                                                       over_reported_pct__isnull=False,
                                                       over_reported_pct__lte='0.25')
    completeness = ProgramCompleteness.objects.filter(fiscal_year=max(FISCAL_YEARS), 
                                                      completeness_failed_dollars=0)


    get_program_id = attrgetter('program_id')
    timeliness_set = set(map(get_program_id, timeliness))
    consistency_set = set(map(get_program_id, under_reporting) +
                          map(get_program_id, over_reporting))
    completeness_set = set(map(get_program_id, completeness))
    best_program_ids = timeliness_set & consistency_set & completeness_set

    print "%d programs in common" % len(best_program_ids)
    for program_id in best_program_ids:
        program = Program.objects.get(pk=program_id)
        prog_timeliness = ProgramTimeliness.objects.get(program=program_id, 
                                                        fiscal_year=max(FISCAL_YEARS))
        prog_consistency = ProgramConsistency.objects.get(program=program_id,
                                                          fiscal_year=max(FISCAL_YEARS),
                                                          type=1)
        prog_completeness = ProgramCompleteness.objects.get(program=program_id,
                                                            fiscal_year=max(FISCAL_YEARS))
        print "{0:>17} . . . {1} ".format(pretty_money(prog_completeness.completeness_total_dollars),
                                          str(program)[:60])


if __name__ == "__main__":
    main()

