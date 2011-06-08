from django.core.management.base import NoArgsCommand
#import MySQLdb
import pgdb
from settings import *
import csv

def generate_csvs(num_pages=None):
    """ Creates the chunked CSV files that will be fed into the script """
    conn = pgdb.connect(host=PG_HOST, user=PG_USER, password=PG_PASSWORD, database=PG_DATABASE)#, dbport=PG_PORT)


    for fy in FISCAL_YEARS:
        print "Gettings query for %s" % fy
        sql = "SELECT %s FROM %s WHERE (fiscal_year=%s) ORDER BY id ASC" % (','.join(CANONICAL_FIELD_ORDER), PG_TABLE_NAME, fy)
        cursor = conn.cursor()
        cursor.execute(sql)
        print "Got Query Results, starting iteration...."
        f = open('completeness/csv/%d.csv' % (fy), 'w')
        writer = csv.writer(f)
        n = 0
        p = 0
        while True:
            row = cursor.fetchone()
            print "got one row"
            if row is None:
                break
            
#            if (n % ROWS_PER_CYCLE) == 0:
 #               print "mod is 0"
  #              if type(f) is file and not f.closed:
   #                 print "closing file"
    #                f.close()

                    # quit at this point, if we're only emitting a set number of files
     #               p += 1
#                    if num_pages is not None and p>=num_pages:
 
#break
      #          print "opening file"
       #         f = open('completeness/csv/%d-%d.csv' % (n, (n + ROWS_PER_CYCLE)), 'w')
        #        writer = csv.writer(f)
             
            writer.writerow(row)

            n += 1

        f.close()


class Command(NoArgsCommand):
    help = "Generates CSVs"

    def handle_noargs(self, **options):       
        generate_csvs(num_pages=1)
                
            
                
