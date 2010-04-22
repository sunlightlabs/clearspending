
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
import MySQLdb
import csv
from datetime import datetime

if __name__ == '__main__':

    MIN_FY = 2006  # We only want fiscal years over 2006
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, port=MYSQL_PORT)
    cursor = conn.cursor()
    bogus_cfda = open('csv/bogus_cfda_program_numbers', 'w')
    bogus_cfda_writer = csv.writer(bogus_cfda)

    programs = Program.objects.all().order_by('program_number')
    program_data = {}

    usa_query = "SELECT cfda_program_num, fiscal_year, SUM(fed_funding_amount) FROM %s WHERE fiscal_year > %s GROUP BY cfda_program_num, fiscal_year ORDER BY cfda_program_num" % (MYSQL_TABLE_NAME, MIN_FY)
    print usa_query
    print "fetching summary query with rollup of programs, fiscal years and total obligations"
    cursor.execute(usa_query)

    rows = cursor.fetchall()
    
    for row in rows:
        try:    
            program = Program.objects.get(program_number=row[0])
            cfda_ob = ProgramObligation.objects.get(program=program, fiscal_year=row[1])
            cfda_ob.usaspending_obligation = row[2]
            cfda_ob.delta = (cfda_ob.obligation - cfda_ob.usaspending_obligation)
            cfda_ob.save()

            print "MATCH: %s - %s - %s - %s diff %s" % (row[0], row[1], cfda_ob.obligation, cfda_ob.usaspending_obligation, cfda_ob.delta)

        except Program.DoesNotExist, e:
            bogus_cfda_writer.writerow([row[0]])

        except ProgramObligation.DoesNotExist, e:
            pass

    cursor.close()
    conn.close()  

         

