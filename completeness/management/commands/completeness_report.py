from django.core.management.base import NoArgsCommand
import sys
from cfda.models import *
from settings import *
from decimal import Decimal
from faads_scorecard.completeness import MetricTester
import pickle
import sys
import csv

def test_load():
    data = {}
    for y in FISCAL_YEARS:
        print "loading %d" % y
        f = open('completeness/output/%d.pickle' % y, 'r')
        data[y] = pickle.load(f)
        f.close()
    return data

def main():
    BLANK = ''
    
    test_success = {}
    test_total = {}
    
    writer = csv.writer(sys.stdout)
    
    mt = MetricTester()
    data = {}
    for y in FISCAL_YEARS:
        # print "loading %d" % y
        f = open('completeness/output/%d.pickle' % y, 'r')
        data[y] = pickle.load(f)
        f.close()
    
    row = ['Program', 'Test']
    for y in FISCAL_YEARS:
        row.append('%d Success (n)' % y)
        row.append('%d Total (n)' % y)
        row.append('%d %% (n)' % y)
        row.append('%d Success ($)' % y)
        row.append('%d Total ($)' % y)
        row.append('%d %% ($)' % y)

    writer.writerow(row)

    for program in Program.objects.all().order_by('program_number'):
        program_number = program.program_number.strip()
        row = ['%s - %s' % (program.program_number.encode('utf-8'), program.program_title.encode('utf-8')), '']
        for y in FISCAL_YEARS:
            result = data[y].get(program_number, {}).get('__all__', None)
            if result is None:
                for i in range(4):
                    row.append(BLANK)
            else:
                row.append(result.sum)
                row.append(result.tests_completed_without_error)
                if result.tests_completed_without_error>0:
                    row.append(result.sum / (1.0 * result.tests_completed_without_error))
                else:
                    row.append(BLANK)
                row.append(result.dollars_of_passed_tests)
                row.append(result.dollars_sum)
                if result.dollars_sum>0:
                    row.append(result.dollars_of_passed_tests / (Decimal('1.0') * result.dollars_sum))
                else:
                    row.append(BLANK)
                                    
        writer.writerow(row)

        for test_name in mt.metrics.keys():
            test_display_name = test_name.replace('metric_completeness.', '')
            row = ['', test_display_name]
            for y in FISCAL_YEARS:
                result = data[y].get(program_number, {}).get(test_name, None)
                
                if result is None:
                    for i in range(6):
                        row.append(BLANK)
                else:
                    row.append(result.sum)
                    row.append(result.tests_completed_without_error)
                    if result.tests_completed_without_error>0:
                        row.append(result.sum / (1.0 * result.tests_completed_without_error))
                    else:
                        row.append(BLANK)
                    row.append(result.dollars_of_passed_tests)
                    row.append(result.dollars_sum)
                    if result.dollars_sum>0:
                        row.append(result.dollars_of_passed_tests / (Decimal('1.0') * result.dollars_sum))
                    else:
                        row.append(BLANK)

                    if not test_success.has_key(test_display_name):
                        test_success[test_display_name] = 0
                        test_total[test_display_name] = 0
                        
                    test_success[test_display_name] += result.sum
                    test_total[test_display_name] += result.tests_completed_without_error

                    
            writer.writerow(row)
            
            
    print
    print
    print
        
    for k in test_success.keys():
        if test_total[k]==0:
            print "%20s         0.00000           (     0)" % (k)
        else:
            print "%20s         %1.5f        (%5d)" % (k, (test_success[k] / (Decimal('1.0') * test_total[k])), test_total[k])
        

class Command(NoArgsCommand):
    help = "Transform pickled completeness test to CSV output"

    def handle_noargs(self, **options):
        main()
                
            
                
