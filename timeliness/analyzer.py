import os
import sys
import cPickle as pickle
from metrics.models import ProgramTimeliness, AgencyTimeliness
from cfda.models import Program, Agency
from timeliness.cube import Cube
from timeliness import (DATA_DIR, DOWNLOAD_DIR, FISCAL_YEARS)


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
    
    c = Cube()

    print 'analyzing pickled cfda awards data...'
    
    print 'initalizing...'
    
    cfda_agency_map = {}
    
    for program in Program.objects.all():
    
        cfda_agency_map[program.program_number] = program.agency_id
    
    print 'loading data...'
    
    f = open(os.path.join(DATA_DIR, 'cfda_awards.out.bin'), 'rb')
    awards = pickle.load(f)
    f.close()
    
    print 'building cube...'
    
    for award_id in awards:
         
        award = awards[award_id]
        
        cfda = award['cfda']
        
        if cfda_agency_map.has_key(cfda):
         
            agency = cfda_agency_map[cfda]
            
            fed_amount = award['fed_amount']
            fiscal_year  = award['fiscal_year']
            reporting_lag = award['reporting_lag']
            fiscal_year_lag = award['fiscal_year_lag']
            
            # reporting lag of negative days converted to 0
            reporting_lag = reporting_lag if reporting_lag > 0 else 0
            
            # select only fy 2007-2009 inclusive 
            if fiscal_year > 2009 or fiscal_year < 2007:
                continue
            
            # filter transactions that occur later than 180 days after the end of the fiscal year
            # this allows us to make a comparison between 2007/2008 and 2009. 
            if fiscal_year_lag > 180:
                continue 
            
            # add record to data cube
            c.add({'fy':fiscal_year, 'cfda':cfda, 'agency':agency}, {'days':reporting_lag, 'dollars':fed_amount})
    
    awards = None 
    
    print 'querying cfda aggregates...'
    
    result = c.query(groups=['cfda','fy'])
    
    print 'loading cfda results into db...'
    
    ProgramTimeliness.objects.all().delete()

    for cfda in result.values:
        
        program = Program.objects.get(program_number=cfda)
        
        for fy in range(2007, 2010):
            
            metric = ProgramTimeliness.objects.create(program=program, 
                                                   agency=program.agency, 
                                                   fiscal_year=fy,
                                                   late_dollars=result.values[cfda].values[fy].get_data(aggregator=sum_dollars_45days_late),
                                                   late_rows=result.values[cfda].values[fy].get_data(aggregator=count_records_45days_late),
                                                   total_dollars=result.values[cfda].values[fy].get_data(aggregator=sum_dollars),
                                                   total_rows=result.values[cfda].values[fy].get_data(aggregator=len),
                                                   avg_lag_rows=result.values[cfda].values[fy].get_data(aggregator=avg_days_by_awards),
                                                   avg_lag_dollars=result.values[cfda].values[fy].get_data(aggregator=avg_days_by_dollars))
    
            metric.save()
            
            
    print 'querying agency aggregates...' 
     
    result = c.query(groups=['agency','fy'])
    
    print 'loading agency results into db...'
    
    AgencyTimeliness.objects.all().delete()

    for agency_id in result.values:
        
        agency = Agency.objects.get(pk=agency_id)
        
        for fy in range(2007, 2010):
            
            metric = AgencyTimeliness.objects.create(agency=agency, 
                                                   fiscal_year=fy,
                                                   late_dollars=result.values[agency_id].values[fy].get_data(aggregator=sum_dollars_45days_late),
                                                   late_rows=result.values[agency_id].values[fy].get_data(aggregator=count_records_45days_late),
                                                   total_dollars=result.values[agency_id].values[fy].get_data(aggregator=sum_dollars),
                                                   total_rows=result.values[agency_id].values[fy].get_data(aggregator=len),
                                                   avg_lag_rows=result.values[agency_id].values[fy].get_data(aggregator=avg_days_by_awards),
                                                   avg_lag_dollars=result.values[agency_id].values[fy].get_data(aggregator=avg_days_by_dollars))
    
            metric.save()
    
    

if __name__ == "__main__":
    analyzer_main()

