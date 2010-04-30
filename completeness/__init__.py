#!/bin/python

import sys, csv, os, imp, pickle
from settings import *
from completeness.statlib import stats
from decimal import Decimal
import MySQLdb
import doctest

BOOKMARK = 'completeness/bookmark.pickle'


class Result(object):
    """ Stores the results of our metric tests. A bit fancier than a dict. """
    def __init__(self, result_type="boolean"):
        super(Result, self).__init__()

        self.result_type = result_type

        self.tests_run = 0
        self.tests_completed_without_error = 0     
        self.dollars_sum = 0
        self.dollars_of_passed_tests = 0   
        self.sum = 0
        self.values = []
        
        if result_type in ('real', 'integer'):
            self.mean = None
            self.std_dev = None            
            if self.result_type is 'integer':
                self.histogram = {}
        
    def record_attempt(self):
        """ To be called prior to running the metric/test """
        self.tests_run += 1
        
    def record_success(self):
        """ To be called after the successful completion of the metric/test """
        self.tests_completed_without_error += 1
        
    def record_val(self, val, *args, **kwargs):
        """ To be passed the result of the metric/test """
        if kwargs.has_key('dollars') and kwargs['dollars'] is not None:
            self.dollars_sum += kwargs['dollars']

        if self.result_type is 'boolean':
            if val is True:
                self.sum += 1
                if kwargs.has_key('dollars') and kwargs['dollars'] is not None:
                    self.dollars_of_passed_tests += kwargs['dollars']
        else:        
            self.sum += val
            self.values.append(val)

            if self.result_type is 'integer':
                if not self.histogram.has_key(val):
                    self.histogram[val] = 0
                self.histogram[val] += 1

    def finish(self):
        if self.result_type in ('integer', 'real'):
            self.mean = stats.mean(self.values)
            if len(self.values)>1:
                self.std_dev = stats.stdev(self.values)
            self.count = len(self.values) # this should be the same as self.tests_completed_without_error, but is a little clearer for adding stats
        del self.values # no need to keep all that garbage
        
        

# main tester object
class MetricTester(object):
    """ Performs specified tests on rows 
    >>> m = MetricTester()
    ''
    
    """
    def __init__(self):
        super(MetricTester, self).__init__()
        
        self.finished = False

        self.results = {}
        self.results['__all__'] = Result()
        
        # bootstrap tests
        self.metrics = {}
        for filename in os.listdir('./completeness/metrics'):
            if filename[-3:]==".py" and not "__init__" in filename:
                module_name = filename[:-3]
                m = __import__('completeness.metrics.%s' % module_name)
                for candidate_name in dir(m.metrics.metric_completeness):
                    candidate = getattr(m.metrics.metric_completeness, candidate_name)
                    if callable(candidate):
                        if getattr(candidate, 'is_metric', False):
                            self.metrics["%s.%s" % (module_name, candidate_name)] = candidate
        
    def _row_to_dict(self, row):
        """ Turns the incoming row into a hash for ease of use """
        r = {}
        for (field_index, field_name) in enumerate(CANONICAL_FIELD_ORDER):
            r[field_name] = row[field_index]
        return r 

    def run_metrics(self, row):
        """ runs the specified metrics/tests on the passed row (which is a dict) """
        
        self.finished = False

        # sanity check for row length
        if len(row)!=len(CANONICAL_FIELD_ORDER):
            raise Exception("input row length (%d) does not match canonical row length (%d)" % (len(row), len(CANONICAL_FIELD_ORDER)))

        # if necessary, convert to a hash for convenience of the metric test functions
        if type(row) is list:
            row = self._row_to_dict(row)
        
        for (metric_name, metric_func) in self.metrics.items():            
            
            self.results['__all__'].record_attempt()            

            # set up necessary hashes and result objects
            cfda_number = row['cfda_program_num']
            if not self.results.has_key(cfda_number):
                self.results[cfda_number] = {}
            if not self.results[cfda_number].has_key(metric_name):
                self.results[cfda_number][metric_name] = Result(result_type=metric_func.metric_type)            
            
            success = True

            # try:

            dollars = None
            try:
                amt = len(str(row['fed_funding_amount']).strip())>0 and str(row['fed_funding_amount']) or '0'
                dollars = Decimal(amt)
            except Exception, e:
                raise e
            self.results[cfda_number][metric_name].record_attempt()
            mf = metric_func(row)
            self.results[cfda_number][metric_name].record_val(mf, dollars=dollars)
            self.results[cfda_number][metric_name].record_success()             
                               
            # except Exception,e:
            #     raise e
            #     success = False
                
            if success:
                self.results['__all__'].record_success()
            
        
    def finish(self):
        """ calculate aggregate values """
        for cfda_program_num in self.results:
            if cfda_program_num!='__all__':
                for metric in self.results[cfda_program_num].keys():
                    self.results[cfda_program_num][metric].finish()

        self.results['__all__'].finish()

        self.finished = True

        
    def emit(self, filename=None):
        """ spits out a pickled object of the results """
        if not self.finished:
            self.finish()
        
        if filename is None:
            return pickle.dumps(self.results)
        else:
            f = open(filename, 'w')
            pickle.dump(self.results, f)
            f.close()

def main_csv():
    """
    >>> from completeness.metrics import MetricTester
    >>> t = MetricTester()
    """    
    
    mtester = MetricTester()
    
    reader = csv.reader(sys.stdin)
    while True:
        row = reader.next()
            
        # break if done
        if not row:
            break
        
        # convert to a hash for ease of use
        row = row_to_dict(row)
        mtester.run_metrics(row)
        
    print mtester.emit()
        

def _store_bookmark(offset):
    f = open(BOOKMARK, 'w')
    pickle.dump(offset, f)
    f.close()


def main_debug():

    RECORD_ID_INDEX = CANONICAL_FIELD_ORDER.index('record_id')

    mtester_all = MetricTester()
    mtester = MetricTester()

    if not os.path.exists(BOOKMARK):
        _store_bookmark(0)

    f = open(BOOKMARK, 'r')
    offset = pickle.load(f)
    f.close()

    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, cursorclass=MySQLdb.cursors.DictCursor)    
    cursor = conn.cursor()

    for year in FISCAL_YEARS:

        while True:

            print "querying - FY%d / offset %d" % (year, offset)
            # 
            # sql = "SELECT * FROM %s WHERE (fiscal_year=%d) AND record_id>%d ORDER BY record_id ASC LIMIT %d" % (MYSQL_TABLE_NAME, year, offset, ROWS_PER_CYCLE)
            # print sql
            # cursor.execute(sql.replace("\n", " "))

            print "finished query, processing..."

            while True:
                row = pickle.load(open('debug_row.pickle'))

                # convert to a hash for ease of use
                mtester.run_metrics(row)        
                mtester_all.run_metrics(row)
                offset = row['record_id']
                
                break

            # store intermediate results
            f = open('completeness/output/%d/%d.pickle' % (year, offset), 'w')
            f.write(mtester.emit())
            f.close()

            # compact/reset tester objects
            mtester_all.finish()
            del mtester
            mtester = MetricTester()

            # increment
            offset += ROWS_PER_CYCLE
            _store_bookmark(offset)


        f = open('output/%d/all.pickle', 'w')
        f.write(mtester_all.emit())
        f.close()


def main_mysql():

    RECORD_ID_INDEX = CANONICAL_FIELD_ORDER.index('record_id')
    
    mtester_all = MetricTester()
    mtester = MetricTester()
    
    if not os.path.exists(BOOKMARK):
        _store_bookmark(0)
    
    f = open(BOOKMARK, 'r')
    offset = pickle.load(f)
    f.close()
    
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, cursorclass=MySQLdb.cursors.DictCursor)    
    cursor = conn.cursor()

    for year in FISCAL_YEARS:
        
        while True:
            
            print "querying - FY%d / offset %d" % (year, offset)
            
            sql = "SELECT * FROM %s WHERE (fiscal_year=%d) AND record_id>%d ORDER BY record_id ASC LIMIT %d" % (MYSQL_TABLE_NAME, year, offset, ROWS_PER_CYCLE)
            print sql
            cursor.execute(sql.replace("\n", " "))

            print "finished query, processing..."

            while True:
                row = cursor.fetchone()
                if row is None:
                    break
            
                pickle.dump(row, open('debug_row.pickle', 'w'))
            
                # convert to a hash for ease of use
                mtester.run_metrics(row)        
                mtester_all.run_metrics(row)
                offset = row['record_id']

            # store intermediate results
            f = open('completeness/output/%d/%d.pickle' % (year, offset), 'w')
            f.write(mtester.emit())
            f.close()
            
            # compact/reset tester objects
            mtester_all.finish()
            del mtester
            mtester = MetricTester()
                
            # increment
            offset += ROWS_PER_CYCLE
            _store_bookmark(offset)


        f = open('output/%d/all.pickle', 'w')
        f.write(mtester_all.emit())
        f.close()


def main():
    main_mysql()
    # main_debug()

if __name__ == '__main__':
    if '--test' in sys.argv:
        doctest.testmod()
