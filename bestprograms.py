from metrics.models import ProgramTimeliness, ProgramConsistency, ProgramCompleteness
from cfda.models import Program, ProgramObligation
from operator import attrgetter
from decimal import Decimal
from settings import FISCAL_YEARS
from utils import pretty_money


FISCAL_YEAR = max(FISCAL_YEARS)


def compare_consistencies(a, b):
    """Comparison function for sorting consistency models"""
    a_pct = max(a.under_reported_pct, a.over_reported_pct)
    b_pct = max(b.under_reported_pct, b.over_reported_pct)
    if a_pct == b_pct:
        a_val = max(a.under_reported_dollars, a.over_reported_dollars)
        b_val = max(b.under_reported_dollars, b.over_reported_dollars)
        return cmp(a_val, b_val)
    else:
        return cmp(a_pct, b_pct)


def best_programs(threshold):
    """To make the list a program must come in under the threshold
    for both the completeness metric and the consistency metric.
    Additionally any program that is over the threshold for the
    timeliness metric will be removed from the list
    """
    timeliness = ProgramTimeliness.objects.filter(fiscal_year=FISCAL_YEAR,
                                                  late_pct__gt=threshold).exclude(total_dollars='0.0')
    under_reporting = ProgramConsistency.objects.filter(fiscal_year=FISCAL_YEAR,
                                                        type=1,
                                                        under_reported_pct__isnull=False,
                                                        under_reported_pct__lte=threshold,
                                                        non_reported_dollars__isnull=True)
    over_reporting = ProgramConsistency.objects.filter(fiscal_year=FISCAL_YEAR,
                                                       type=1,
                                                       over_reported_pct__isnull=False,
                                                       over_reported_pct__lte=threshold,
                                                       non_reported_dollars__isnull=True)
    completeness = [pc for pc in ProgramCompleteness.objects.filter(fiscal_year=FISCAL_YEAR)
                    if pc.failed_pct < Decimal(threshold)]


    get_program_id = attrgetter('program_id')
    timeliness_set = set(map(get_program_id, timeliness))
    consistency_set = set(map(get_program_id, under_reporting) +
                          map(get_program_id, over_reporting))
    completeness_set = set(map(get_program_id, completeness))
    best_program_ids = (consistency_set & completeness_set) - timeliness_set
    return best_program_ids


def print_program_list(best_program_ids):
    best_program_consistencies = list(ProgramConsistency.objects.filter(fiscal_year=FISCAL_YEAR,
                                                                        type=1,
                                                                        program__in=best_program_ids))
    best_program_consistencies.sort(compare_consistencies)

    fmtstr = "{program:<8} {consistency:>14} {completeness:>12} {timeliness:>11} {cfda:>21}"
    print fmtstr.format(
        program='PROGRAM',
        consistency='INCONSISTENT',
        completeness='INCOMPLETE',
        timeliness='LATE',
        cfda='CFDA OBLIGATION'
    )
    for prog_consistency in best_program_consistencies:
        program = Program.objects.get(pk=prog_consistency.program_id)
        program_obligation = ProgramObligation.objects.get(fiscal_year=FISCAL_YEAR,
                                                           type=1,
                                                           program=prog_consistency.program_id)

        prog_completeness = ProgramCompleteness.objects.get(fiscal_year=FISCAL_YEAR,
                                                            program=prog_consistency.program_id)
        try:
            prog_timeliness = ProgramTimeliness.objects.get(fiscal_year=FISCAL_YEAR,
                                                            program=prog_consistency.program_id)
        except:
            prog_timeliness = None


        if prog_consistency.over_reported_pct not in (None, ''):
            over_or_under = "-" + str(prog_consistency.over_reported_pct)
        elif prog_consistency.under_reported_pct not in (None, ''):
            over_or_under = "-" + str(prog_consistency.under_reported_pct)
        else:
            over_or_under = None

        values = {
            'program': str(program.program_number),
            'consistency': str(over_or_under) + '%',
            'completeness': str(round(prog_completeness.failed_pct)) + '%',
            'timeliness': str(round(prog_timeliness.late_pct)) + '%' if prog_timeliness and prog_timeliness.late_pct is not None else '---',
            'cfda': pretty_money(program_obligation.obligation)
        }
        print fmtstr.format(**values)
                                     

def main():
    thresholds = ['1', '25', '50', '75']
    lists = dict.fromkeys(thresholds)
    cumulative = set()

    for threshold in thresholds:
        programs_for_threshold = best_programs(threshold)
        lists[threshold] = programs_for_threshold - cumulative
        cumulative = cumulative.union(programs_for_threshold)

    for threshold in thresholds:
        programs_for_threshold = lists[threshold]
        print "%s%d programs in %d at %s%% threshold" % (
            "" if threshold == thresholds[0] else "plus ",
            len(programs_for_threshold), 
            FISCAL_YEAR, threshold)
        print_program_list(programs_for_threshold)
        print

if __name__ == "__main__":
    main()

