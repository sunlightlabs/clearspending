#!/bin/python

import sys, csv, os, imp, pickle
from settings import *
from completeness.statlib import stats
from decimal import Decimal
import doctest

BOOKMARK = 'completeness/bookmark.pickle'


def success_rate(year):
    f = open('completeness/output/%d.pickle' % year, 'r')
    obj = pickle.load(f)
    f.close()
    
    program_totals = {}
    
    for program in obj:
        program_sum = 0
        program_total = 0
        if program!='__all__':
            for (test, result) in obj[program].items():
                test_name = test.replace('metric_completeness.', '')
                # if test_name=='obligation_action_date_is_properly_formatted':
                if result.tests_completed_without_error>0:
                    rate = (result.sum / (result.tests_completed_without_error * 1.0))
                else:
                    rate = 0
                print "%7s %20s %f" % (program, test_name, rate)
                
                program_sum += result.sum
                program_total += result.tests_completed_without_error
                
        if program_total > 0:
            program_totals[program] = program_sum / (program_total * 1.0)            
    
    for (p, r) in program_totals.items():
        print "%7s %f" % (p, r)
    

class Result(object):
    """ Stores the results of our metric tests. A bit fancier than a dict. """
    def __init__(self, result_type="boolean"):
        super(Result, self).__init__()

        self.result_type = result_type

        self.tests_run = 0
        self.tests_completed_without_error = 0     
        self.failed_tests = 0
        self.dollars_sum = 0
        self.dollars_of_passed_tests = 0   
        self.dollars_of_failed_tests = 0
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
            self.dollars_sum += abs(kwargs['dollars'])

        if val is False:
            self.failed_tests += 1

        if self.result_type is 'boolean':
            if val is True:
                self.sum += 1
                if kwargs.has_key('dollars') and kwargs['dollars'] is not None:
                    self.dollars_of_passed_tests += abs(kwargs['dollars'])
            elif val is False:
                if kwargs.has_key('dollars') and kwargs['dollars'] is not None:
                    self.dollars_of_failed_tests += abs(kwargs['dollars'])
        else:        
            self.sum += val
            
            self.values.append(val)

            if self.result_type is 'integer':
                if not self.histogram.has_key(val):
                    self.histogram[val] = 0
                self.histogram[val] += 1

    def finish(self):
        if self.result_type in ('integer', 'real'):
            if len(self.values)>0:
                self.mean = stats.mean(self.values)
            if len(self.values)>1:
                self.std_dev = stats.stdev(self.values)
            self.count = len(self.values) # this should be the same as self.tests_completed_without_error, but is a little clearer for adding stats
        del self.values # no need to keep all that garbage
        self.values = []
        
        

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
        
        self.misreported_dollars = {}      
        self.total_dollars = {}  
        
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
    
    
    def record_dollars(self, cfda_program, misreported_dollars, total_dollars):
        if not self.misreported_dollars.has_key(cfda_program):
            self.misreported_dollars[cfda_program] = 0
        self.misreported_dollars[cfda_program] += abs(misreported_dollars)
        
        if not self.total_dollars.has_key(cfda_program):
            self.total_dollars[cfda_program] = 0
        self.total_dollars[cfda_program] += abs(total_dollars)
        
        
    def _row_to_dict(self, row):
        """ Turns the incoming row into a hash for ease of use """
        r = {}
        for (field_index, field_name) in enumerate(CANONICAL_FIELD_ORDER):
            if field_index < len(row):
                r[field_name] = row[field_index]
        return r 

    def run_metrics(self, row):
        """ runs the specified metrics/tests on the passed row (which is a dict) """
        
        self.finished = False

        # if necessary, convert to a hash for convenience of the metric test functions
        if type(row) is list:
            row = self._row_to_dict(row)


        dollars = None
        try:
            amt = len(str(row['fed_funding_amount']).strip())>0 and str(row['fed_funding_amount']) or '0'
            dollars = Decimal(amt)
        except Exception, e:
            dollars = 0        

        
        row_all_clean = True
        for (metric_name, metric_func) in self.metrics.items():                      

            # set up necessary hashes and result objects
            cfda_number = row['cfda_program_num']
            if not self.results.has_key(cfda_number):
                self.results[cfda_number] = {}            
            if not self.results[cfda_number].has_key('__all__'):
                self.results[cfda_number]['__all__'] = Result()
            if not self.results[cfda_number].has_key('__byrow__'):
                self.results[cfda_number]['__byrow__'] = Result()
            if not self.results[cfda_number].has_key(metric_name):
                self.results[cfda_number][metric_name] = Result(result_type=metric_func.metric_type)                        

            mf = metric_func(row)
                        
            for t in (self.results[cfda_number][metric_name], self.results[cfda_number]['__all__'], self.results['__all__']):
                t.record_attempt()
                t.record_val(mf, dollars=dollars)
                t.record_success()
                               
            row_all_clean = row_all_clean and mf

        
        # record by-row metric -- if it passed all tests, it's okay
        # this lets us only count problem rows once
        if row_all_clean:
            self.record_dollars(cfda_program=cfda_number, misreported_dollars=0, total_dollars=dollars)
        else:
            self.record_dollars(cfda_program=cfda_number, misreported_dollars=dollars, total_dollars=dollars)            
            
        
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
            
    def emit_dollars(self, filename_misreported, filename_total):
        f = open(filename_misreported, 'w')
        pickle.dump(self.misreported_dollars, f)
        f.close()
        
        f = open(filename_total, 'w')
        pickle.dump(self.total_dollars, f)
        f.close()
            
        
        
def main_csv():

    for year in FISCAL_YEARS:

        print "Processing FAADS results for %d" % year

        mtester = MetricTester()

        f = open('completeness/csv/%d.csv' % year, 'r')
        reader = csv.reader(f)

        i = 0
        for row in reader:
            row = mtester._row_to_dict(row)
            mtester.run_metrics(row)        

            if (i%10000)==0:
                print "     processing record %d" % i

            i += 1

        f.close()

        mtester.emit(filename='completeness/output/%d.pickle' % year)
        mtester.emit_dollars(filename_misreported='completeness/output/%d-dollars_misreported.pickle' % year, filename_total='completeness/output/%d-dollars_total.pickle' % year)

def main():
    main_csv()

if __name__ == '__main__':
    if '--test' in sys.argv:
        doctest.testmod()
