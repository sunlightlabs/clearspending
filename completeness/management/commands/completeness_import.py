from django.core.management.base import NoArgsCommand
import sys
from cfda.models import *
from metrics.models import *
from settings import *
from decimal import Decimal
from faads_scorecard.completeness import MetricTester
import pickle
import sys
import csv


def load_pickle_file(filename):
    f = open(filename, 'r')
    r = pickle.load(f)
    f.close()
    return r


def main():
    
    # clear out old summary objects
    ProgramCompleteness.objects.all().delete()
    ProgramCompletenessDetail.objects.all().delete()
    
    for y in FISCAL_YEARS:
        print 'processing fiscal year %d' % y
        data_pct = load_pickle_file('completeness/output/%d.pickle' % y)
        data_bad_dollars = load_pickle_file('completeness/output/%d-dollars_misreported.pickle' % y)
        data_total_dollars = load_pickle_file('completeness/output/%d-dollars_total.pickle' % y)
        
        for program_number in data_pct:      
            print '   processing %s' % program_number  
            program = None
            try:
                program = Program.objects.get(program_number=program_number)
            except Program.DoesNotExist, e:
                print "   no entry found for program with CFDA number %s" % program_number
                continue
            
            # save detailed program-level test information    
            PCD = ProgramCompletenessDetail()
            PCD.fiscal_year = y
            PCD.program = program
            PCD.agency = PCD.program.agency
            
            total_successful_tests = 0
            total_tests = 0
            
            for metric_name in data_pct[program_number]:
                
                if metric_name[0:2]=='__':
                    continue
                
                metric_model_name = metric_name.split('.')[-1]
                setattr(PCD, metric_model_name, Decimal(str(data_pct[program_number][metric_name].dollars_of_failed_tests)))                

            PCD.save()
            
            # save program-level summary
            PC = ProgramCompleteness()
            PC.fiscal_year = y
            PC.program = program
            PC.agency = PC.program.agency
            PC.completeness_failed_dollars = data_bad_dollars.get(program.program_number, None)
            PC.completeness_total_dollars = data_total_dollars.get(program.program_number, None)
            PC.save()
            
            
                
            
            



class Command(NoArgsCommand):
    help = "Import pickle files produced by completeness testing"

    def handle_noargs(self, **options):
        main()
                
            
                
