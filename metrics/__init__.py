#!/bin/python

import pickle
import metrics
import imp
import os
from settings import *

# convenience decorators for metrics

# true/false tests
def boolean(target):
    target.is_metric = True
    target.metric_type = 'boolean'
    return target
        
# calculates more aggregate statistics
def real(target):
    target.is_metric = True
    target.metric_type = 'real'
    return target
    
# calculates the same statistics as float, but also assembles a histogram
def integer(target):
    target.is_metric = True
    target.metric_type = 'integer'
    return target

# /decorators



# main tester object
class MetricTester(object):
    """ Performs specified tests on rows """
    def __init__(self):
        super(Tester, self).__init__()
        
        self.finished = False
        
        # bootstrap tests
        self.metrics = []
        for filename in os.listdir(str(''.join(__path__))):
            if filename[-3:]==".py" and not "__init__" in filename:
                (p_file, p_pathname, p_description) = imp.find_module(filename[:-3], [__name__])
                if p_file is not None:
                    m = imp.load_module(filename[:-3], p_file, p_pathname, p_description)
                    for candidate_name in dir(m):
                        candidate = getattr(m, candidate_name)
                        if callable(candidate):
                            if getattr(candidate, 'is_metric', False):
                                self.metrics.append(candidate)
    
    
    def _row_to_dict(row):
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

        # convert to a hash for convenience of the metric test functions
        row = self._row_to_dict(row)

        for test in self.metrics:
            pass


        
    def finish(self):
        """ calculate aggregate values """
        # TODO: calculate the aforementioned aggregate values
        self.finished = True
        pass
        
    def emit(self):
        """ spits out a pickled object of the results """
        if not self.finished:
            self.finish()
        
        # TODO: uh, this        
        pass
        