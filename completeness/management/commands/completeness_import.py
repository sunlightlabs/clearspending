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
        data_dollars = load_pickle_file('completeness/output/%d-dollars.pickle' % y)
        
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
                
                this_run_passed_tests = data_pct[program_number][metric_name].sum
                this_run_total_tests = data_pct[program_number][metric_name].tests_completed_without_error
                
                total_successful_tests += this_run_passed_tests
                total_tests += this_run_total_tests
                
                if this_run_passed_tests>this_run_total_tests:
                    raise Exception('MISMATCH!!! %s %s %d %d' % (program_number, metric_name, this_run_passed_tests, this_run_total_tests))
                
                metric_model_name = metric_name.split('.')[-1]
                setattr(PCD, '%s_dollars' % metric_model_name, Decimal(str(data_pct[program_number][metric_name].dollars_of_failed_tests)))
                if this_run_total_tests>0:
                    setattr(PCD, '%s_pct' % metric_model_name, Decimal(str(this_run_passed_tests / (1.0 * this_run_total_tests))))
                else:
                    setattr(PCD, '%s_pct' % metric_model_name, Decimal('0'))
            PCD.save()
            
            # save program-level summary
            PC = ProgramCompleteness()
            PC.fiscal_year = y
            PC.program = program
            PC.agency = PC.program.agency
            if total_tests>0:
                PC.completeness_pct = Decimal(str(total_successful_tests / (1.0 * total_tests)))
            else:
                PC.completeness_pct = Decimal('0')
            PC.completeness_dollars = data_dollars.get(program.program_number, Decimal('0'))
            PC.save()
            
            
                
            
            



class Command(NoArgsCommand):
    help = "Import pickle files produced by completeness testing"

    def handle_noargs(self, **options):
        main()
                
            
                
