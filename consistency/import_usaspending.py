
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
from metrics.models import ProgramCorrection
import MySQLdb
import csv
from datetime import datetime
import numpy as np
FISCAL_YEAR = 2008

def fix_cfda():
    #Identify possible cfda mistakes
        
    fin_programs = Program.objects.filter(types_of_assistance__financial=True)
    fin_obligations = ProgramObligation.objects.filter(program__in=fin_programs)

    for fy in FISCAL_YEARS:
        over_programs = fin_obligations.filter(fiscal_year=fy, weighted_delta__gt=0)
        sd = np.std([float(v) for v in over_programs.values_list('weighted_delta', flat=True)])
        avg = np.average([float(v) for v in over_programs.values_list('weighted_delta', flat=True)])
        new_over = over_programs.filter(weighted_delta__lte=str(((3*sd) + avg)))
        sd_new = np.std([float(v) for v in new_over.values_list('weighted_delta', flat=True)])
        avg_new = np.average([float(v) for v in new_over.values_list('weighted_delta', flat=True)])

        outliers = over_programs.filter(weighted_delta__gte=str(avg_new))
        i = 1
        print "Possible CFDA mistakes for FY %s" % fy
        for o in outliers:
            print "%s: %s\t%s\t%s\t%s\t%s" % (i, o.program.program_number, o.program.program_title, o.obligation, o.usaspending_obligation, o.weighted_delta)
            i += 1

        while True:
            input = raw_input("fix an obligation? (enter number of obligation, q to quit, or n to move to the next FY): ")
            if input == 'q':
                sys.exit()

            elif input == 'n':
                break

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
    program.delta = program.usaspending_obligation - program.obligation
    try:
        program.weighted_delta = program.delta / program.obligation
    except Exception:
        if program.obligation == 0:
            if not program.usaspending_obligation:
                program.weighted_delta = 0
            else:
                program.weighted_delta = 1
    program.corrected = True
    program.save()

    correction = ProgramCorrection(program=program.program, program_obligation=program, corrected_obligation=program.obligation, old_obligation=old_obligation, note="Corrected manually in program run",  correction_date=datetime.today())
    correction.save()

if __name__ == '__main__':


    MIN_FY = 2006  # We only want fiscal years over 2006
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, port=MYSQL_PORT)
    cursor = conn.cursor()
    bogus_cfda = open('csv/bogus_cfda_program_numbers', 'w')
    bogus_cfda_writer = csv.writer(bogus_cfda)

    programs = Program.objects.all().order_by('program_number')
    program_data = {}

    usa_query = "SELECT cfda_program_num, fiscal_year, SUM(fed_funding_amount), SUM(face_loan_guran) FROM %s WHERE fiscal_year > %s GROUP BY cfda_program_num, fiscal_year ORDER BY cfda_program_num" % (MYSQL_TABLE_NAME, MIN_FY)
    print usa_query
    print "fetching summary query with rollup of programs, fiscal years and total obligations"
    cursor.execute(usa_query)

    rows = cursor.fetchall()
    
    for row in rows:
        try:    
            program = Program.objects.get(program_number=row[0])

            cfda_obligations = ProgramObligation.objects.filter(program=program, fiscal_year=row[1])
            
            for cfda_ob in cfda_obligations:
                if cfda_ob.type == 1:
                    #its direct spending/grants
                    obligation = row[2]
                else:
                    obligation = row[3]
            
                cfda_ob.usaspending_obligation = obligation

                cfda_ob.delta = (cfda_ob.usaspending_obligation - cfda_ob.obligation)
                try:
                    cfda_ob.weighted_delta = (cfda_ob.delta / cfda_ob.obligation)
                except Exception:
                    if cfda_ob.obligation == 0:
                        if not cfda_ob.usaspending_obligation:
                            cfda_ob.weighted_delta = 0
                        else:
                            cfda_ob.weighted_delta = 1

                cfda_ob.save()

                #print "MATCH: %s - %s - %s - %s diff %s" % (row[0], row[1], cfda_ob.obligation, cfda_ob.usaspending_obligation, cfda_ob.delta)

        except Program.DoesNotExist, e:
            bogus_cfda_writer.writerow([row[0]])

        except ProgramObligation.DoesNotExist, e:
            pass

    cursor.close()
    conn.close()
    
    fix_cfda()


