from metrics.models import ProgramTimeliness, AgencyTimeliness
from numpy import mean
from helpers.charts import Pie
from utils import short_money
from settings import FISCAL_YEARS, MEDIA_ROOT

def main():
    for fy in FISCAL_YEARS:
        timely_programs = ProgramTimeliness.objects.filter(fiscal_year=fy, avg_lag_rows__lte='45')
        programs_available = ProgramTimeliness.objects.filter(fiscal_year=fy)
        pct = len(timely_programs) * 100 / len(programs_available)
        avg_avg_lag_rows = mean([t.avg_lag_rows for t in programs_available])
        print "%d: %d / %d (%.2f%%) programs with avg lag <=45 days, avg program lag: %.2f days" % (
            fy,
            len(timely_programs),
            len(programs_available),
            pct,
            avg_avg_lag_rows
        )

    for fy in FISCAL_YEARS:
        timely_agencies = AgencyTimeliness.objects.filter(fiscal_year=fy, avg_lag_rows__lte='45')
        agencies_available = AgencyTimeliness.objects.filter(fiscal_year=fy)
        pct = len(timely_agencies) * 100 / len(agencies_available)
        avg_avg_lag_rows = mean([t.avg_lag_rows for t in agencies_available])
        print "%d: %d / %d (%.2f%%) agencies with avg lag <=45 days, avg agency lag: %.2f days" % (
            fy,
            len(timely_agencies),
            len(agencies_available),
            pct,
            avg_avg_lag_rows)
    
    for fy in FISCAL_YEARS:
        all_agencies = AgencyTimeliness.objects.filter(fiscal_year=fy)
        timely_sum = sum([t.total_dollars - t.late_dollars for t in all_agencies])
        tardy_sum = sum([t.late_dollars for t in all_agencies])
        tardy_pct = tardy_sum * 100 / (timely_sum + tardy_sum)

        pie = Pie(170, 170, [[('Timely', float(timely_sum))],
                             [('Tardy', float(tardy_sum))]],
                  show_labels=False,
                  stylesheet=MEDIA_ROOT + '/styles/timeliness-charts.css',
                  x_padding=0, y_padding=0)
        pie.output(MEDIA_ROOT + '/images/charts/program-timeliness-%d.svg' % fy)


        print "%d: timely %s vs %s tardy, %.2f%% tardy" % (fy,
                                                           short_money(timely_sum),
                                                           short_money(tardy_sum),
                                                           tardy_pct)

if __name__ == "__main__":
    main()
