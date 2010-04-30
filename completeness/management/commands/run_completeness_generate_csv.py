from django.core.management.base import NoArgsCommand
import MySQLdb
from settings import *

def generate_csvs(num_pages=None):
    """ Creates the chunked CSV files that will be fed into the script """
    conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD, db=MYSQL_DATABASE)
    cursor = conn.cursor()

    sql = "SELECT %s FROM %s WHERE (%s) ORDER BY record_id ASC" % (','.join(CANONICAL_FIELD_ORDER), MYSQL_TABLE_NAME, MYSQL_WHERE_CLAUSE)
    cursor.execute(sql.replace("\n", " "))

    n = 0
    p = 0
    while True:
        row = cursor.fetchone()
        if row is None:
            break

        if (n % ROWS_PER_CYCLE) == 0:
            if type(f) is file and not f.closed:
                f.close()

                # quit at this point, if we're only emitting a set number of files
                p += 1
                if num_pages is not None and p>=num_pages:
                    break

            f = open('completeness/csv/%d-%d.csv' % (n, (n + ROWS_PER_CYCLE)), 'w')
            writer = csv.writer(f)
    
        writer.writerow(row)

        n += 1

    f.close()

    cursor.close()
    conn.close()

class Command(NoArgsCommand):
    help = "Generates CSVs"

    def handle_noargs(self, **options):       
        generate_csvs(num_pages=1)
                
            
                
