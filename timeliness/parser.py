"""Parses text files downloaded by timeliness.crawler and
stores the pickled results for the analysis stage."""

import re
import os
import sys
import time
import cPickle as pickle
from datetime import date, datetime
from utils import flattened, recursive_listdir, pretty_bytes, pretty_seconds, Accumulator
from timeliness import (DATA_DIR, DOWNLOAD_DIR, FISCAL_YEARS)


RE_CFDA = re.compile('^[0-9]{2,2}.[0-9]{3,3}$')
                


class InvalidCFDAProgramNumber(ValueError):
    def __init__(self, *args, **kwargs):
        self.program_number = kwargs.pop('program_number', None)
        super(InvalidCFDAProgramNumber, self).__init__(*args, **kwargs)

class UnparseableFile(Exception):
    def __init__(self, *args, **kwargs):
        self.path = kwargs.pop('path', None)
        super(UnparseableFile, self).__init__(*args, **kwargs)

def get_fiscal_year(d):        
    if d.month < 10:
        return d.year
    else:
        return d.year + 1
        

def find_date(haystack):
    patterns = [
        re.compile('(?P<year>20[0-9]{2,2})[.\s\_]{1,1}(?P<month>[0-9]{1,2})[.\s\_]{1,1}(?P<day>[0-9]{1,2})'),
        re.compile('(?P<year>20[0-9]{2,2})(?P<month>[0-9]{2,2})(?P<day>[0-9]{2,2})')
    ]
    for p in patterns:
        m = p.search(haystack)
        if m:
            return date(year=int(m.group('year')),
                        month=int(m.group('month')),
                        day=int(m.group('day')))

    raise ValueError("{0} does not contain a date string.".format(haystack))


def parse_line(line, import_date):
    award = {}
    award['cfda'] = line[0:7].strip()
    if not RE_CFDA.match(award['cfda']):
        raise InvalidCFDAProgramNumber(award['cfda'])

    award['action'] = line[135]
    award['award_id'] = line[142:158].strip()
    award['fed_amount'] = int(line[163:173])
    
    # for aggregates obligation date is the last day of the quarter
    award['obligation_date'] = date(year=int(line[196:200]), 
                                    month=int(line[200:202]), 
                                    day=int(line[202:204]))
    award['import_date'] = import_date
    award['reporting_lag'] = (award['import_date'] - award['obligation_date']).days
    
    fiscal_year = get_fiscal_year(award['obligation_date'])
    
    award['fiscal_year_lag'] = (award['import_date'] - date(year=fiscal_year, 
                                                            month=9, 
                                                            day=30)).days

    award['fiscal_year'] = fiscal_year

    return award


def store_award(awards, award):
    """Checks for duplicate reporting for the same award ID,
    discarding the newer report."""

    is_duplicate = False

    # only process new transactions
    if award['action'] == 'A':
        # check for past transactions with same award_id
        if award['award_id'] in awards:
            other_award = awards[award['award_id']]

            if other_award['cfda'] == award['cfda']:
                is_duplicate = True
            
                #check if new transaction was reported first
                if award['import_date'] < other_award['import_date']:
                    # keep earliest reported transaction
                    awards[award['award_id']] = award
        else:
            awards[award['award_id']] = award

    return is_duplicate


def parser_main():
    awards = {}

    failed_lines = file(os.path.join(DATA_DIR, 'failed_lines.out'), 'w')
    failed_files = file(os.path.join(DATA_DIR, 'failed_files.out'), 'w')
    
    duplicates = 0
    bad_records = 0
    bad_filenames = 0
    
    # Sort files by filename. This should cause the Shove cache's
    # hit rate to increase since the filenames are prefixed with the
    # agency name and we don't expect two agencies to report for the 
    # same award_id value.

    files_to_process = sorted(flattened(recursive_listdir(DOWNLOAD_DIR)), 
                              key=os.path.basename)

    bytes_accumulator = Accumulator()
    files_to_process = [(path, os.path.getsize(path), bytes_accumulator(os.path.getsize(path)))
                        for path in files_to_process]
    bytes_to_process = bytes_accumulator.getvalue()

    print "Files to process: {0}".format(len(files_to_process))
    print "Bytes to process: {0}".format(pretty_bytes(bytes_to_process))
    print "Continue?"
    user_input = raw_input()
    if not 'yes'.startswith(user_input.lower()):
       return

    begin_time = time.time()
    for files_processed, (filepath, filebytes, bytes_processed) in enumerate(files_to_process, start=0):
        filename = os.path.basename(filepath)

        try:
            try:
                import_date = find_date(filename)
            except (ValueError, ImportError), err:
                bad_filenames += 1
                continue

            with file(filepath) as fil:
                for line_number, line in enumerate(fil): 
                    if line.strip() == '' or len(line) < 100:
                        continue
                    
                    try:
                        award = parse_line(line, import_date)
                        is_duplicate = store_award(awards, award)
                        duplicates += 1

                    except Exception, ex:
                        bad_records += 1
                        failed_lines.write(line)

                    if line_number % 100 == 0:
                        sys.stdout.write(".")
                        sys.stdout.flush()

        except UnparseableFile, nonparse:
            failed_files.write('%s\n' % filepath)
            print
            print "Skipping {0} because {1}".format(filename, unicode(nonparse))

        except UnicodeDecodeError, error:
            log_error(db, filepath, "Unable to parse file: {0}".format(unicode(error)))

        except KeyboardInterrupt:
            break

        now_time = time.time()
        bytes_per_second = bytes_processed / max(now_time - begin_time, 1)
        bytes_processed_pct = bytes_processed * 100 / bytes_to_process
        eta_seconds = (bytes_to_process - bytes_processed) / bytes_per_second
        print
        print "{0}/{1} ({2}%), {3}/s, ETA {4}".format(
            pretty_bytes(bytes_processed),
            pretty_bytes(bytes_to_process),
            bytes_processed_pct,
            pretty_bytes(bytes_per_second),
            pretty_seconds(eta_seconds))

    print 'bad filenames: %d' % bad_filenames
    print 'files processed: %d' % files_processed  
    print 'bad records: %d' % bad_records
    print 'good records: %d' % len(awards)

    failed_lines.close()
    failed_files.close()
   
    print "Dumping awards dictionary..."
    with file(os.path.join(DATA_DIR, 'cfda_awards.out.bin'), 'wb') as outf:
        pickle.dump(awards, outf)


def fix_prefix(prefix):
    for stem in ['VA', 'DHS', 'HUD', 'USAID', 'DOJ', 'USTREAS', 'DOE', 'DOI', 'IMLS', 'DOC']:
        if prefix.startswith(stem):
            return stem
    return prefix


def show_prefixes():
    def filename_has_date(filename):
        try:
            import_date = find_date(filename)
            return True
        except (ValueError, ImportError), err:
            return False

    re_agency = re.compile('^[0-9]*[A-Z]+')
    def extract_prefix(filename):
        prefix_match = re_agency.match(filename.upper())
        if not prefix_match is None:
            prefix = prefix_match.group()
            return fix_prefix(prefix)
        else:
            return None

    files_to_process = filter(filename_has_date, map(os.path.basename, flattened(recursive_listdir(DOWNLOAD_DIR))))
    prefixes = map(extract_prefix, files_to_process)

    def unique(iterable):
        def combine(accum, item):
            accum[item] = None
            return accum
        return reduce(combine, iterable, {}).keys()

    def frequency(iterable):
        def combine(frequencies, item):
            cnt = frequencies.get(item, 0)
            frequencies[item] = cnt + 1
            return frequencies
        return reduce(combine, iterable, {})

    def print_freq(freq, indent=""):
        def value((k, v)):
            return v
        for s, f in sorted(freq.iteritems()):
            print "{0}{1!s:15}: {2!s:>7}".format(indent, s, f)

    print_freq(frequency(prefixes))



if __name__ == "__main__":
    parser_main()

