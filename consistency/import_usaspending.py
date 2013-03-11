
#Metric for consistency in USASpending versus CFDA reported obligations

import sys
import re
import csv
from decimal import Decimal
from datetime import datetime

import pg
import numpy as np

from metrics.models import ProgramCorrection, USASpendingAggregate
from cfda.models import Program, ProgramObligation
from utils import pretty_money

from django.conf import settings

def fix_cfda_program_all_years(program_number):
    program = Program.objects.get(program_number=program_number)
    obligations = list(program.programobligation_set.order_by('obligation_type', 'fiscal_year'))

    def print_obligations():
        print "{0}\t{1}".format(program_number, program.program_title)
        print "\tURL:   {0}".format(program.url)
        for (i, o) in enumerate(obligations):
            print "{0}: {1}\t{2}".format(i, 'Grants' if o.obligation_type == 1 else 'Loans', o.fiscal_year)
            print "\t\tCFDA:  {0!s: >17} ({1}) {2}".format(pretty_money(o.obligation or 0), o.obligation, 'CORRECTED' if o.corrected else '')
            print "\t\tFAADS: {0!s: >17} ({1})".format(pretty_money(o.usaspending_obligation or 0), o.usaspending_obligation)
            print

    while True:
        print_obligations()
        response = raw_input("To fix an obligation, enter the number followed by the corrected value. Press 'q' to quit): ")
        if response.lower() in ('q', 'quit'):
            break
        elif response == '':
            pass
        else:
            try:
                (i, new_value) = re.split(ur'[:,\s]+', response.strip())
                i = int(i)
            except ValueError:
                print "I don't understand what you mean!"
                continue
            update_obligation(new_value, obligations[i])

def fix_cfda():
    #Identify possible cfda mistakes
        
    fin_programs = Program.objects.filter(types_of_assistance__financial=True)
    fin_obligations = ProgramObligation.objects.filter(program__in=fin_programs)

    for fy in settings.FISCAL_YEARS:
        over_programs = fin_obligations.filter(fiscal_year=fy, weighted_delta__gt=0)
        sd = np.std([float(v) for v in over_programs.values_list('weighted_delta', flat=True)])
        avg = np.average([float(v) for v in over_programs.values_list('weighted_delta', flat=True)])
        new_over = over_programs.filter(weighted_delta__lte=str(((3*sd) + avg)))
        sd_new = np.std([float(v) for v in new_over.values_list('weighted_delta', flat=True)])
        avg_new = np.average([float(v) for v in new_over.values_list('weighted_delta', flat=True)])

        outliers = over_programs.filter(weighted_delta__gte=str(avg_new)).exclude(corrected=True)
        def print_outliers():
            print "Possible CFDA mistakes for FY %s" % fy
            i = 1
            for o in outliers:
                print "{0}: {1}\t{2}".format(i, o.program.program_number, o.program.program_title)
                print "\t\tURL:   {0}".format(o.program.url)
                print "\t\tCFDA:  {0!s: >17}".format(pretty_money(o.obligation))
                print "\t\tFAADS: {0!s: >17}".format(pretty_money(o.usaspending_obligation))
                print "\t\tWeighted delta: {0}".format(o.weighted_delta)
                print
                i += 1

        print_outliers()
        while True:
            input = raw_input("fix an obligation? (enter number of obligation, q to quit, or n to move to the next FY): ")
            if input == 'q':
                sys.exit()

            elif input == 'n':
                break

            elif input == '':
                print_outliers()

            elif 0 < int(input) <= len(outliers):
                program = outliers[int(input)-1]
                new_obligation = raw_input("Enter the new CFDA obligation for %s: " % program.program.program_title)
                if int(new_obligation) > program.obligation:
                    update_obligation(new_obligation, program)
                    print "%s obligation updated to %s" % (program.program.program_title, new_obligation)
                else:
                    confirm = raw_input('amount entered is less than original obligation. Continue anyway?(y or n): ')
                    if confirm == 'y':
                        update_obligation(new_obligation, program)
                    else:
                        continue
                    

def update_obligation(new_obligation, program):
    
    old_obligation = program.obligation
    program.obligation = int(new_obligation)
    program.corrected = True
    program.save()

    correction = ProgramCorrection(program=program.program, program_obligation=program, corrected_obligation=program.obligation, old_obligation=old_obligation, note="Corrected manually in program run",  correction_date=datetime.today())
    correction.save()

if __name__ == '__main__':


    conn = pg.connect(host=settings.PG_HOST, user=settings.PG_USER,
                      passwd=settings.PG_PASSWORD, dbname=settings.PG_DATABASE,
                      port=settings.PG_PORT)
    bogus_cfda = open('csv/bogus_cfda_program_numbers', 'w')
    bogus_cfda_writer = csv.writer(bogus_cfda)

    programs = Program.objects.all().order_by('program_number')
    program_data = {}
    
    usaspending_total = dict.fromkeys(settings.FISCAL_YEARS, 0)

    usa_query = "SELECT fiscal_year, SUM(fed_funding_amount) as fed_funding_amount FROM %s WHERE fiscal_year >= %s AND fiscal_year <= %s GROUP BY fiscal_year" % (settings.PG_TABLE_NAME,
                                                                                                                                                                  min(settings.FISCAL_YEARS),
                                                                                                                                                                  max(settings.FISCAL_YEARS))
    print "Fetching aggregate spending totals from USASpending"
    rows = conn.query(usa_query).dictresult()
    
    for row in rows:
        agg = USASpendingAggregate(fiscal_year=row['fiscal_year'])
        agg.total_federal_funding = row['fed_funding_amount']
        agg.save()

    usa_query = "SELECT cfda_program_num, fiscal_year, SUM(fed_funding_amount) as fed_funding_amount, SUM(face_loan_guran) as face_loan_guran FROM %s WHERE fiscal_year >= %s AND fiscal_year <= %s GROUP BY cfda_program_num, fiscal_year ORDER BY cfda_program_num" % (settings.PG_TABLE_NAME,
                                                                                                                                                                                                                                                                         min(settings.FISCAL_YEARS),
                                                                                                                                                                                                                                                                         max(settings.FISCAL_YEARS))
    print usa_query
    print "fetching summary query with rollup of programs, fiscal years and total obligations"
    rows = conn.query(usa_query).dictresult()
    
    for row in rows:
        print row
        try:    
            if row['cfda_program_num']:
                usaspending_total[row['fiscal_year']] += row['fed_funding_amount']
                program = Program.objects.get(program_number=row['cfda_program_num'])
                if row['fed_funding_amount'] > 0:
                    cfda_ob = ProgramObligation.objects.get(program=program,
                                                            fiscal_year=row['fiscal_year'],
                                                            obligation_type=1)
                    cfda_ob.usaspending_obligation = row['fed_funding_amount']
                    cfda_ob.save()
                if row['face_loan_guran'] > 0:
                    cfda_ob = ProgramObligation.objects.get(program=program,
                                                            fiscal_year=row['fiscal_year'],
                                                            obligation_type=2)
                    cfda_ob.usaspending_obligation = row['face_loan_guran']
                    cfda_ob.save()

                    #print "MATCH: %s - %s - %s - %s diff %s" % (row[0], row[1], cfda_ob.obligation, cfda_ob.usaspending_obligation, cfda_ob.delta)
            else:
                bogus_cfda_writer.writerow([row['cfda_program_num'], row['fed_funding_amount'], row['fiscal_year']])
        except Program.DoesNotExist, e:
            bogus_cfda_writer.writerow([row['cfda_program_num'], row['fed_funding_amount'], row['fiscal_year']])

        except ProgramObligation.DoesNotExist, e:
            pass

    print "Total processed: %s" % usaspending_total

    fix_cfda()


