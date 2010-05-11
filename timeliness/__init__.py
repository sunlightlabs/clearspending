import urllib
import urllib2
import re
import os
import csv
import cPickle as pickle
from timeliness.cube import Cube
from BeautifulSoup import BeautifulSoup
from datetime import date    
    
DOWNLOAD_URL = 'http://www.usaspending.gov/downloads.php'
DATA_URL = 'http://www.usaspending.gov/'

DATA_DIR = 'timeliness_data/'
DOWNLOAD_DIR = DATA_DIR + 'raw/'


def download():
    
    print "downloading data from USASpending.gov..."
    
    if not os.path.exists(DATA_DIR):
        os.mkdir(DATA_DIR)
    
    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)

    # request list of agency submissions
    downloads_html = urllib2.urlopen(DOWNLOAD_URL)

    downloads_soup = BeautifulSoup(downloads_html.read())
    
    rows = downloads_soup.findAll('tr')
    
    for row in rows:
        
        columns = row.findAll('td')
        
        if len(columns) > 1:
            
            for link in columns[1].findAll('a'):
                
                if link.has_key('href') and link['href'][0:8] == 'uploads/':
                    
                    print link['href'][9:]
                    
                    data = urllib2.urlopen(DATA_URL + urllib.quote(link['href']))
                    f = open('%s%s' % (DOWNLOAD_DIR, link['href'][9:]), 'w')
                    f.write(data.read())
                    f.close()
  
                
def get_fiscal_year(d):
        
    if d.month < 10:
        return d.year
    else:
        return d.year + 1
        
                
def parse():
    awards = {}
    
    print "Processing raw USASpending data..."
    
    re_date1 = re.compile('(20[0-9]{2,2})[.\s\_]{1,1}([0-9]{1,2})[.\s\_]{1,1}([0-9]{1,2})')
    re_date2 = re.compile('(20[0-9]{2,2})([0-9]{2,2})([0-9]{2,2})')
    
    re_cfda = re.compile('^[0-9]{2,2}.[0-9]{3,3}$')
    
    
    failed_lines = open(DATA_DIR + 'failed_lines.out', 'w')
    failed_files = open(DATA_DIR + 'failed_files.out', 'w')
    
    duplicates = 0
    bad_records = 0
    bad_filenames = 0
    files_processed = 0
    
    
    for filename in os.listdir(DOWNLOAD_DIR):
        
        print filename
        
        try:
            m = re_date1.search(filename)
            if m:
                import_date = date(year=int(m.group(1)), month=int(m.group(2)), day=int(m.group(3)))
            else:
                m = re_date2.search(filename)
                if m:
                    import_date = date(year=int(m.group(1)), month=int(m.group(2)), day=int(m.group(3)))
                else:
                    bad_filenames += 1
                    failed_files.write('%s\n' % filename)
                    continue 
        except:
            bad_filenames += 1
            failed_files.write('%s\n' % filename)
            continue
    
    
        file = open(DOWNLOAD_DIR + filename)
        
        files_processed += 1
        
        
        for line in file:
            
            if line.strip() == '' or len(line) < 100:
                continue
            
            try:
                
                award = {}
                
                award['cfda'] = line[0:7].strip()
                award['action'] = line[135]
                award['award_id'] = line[142:158].strip()
                award['fed_amount'] = int(line[163:173])
                
                # for aggregates obligation date is the last day of the quarter
                award['obligation_date'] = date(year=int(line[196:200]), month=int(line[200:202]), day=int(line[202:204]))
                award['import_date'] = import_date     
                award['reporting_lag'] = (award['import_date'] - award['obligation_date']).days
                
                fiscal_year = get_fiscal_year(award['obligation_date'])
                
                award['fiscal_year_lag'] = (award['import_date'] - date(year=fiscal_year, month=9, day=30)).days
            
                award['fiscal_year'] = fiscal_year
                
                # only keep records with valid (non-alpha) cfda numbers
                if not re_cfda.match(award['cfda']):
                    bad_records += 1
                    continue
                
                # only process new transactions
                if award['action'] == 'A':
                    
                    # check for past transactions with same award_id
                    if awards.has_key(award['award_id']) and awards[award['award_id']]['cfda'] == award['cfda']:
                        
                        duplicates += 1
                        
                        #check if new transaction was reported first
                        if award['import_date'] < awards[award['award_id']]['import_date']:
                            
                            # keep earliest reported transaction
                            awards[award['award_id']] = award
                            
                    else:
                        awards[award['award_id']] = award
                    
                            
                    
            except:
                failed_lines.write(line)
                
            
        file.close()
    
    
    failed_lines.close()
    failed_files.close()
    
    print 'dump binary data...'
    
    f = open(DATA_DIR + 'cfda_awards.out.bin', 'wb')
    pickle.dump(awards, f)
    f.close()
    
    print 'bad filenames: %d' % bad_filenames
    print 'files processed: %d' % files_processed  
    print 'bad records: %d' % bad_records
    print 'duplicates: %d' % duplicates  
    print 'good records: %d' % len(awards)
    
    
def analyze():
    
    c = Cube()

    print 'analyzing pickled cfda awards data...'
    
    print 'loading data...'
    
    f = open(DATA_DIR + 'cfda_awards.out.bin', 'rb')
    awards = pickle.load(f)
    f.close()
    
    print 'building cube...'
    
    for award_id in awards:
        
        award = awards[award_id]
        
        cfda = award['cfda']
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
        c.add({'fy':fiscal_year, 'cfda':cfda}, {'days':reporting_lag, 'dollars':fed_amount})
    
    awards = None 
    
    print 'querying...'
    
    result = c.query(groups=['cfda','fy'])
    
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
    
    
    print 'load results into db...'
    
    
    f = open(DATA_DIR + 'cfda_reporting_lag.csv', 'w')
    writer = csv.writer(f)
    
    for cfda in result.values:
        row = []
        
        row.append(cfda)
        
        for fy in range(2007, 2010):
            
            row.append(result.values[cfda].values[fy].get_data(aggregator=len))
            row.append(result.values[cfda].values[fy].get_data(aggregator=sum_dollars))
            row.append(result.values[cfda].values[fy].get_data(aggregator=sum_dollars_45days_late))
            row.append(result.values[cfda].values[fy].get_data(aggregator=avg_days_by_awards))
            row.append(result.values[cfda].values[fy].get_data(aggregator=avg_days_by_dollars))
    
        writer.writerow(row)
        
    f.close()
