import plac
from metrics.models import ProgramTimeliness, ProgramConsistency, ProgramCompleteness
from cfda.models import Program, ProgramObligation
from operator import attrgetter
from decimal import Decimal
from settings import FISCAL_YEARS
from helpers.charts import Pie
from utils import pretty_money
from settings import MEDIA_ROOT


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


def best_programs(fiscal_year, range_low, range_high):
    """To make the list a program must come in under the threshold
    for both the completeness metric and the consistency metric.
    Additionally any program that is over the threshold for the
    timeliness metric will be removed from the list
    """
    timeliness = ProgramTimeliness.objects.filter(fiscal_year=fiscal_year,
                                                  late_pct__gte=range_low,
                                                  late_pct__lt=range_high).exclude(total_dollars='0.0')
    under_reporting = ProgramConsistency.objects.filter(fiscal_year=fiscal_year,
                                                        type=1,
                                                        under_reported_pct__isnull=False,
                                                        under_reported_pct__gte=range_low,
                                                        under_reported_pct__lt=range_high,
                                                        non_reported_dollars__isnull=True)
    over_reporting = ProgramConsistency.objects.filter(fiscal_year=fiscal_year,
                                                       type=1,
                                                       over_reported_pct__isnull=False,
                                                       over_reported_pct__gte=range_low,
                                                       over_reported_pct__lt=range_high,
                                                       non_reported_dollars__isnull=True)
    accurate_reporting = ProgramConsistency.objects.filter(fiscal_year=fiscal_year,
                                                           type=1,
                                                           over_reported_pct__isnull=True,
                                                           under_reported_pct__isnull=True,
                                                           non_reported_pct__isnull=True)
    completeness = [pc for pc in ProgramCompleteness.objects.filter(fiscal_year=fiscal_year)
                    if Decimal(range_low) < pc.failed_pct < Decimal(range_high)]


    get_program_id = attrgetter('program_id')
    timeliness_set = set(map(get_program_id, timeliness))
    consistency_set = set(map(get_program_id, under_reporting) +
                          map(get_program_id, over_reporting) +
                          map(get_program_id, accurate_reporting))
    completeness_set = set(map(get_program_id, completeness))
    best_program_ids = (consistency_set & completeness_set) - timeliness_set
    return best_program_ids


def print_program_list(fiscal_year, best_program_ids):
    best_program_consistencies = list(ProgramConsistency.objects.filter(fiscal_year=fiscal_year,
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
        program_obligation = ProgramObligation.objects.get(fiscal_year=fiscal_year,
                                                           type=1,
                                                           program=prog_consistency.program_id)

        prog_completeness = ProgramCompleteness.objects.get(fiscal_year=fiscal_year,
                                                            program=prog_consistency.program_id)
        try:
            prog_timeliness = ProgramTimeliness.objects.get(fiscal_year=fiscal_year,
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
            'consistency': (str(over_or_under) + '%'
                            if over_or_under else '---'),
            'completeness': str(round(prog_completeness.failed_pct)) + '%' if prog_completeness.failed_pct is not None else '---',
            'timeliness': str(round(prog_timeliness.late_pct)) + '%' if prog_timeliness and prog_timeliness.late_pct is not None else '---',
            'cfda': pretty_money(program_obligation.obligation)
        }
        print fmtstr.format(**values)
                                     

def main_chart(fiscal_year):
    good_cnt = len(best_programs(fiscal_year, 0, 26))
    avg_cnt = len(best_programs(fiscal_year, 26, 51))
    poor_cnt = len(best_programs(fiscal_year, 51, 1000000000))

    series = [[('',good_cnt),('',avg_cnt),('',poor_cnt)]]

    chart = Pie(240, 240, series,
                show_labels=False,
                stylesheet=MEDIA_ROOT + '/styles/bestprograms.css',
                x_padding=0, y_padding=0)
    chart.output(MEDIA_ROOT + '/images/charts/program-consistency-pie.svg')


def main_lists(fiscal_year):
    thresholds = ['1', '25', '50', '75', '100', '101', '110', '1000', '10000', '100000']
    lists = dict.fromkeys(thresholds)
    cumulative = set()

    for threshold in thresholds:
        programs_for_threshold = best_programs(fiscal_year, threshold)
        lists[threshold] = programs_for_threshold - cumulative
        cumulative = cumulative.union(programs_for_threshold)

    for threshold in thresholds:
        programs_for_threshold = lists[threshold]
        print "%s%d programs in %d at %s%% threshold" % (
            "" if threshold == thresholds[0] else "plus ",
            len(programs_for_threshold), 
            fiscal_year, threshold)
        print_program_list(fiscal_year, programs_for_threshold)
        print


@plac.annotations(
    target=('Output target type', 'positional', None, str, ['chart', 'lists'], 'TARGET'),
    fiscal_year=('Fiscal year', 'option', None, int, FISCAL_YEARS, 'FISCAL_YEAR'),
)
def main(target, fiscal_year=None):
    fiscal_year = fiscal_year or max(FISCAL_YEARS)
    if target == "lists":
        main_lists(fiscal_year)
    else:
        main_chart(fiscal_year)

if __name__ == "__main__":
    plac.call(main)

