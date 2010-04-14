#!/bin/python

import sys, csv
from settings import *
from metrics import Tester


def generate_csvs():
    """ Creates the chunked CSV files that will be fed into the script """
    sql = "SELECT %s FROM %s WHERE (%s) ORDER BY record_id ASC" % (','.join(CANONICAL_FIELD_ORDER), SQL_TABLE_NAME, SQL_WHERE_CLAUSE)
    # TODO: generate CSV files of ROWS_PER_CSV_FILE rows in output/ based on the above query
    
def main():
    """
    >>> from metrics import MetricTester
    >>> t = MetricTester()
    """
    
    
    tester = Tester()
    
    reader = csv.reader(sys.stdin)
    while True:
        row = reader.next()
            
        # break if done
        if not row:
            break
        
        # convert to a hash for ease of use
        row = row_to_dict(row)
        
        # run each test
      
        # ALL:
        # - rows examined
        # - completed tests
        # 
        # BOOLEAN:
        # - successes
        # 
        # FLOAT:
        # - average
        # - standard deviation
        # 
        # 
        # 
        # INTEGER:
        # - histogram
        # - average
        # - standard deviation
        
    
        
        

if __name__ == '__main__':
    if '--csv' in sys.argv:
        generate_csvs()
    elif '--test' in sys.argv:
        import doctest
        doctest.testmod()
    else:
        main()