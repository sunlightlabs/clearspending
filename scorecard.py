#!/bin/python

import sys, csv
from settings import *
from metrics import MetricTester


def main():
    """
    >>> from metrics import MetricTester
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
        
    
        
        

if __name__ == '__main__':
    if '--test' in sys.argv:
        import doctest
        doctest.testmod()
    else:
        main()