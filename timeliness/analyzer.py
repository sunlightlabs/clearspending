import os
import sys
import cPickle as pickle
import stream
from utils import unpickle
from operator import itemgetter, le, add
from functools import partial
from metrics.models import ProgramTimeliness, AgencyTimeliness
from cfda.models import Program, Agency
from timeliness.cube import Cube
from timeliness import (DATA_DIR, DOWNLOAD_DIR, FISCAL_YEARS)
from settings import FISCAL_YEARS, FISCAL_YEAR_LAG_THRESHOLD

def sum_dollars(data):
    sum = 0
    for i in data:
        sum += i['dollars']
    return sum


def sum_dollars_45days_late(data):
    sum = 0
    for i in data:
        if i['days'] > 45:
            sum += i['dollars']
    return sum


def count_records_45days_late(data):
    count = 0
    for i in data:
        if i['days'] > 45:
            count += 1
    return count


def avg_days_by_awards(data):
    award_count = 0
    sum_days = 0
    for i in data:
        award_count += 1
        sum_days += i['days']
    return sum_days / award_count


def avg_days_by_dollars(data):
    sum_dollars = 0
    sum_dollar_days = 0
    for i in data:
        sum_dollars += i['dollars']
        sum_dollar_days += (i['days'] * i['dollars'])
    if sum_dollars:
        return (sum_dollar_days / sum_dollars)
    else: 
        return 0


def analyzer_main():
    print 'Loading data...'
    cfda_agency_map = dict((p.program_number, p.agency_id) 
                           for p in Program.objects.all())
   
    awards = unpickle(os.path.join(DATA_DIR, 'cfda_awards.out.bin'))
    
    print 'Building cube'
    c = Cube()
    for (idx, (award_id, award)) in enumerate(awards.iteritems()):
        # Simple progress ticker
        if idx % 1000 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

        cfda = award['cfda']
        agency = cfda_agency_map.get(cfda, None)
        if agency:
            fed_amount = award['fed_amount']
            fiscal_year  = award['fiscal_year']
            reporting_lag = award['reporting_lag']
            fiscal_year_lag = award['fiscal_year_lag']
            
            # select only fy 2007-2009 inclusive 
            if fiscal_year not in FISCAL_YEARS:
                continue

            # We need to set an upper bound on the fiscal year lag in order to
            # make comparisons between fiscal years useful.
            if fiscal_year_lag > FISCAL_YEAR_LAG_THRESHOLD:
                continue 
            
            # reporting lag of negative days converted to 0
            reporting_lag = reporting_lag if reporting_lag > 0 else 0
            
            # add record to data cube
            c.add({'fy':fiscal_year, 'cfda':cfda, 'agency':agency}, {'days':reporting_lag, 'dollars':fed_amount})


    awards = None 

    print 'Querying cfda aggregates...'
    result = c.query(groups=['cfda','fy'])
    
    print 'Loading cfda results into db...'
    ProgramTimeliness.objects.all().delete()

    for (cfda, cfda_results) in result.values.iteritems():
        program = Program.objects.get(program_number=cfda)
        
        for fy in FISCAL_YEARS:
            cfda_fy_results = cfda_results.values[fy]
            metric = ProgramTimeliness.objects.create(
                program=program, 
                agency=program.agency, 
                fiscal_year=fy,
                late_dollars=cfda_fy_results.get_data(sum_dollars_45days_late),
                late_rows=cfda_fy_results.get_data(count_records_45days_late),
                total_dollars=cfda_fy_results.get_data(sum_dollars),
                total_rows=cfda_fy_results.get_data(len),
                avg_lag_rows=cfda_fy_results.get_data(avg_days_by_awards),
                avg_lag_dollars=cfda_fy_results.get_data(avg_days_by_dollars)
            )
            if metric.total_dollars > 0:
                metric.late_pct = metric.late_dollars * 100 / metric.total_dollars
            metric.save()
            
            
    print 'Querying agency aggregates...' 
    result = c.query(groups=['agency','fy'])
    
    print 'Loading agency results into db...'
    AgencyTimeliness.objects.all().delete()

    for (agency_id, agency_results) in result.values.iteritems():
        agency = Agency.objects.get(pk=agency_id)
        
        for fy in FISCAL_YEARS:
            agency_fy_results = agency_results.values[fy]
            metric = AgencyTimeliness.objects.create(
                agency=agency, 
                fiscal_year=fy,
                late_dollars=agency_fy_results.get_data(sum_dollars_45days_late),
                late_rows=agency_fy_results.get_data(count_records_45days_late),
                total_dollars=agency_fy_results.get_data(sum_dollars),
                total_rows=agency_fy_results.get_data(len),
                avg_lag_rows=agency_fy_results.get_data(avg_days_by_awards),
                avg_lag_dollars=agency_fy_results.get_data(avg_days_by_dollars)
            )
            if metric.total_dollars > 0:
                metric.late_pct = metric.late_dollars * 100 / metric.total_dollars
            metric.save()
    
    

if __name__ == "__main__":
    analyzer_main()

