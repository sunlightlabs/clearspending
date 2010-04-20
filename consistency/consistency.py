
#Metric for consistency in USASpending versus CFDA reported obligations

from settings import *
from cfda.models import *
import MySQLdb
import csv
from datetime import datetime

if __name__ == '__main__':

    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE, port=3308)
    cursor = conn.cursor()
    f = open('csv/consistency_report_%s' % datetime.today(), 'w')
    nonfinancial = open('csv/nonfinancial_programs', 'w')
    no_cfda_obligations = open('csv/programs_without_cfda_obligations', 'w')

    data_writer = csv.writer(f)
    nf_writer = csv.writer(nonfinancial)
    no_ob_writer = csv.writer(no_cfda_obligations)

    programs = Program.objects.all()
    program_data = {}

    for p in programs:

        obligations = ProgramObligation.objects.filter(program=p)
        financial = False
        for assistance in  p.types_of_assistance.all():
            if assistance.financial: 
                financial = True

        if financial: 
            if len(obligations) > 0:
                sql = "SELECT fiscal_year, SUM(fed_funding_amount) FROM %s WHERE cfda_program_num=%s GROUP BY fiscal_year ORDER BY fiscal_year" % (MYSQL_TABLE_NAME, p.program_number)

                print "Executing query on %s-%s\n" % (p.program_number, p.program_title)
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                for ob in obligations:

                    usa_obligation = 0  #base case for no records in USASpending
            
                    for row in rows:
                        if row[0] == ob.fiscal_year:
                            usa_obligation = row[1]

                    delta = ob.obligation - usa_obligation
                    data = (ob.fiscal_year, ob.obligation, usa_obligation, delta)
                    
                    try:
                        program_data[p.program_number].append(data)

                    except Exception, e:
                        #key doesn't exist yet
                        program_data[p.program_number] = [data]
                    
                    data_writer.writerow(data)
                    print data
                    
            else:
                no_ob_writer.writerow((p.program_number, p.program_title))
        else:
            nf_writer.writerow((p.program_number, p.program_title))

    cursor.close()
    conn.close()  

    data_writer.close()
    nf_writer.close()
    no_ob_writer.close()
         

