"""Defines the format for agency submission files to USASpending, along with
a lazy record parser."""

import sys
import re
import hashlib
from datetime import date
from functools import partial
from utils import Accumulator


class FAADSPlusFormat(object):
    # Based on table from memo m09-19 pages 14-15, which defines the 
    # agency submission record format
    FIELDS = [
        ('CFDA Program Number', 'cfda', 7),
        ('State Application Identifier (SAI Number)', 'sai', 20),
        ('Recipient Name', 'recipient_name', 45),
        ('Recipient City Code', 'recipient_city_code', 5),
        ('Recipient City Name', 'recipient_city_name', 21),
        ('Recipient County Code', 'recipient_county_code', 3),
        ('Recipient County Name', 'recipient_county_name', 21),
        ('Recipient State Code', 'recipient_state_code', 2),
        ('Recipient Zip Code', 'recipient_zip_code', 9),
        ('Type of Recipient', 'recipient_type', 2),
        ('Type of Action', 'action_type', 1),
        ('Recipient Congressional District', 'recipient_cd', 2),
        ('Federal Agency/Organizational Unit Code', 'agency_code', 4),
        ('Federal Award Identifier Number (FAIN)', 'award_id', 16),
        ('Federal Award Identifier Number (Modification)', 'award_mod', 4),
        ('Federal Funding Sign', 'fed_funding_sign', 1),
        ('Federal Funding Amount', 'fed_funding_amount', 10),
        ('Non-Federal Funding Sign', 'nonfed_funding_sign', 1),
        ('Non-Federal Funding Amount', 'nonfed_funding_amount', 10),
        ('Total Funding Sign', 'funding_sign', 1),
        ('Total Funding Amount', 'funding_amount', 11),
        ('Obligation/Action Date', 'obligation_action_date', 8),
        ('Starting Date', 'obligation_start_date', 8),
        ('Ending Date', 'obligation_end_date', 8),
        ('Type of Assistance Transaction', 'assistance_type', 2),
        ('Record Type', 'record_type', 1),
        ('Correction/Late Indicator', 'correction_indicator', 1),
        ('Fiscal Year and Quarter Correction', 'fyq_correction', 5),
        ('Principal Place of Performance Code', 'ppop_code', 7),
        ('Principal Place of Performance (State)', 'ppop_state', 25),
        ('Principal Place of Performance (County or City)', 'ppop_county_or_city', 25),
        ('Principal Place of Performance Zip Code', 'ppop_zip_code', 9),
        ('Principal Place of Performance Congressional District', 'ppop_cd', 2),
        ('CFDA Program Title', 'cfda_title', 74),
        ('Federal Agency Name', 'agency_name', 72),
        ('State Name', 'state_name', 25),
        ('Project Description', 'project_description', 149),
        ('DUNS Number', 'duns', 9),
        ('DUNS Number PLUS 4', 'duns_plus_4', 4),
        ('Dun & Bradstreet Confidence Code', 'duns_conf_code', 2),
        ('Program Source/Treasury Account Symbol: Agency Code', 'program_source_agency_code', 2),
        ('Program Source/Treasury Account Symbol: Account Code', 'program_source_account_code', 4),
        ('Program Source/Treasury Account Symbol: Account Code (OPTIONAL)', 'program_source_account_code_opt', 3),
        ('Recipient Address Line 1', 'recipient_address1', 35),
        ('Recipient Address Line 2', 'recipient_address2', 35),
        ('Recipient Address Line 3', 'recipient_address3', 35),
        ('Face Value of Direct Loan/Load Guarantee', 'loan_face_value', 16),
        ('Original Subsidy Cost of the Direct Loan/Loan Guarantee', 'orig_loan_subsidy_cost', 16),
        ('Business Funds Indicator (BFI)', 'bfi', 3),
        ('Recipient Country Code', 'recipient_country_code', 3),
        ('Principal Place of Performance Country Code', 'ppop_country_code', 3),
        ('Unique Record Identifier', 'uri', 70)
    ]

    offset_accumulator = Accumulator()
    FIELDS_BY_ABBREV = dict([(abbrev, (abbrev, offset_accumulator(length), length, desc)) 
                            for (desc, abbrev, length) in FIELDS])

    class Record(object):
        def __init__(self, text):
            self.__text = text
            self.__hash = None

        def __getitem__(self, key):
            field = FAADSPlusFormat.FIELDS_BY_ABBREV.get(key)
            if field is None:
                raise KeyError(key)
            (abbrev, offset, length, desc) = field
            return self.__text[offset:offset+length]

        @property
        def id(self):
            uri = self['uri'].strip()
            if len(uri) > 0:
                return uri
            return (self['award_id'] + self['award_mod']).strip()

        @property
        def fed_funding_value(self):
            text = self['fed_funding_sign'] + self['fed_funding_amount']
            return int(text.strip())

        @property
        def nonfed_funding_value(self):
            text = self['nonfed_funding_sign'] + self['nonfed_funding_amount']
            return int(text.strip())

        @property
        def total_funding_value(self):
            text = self['total_funding_sign'] + self['total_funding_amount']
            return int(text.strip())

        @property
        def hash(self):
            if self.__hash:
                return self.__hash
            else:
                hasher = hashlib.md5()
                for field in FAADSPlusFormat.FIELDS_BY_ABBREV:
                    hasher.update(self[field])
                self.__hash = hasher.hexdigest()
                return self.__hash

        def as_dict(self):
            return dict(((k, self[k]) for k in FAADSPlusFormat.FIELDS_BY_ABBREV))

    @staticmethod
    def slurp(path):
        with file(path) as fil:
            return [FAADSPlusFormat.Record(ln) for ln in fil]

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

def main():
    fields = map(lambda (_1, abbrev, _2): abbrev, 
                 FAADSPlusFormat.FIELDS)
    def quotestr(s):
        return '"{0}"'.format(s)

    print ",".join(map(quotestr, ["import_date"] + fields))
    for path in sys.argv[1:]:
        try:
            import_date = find_date(path).strftime("%Y-%m-%d")
        except ValueError:
            print >>sys.stderr, "Unparseable path: {0}".format(path)
            continue

        try:
            with file(path) as fil:
                for line in fil:
                    record = FAADSPlusFormat.Record(line)
                    values = ([import_date] 
                              + map(record.__getitem__, fields))
                    print ",".join(map(quotestr, values))
        except IOError, err:
            print >>sys.stderr, "Unable to parse file: {0}".format(path)
            print >>sys.stderr, str(err)
            continue

if __name__ == "__main__":
    main()

