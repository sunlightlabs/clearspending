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
        re.compile('(?P<year>20[0-9]{2,2})[-.\s\_]{1,1}(?P<month>[0-9]{1,2})[-.\s\_]{1,1}(?P<day>[0-9]{1,2})'),
        re.compile('(?P<year>20[0-9]{2,2})(?P<month>[0-9]{2,2})(?P<day>[0-9]{2,2})'),
        re.compile('(?P<month>[0-9]{2,2})(?P<day>[0-9]{2,2})(?P<year>20[0-9]{2,2})')
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
    try:
        award['award_mod'] = int(line[158:162].strip())
    except ValueError:
        award['award_mod'] = None
    award['fed_amount'] = int(line[162:173])
    award['correction_indicator'] = line[223]

    # for aggregates obligation date is the last day of the quarter
    award['obligation_date'] = date(year=int(line[196:200]), 
                                    month=int(line[200:202]), 
                                    day=int(line[202:204]))

    award['import_date'] = import_date
    award['reporting_lag'] = (award['import_date'] - award['obligation_date']).days
    
    fiscal_year = get_fiscal_year(award['obligation_date'])
    
    award['fiscal_year_lag'] = (import_date - date(year=fiscal_year, 
                                                   month=9, 
                                                   day=30)).days

    award['fiscal_year'] = fiscal_year

    return award


def parse_file(path, import_date, on_bad_line=None):
    transactions = {}

    with file(path) as fil:
        for line in fil:
            if line.strip() == '' or len(line) < 100:
                continue
            
            try:
                t = parse_line(line, import_date)
                ts = transactions.get(t['award_id'])
                if ts is None:
                    transactions[t['award_id']] = [t]
                else:
                    ts.append(t)

            except Exception, ex:
                if not on_bad_line is None:
                    on_bad_line(line)

    first_transactions = []
    for (award_id, ts) in transactions.iteritems():
        ts.sort(key=lambda t: t['award_mod'])
        for t in ts:
            if t['action'] == 'A' and t['correction_indicator'] not in('D', 'C', 'L'):
                first_transactions.append((award_id, t))
                break

    return [(award_id, t) 
            for (award_id, t) in first_transactions
            if t['fed_amount'] > 0]

def find_files_to_process():
    files_from_crawler = list(flattened(recursive_listdir(DOWNLOAD_DIR)))

    files_to_process = []
    files_to_ignore = []
    for path in files_from_crawler:
        try:
            import_date = find_date(path)
            size = os.path.getsize(path)
            files_to_process.append((path, 
                                     import_date,
                                     os.path.getsize(path)))
        except ValueError:
            files_to_ignore.append(path)

    def _import_date((_1, import_date, _2)): return import_date
    def _size((_1, _2, size)): return size
    bytes_accumulator = Accumulator()
    files_to_process.sort(key=_import_date)
    files_to_process = [(f, bytes_accumulator(_size(f)))
                        for f in files_to_process]
    bytes_to_process = bytes_accumulator.getvalue()

    return (bytes_to_process, files_to_process, files_to_ignore)


def parser_main(): 
    (bytes_to_process,
     files_to_process,
     files_to_ignore) = find_files_to_process()

    for path in files_to_ignore:
        print "Unparseable filename: {0}".format(os.path.basename(path))

    print "Files to process: {0}".format(len(files_to_process))
    print "Bytes to process: {0}".format(pretty_bytes(bytes_to_process))
    print "Continue?"
    user_input = raw_input()
    if not 'yes'.startswith(user_input.lower()):
       return

    transactions = {}

    failed_lines = file(os.path.join(DATA_DIR, 'failed_lines.out'), 'w')
    failed_files = file(os.path.join(DATA_DIR, 'failed_files.out'), 'w')
    
    begin_time = time.time()
    for files_processed, ((filepath, import_date, filesize), bytes_processed) in enumerate(files_to_process, start=1):
        try:
            print
            print "Parsing {0}".format(os.path.basename(filepath))
            file_transactions = parse_file(filepath, import_date)
            for (award_id, t) in file_transactions:
                if award_id not in transactions:
                    transactions[award_id] = t

        except UnicodeDecodeError, error:
            log_error(db, filepath, "Unable to parse file: {0}".format(unicode(error)))

        except KeyboardInterrupt:
            break

        now_time = time.time()
        bytes_per_second = bytes_processed / max(now_time - begin_time, 1)
        bytes_processed_pct = bytes_processed * 100 / bytes_to_process
        eta_seconds = (bytes_to_process - bytes_processed) / max(bytes_per_second, 1)
        print "{0}/{1} ({2}%), {3}/s, ETA {4}".format(
            pretty_bytes(bytes_processed),
            pretty_bytes(bytes_to_process),
            bytes_processed_pct,
            pretty_bytes(bytes_per_second),
            pretty_seconds(eta_seconds))

    failed_lines.close()
    failed_files.close()
   
    print "Dumping awards dictionary..."
    with file(os.path.join(DATA_DIR, 'cfda_awards.out.bin'), 'wb') as outf:
        pickle.dump(transactions, outf)


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

