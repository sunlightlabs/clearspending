
from django.db import models
import csv
import re
import sys
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from itertools import izip
from operator import itemgetter

import django.db.models
from django.utils.encoding import smart_unicode
from decimal import DivisionByZero
from math import fabs
from helpers.unicode import decode_string
from utils import chunk_list, freq, grouped
from datetime import datetime
from django.conf import settings


class MySqlTextField(models.TextField):
    def db_type(self, connection):
        return 'text'

class Agency(models.Model):
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']
        
    code = models.IntegerField(primary_key=True, blank=False, null=False)
    name = models.TextField("Federal Agency", blank=True, default="")
    description = models.TextField("Description", blank=True, default="")
    caveat = models.TextField("Caveats associated with the spending in this agency", blank=True, null=True)
     
class AssistanceTypeManager(models.Manager):

    def generate(self):

        for i in range(1, len(AssistanceType.CODE_OPTIONS)+1):
            try:
                at = AssistanceType.objects.get(code=i)
            except AssistanceType.DoesNotExist:
                at = AssistanceType(code=i)

            if i < 8:
                at.financial = True
            else:
                at.financial = False

            at.save()

class AssistanceType(models.Model):
    def __unicode__(self):
        return "%s" % self.code
    
    class Meta:
        verbose_name = 'Assistance Type'
    
    # CODE_OPTIONS corresponds to the types defined here:
    # https://www.cfda.gov/?static=assistance&s=generalinfo&mode=list&tab=list&tabmode=list
    CODE_OPTIONS = (
        (1, "Formula Grants", "Formula Grants (Cooperative Agreements)"),
        (2, "Project Grants",
            "Project Grants (Discretionary)",
            "Project Grants (For Specified Projects)",
            "Project Grants (Cooperative Agreements)", "Project Grants (Contracts)",
            "Project Grants (Special)", "Project Grants (Fellowships)",
            "Project Grants (Cooperative Agreements or Contracts)",
            "Project Grants (Including Individual Awards)"),
        (3, "Direct Payments for Specified Use", "Direct Payments for a Specified Use",
            "Direct Payments for Specified Use (Cooperative Agreements)",
            "Direct Payments for Specified Use(Cooperative Agreements)"),
        (4, "Direct Payments with Unrestricted Use"),
        (5, "Direct Loans"),
        (6, "Guaranteed/Insured Loans", "Loan Guarantees/Grants"),
        (7, "Insurance"),
        (8, "Sale, Exchange, or Donation of Property and Goods", 
            "Sale, Exchange, or Donation of Property or Goods"),
        (9, "Use of Property, Facilities, and Equipment"),
        (10, "Provision of Specialized Services"),
        (11, "Advisory Services and Counseling"),
        (12, "Dissemination of Technical Information", "Information"),
        (13, "Training"),
        (14, "Investigation of Complaints", "Resolution of Disputes"),
        (15, "Federal Employment"),
        (16, "Cooperative Agreements", "Cooperative Agreements (Discretionary Grants)"),
    )

    code = models.IntegerField("Numeric Code", max_length=2, blank=False)
    financial = models.BooleanField(default=True)
    objects = AssistanceTypeManager()

class ProgramObligation(models.Model):

    program = models.ForeignKey('Program', blank=False, null=False)
    fiscal_year = models.IntegerField(blank=False, null=False)
    obligation = models.DecimalField(max_digits=27, decimal_places=2, blank=False, null=False)
    usaspending_obligation = models.DecimalField(max_digits=27, decimal_places=2, blank=True, null=True)
    delta = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    weighted_delta = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    cfda_edition = models.IntegerField(blank=False, null=False)
    corrected = models.BooleanField(default=False)

    TYPE_CHOICES = (
        (1, 'Grants'),
        (2, 'Loans'),
        (3, 'Loan Guarantees'),
        (4, 'Insurance')
    )

    #for simplicity's sake this has been collapsed in the actual processing, grants=1 everything else=2
    obligation_type = models.IntegerField(max_length=1, choices=TYPE_CHOICES, null=True)
    GRADE_CHOICES = (
        ('p', 'Pass'),
        ('o', 'Overreporting Obligations'),
        ('u', 'Underreporting Obligations'),
        ('n', 'Not reporting Obligations'),
        ('t', 'Late reporting'),
        ('c', 'Incomplete reporting')
    )
    grade = models.TextField(choices=GRADE_CHOICES)

    def save(self, *args, **kwargs):
        self._update_deltas()
        super(ProgramObligation, self).save(*args, **kwargs)

    def _update_deltas(self):
        self.delta = (self.usaspending_obligation or 0) - (self.obligation or 0)
        try:
            self.weighted_delta = float(self.delta) / float(self.obligation)
        except (ZeroDivisionError, DivisionByZero):
            if fabs(self.delta) > 0:
                self.weighted_delta = float(1.0)
            else:
                self.weighted_delta = float(0.0)
        except Exception, e:
            fmt = u"Exception while calculating delta for program {0} FY {1}: {2}"
            print fmt.format(self.program.program_number,
                             self.fiscal_year,
                             unicode(e))
            self.weighted_delta = float(0.0)
        except:
            fmt = u"Exception while calculating delta for program {0} FY {1}"
            print fmt.format(self.program.program_number,
                             self.fiscal_year)
        self.weighted_delta = str(self.weighted_delta)

class ProgramAccount(models.Model):

    account_number = models.CharField(max_length=255, blank=False, null=False, primary_key=True)


class Program(models.Model):

    def __unicode__(self):
        return "%s %s" % (self.program_number, self.program_title)

    program_number = models.CharField("Program number", max_length=7)
    program_title = MySqlTextField("Program title", max_length=255)
    federal_agency = MySqlTextField("Federal agency",
                                    max_length=64000,
                                    blank=True,
                                    default="")
    agency = models.ForeignKey('Agency', blank=True, null=True)
    authorization = MySqlTextField("Authorization",
                                   max_length=64000,
                                   blank=True,
                                   default="")
    objectives = MySqlTextField("Objectives",
                                max_length=64000,
                                blank=True,
                                default="")
    types_of_assistance = models.ManyToManyField(AssistanceType)
    uses_and_use_restrictions = MySqlTextField("Uses and use restrictions",
                                               max_length=64000,
                                               blank=True,
                                               default="")
    applicant_eligibility = MySqlTextField("Applicant eligibility",
                                           max_length=64000,
                                           blank=True,
                                           default="")
    beneficiary_eligibility = MySqlTextField("Beneficiary eligibility",
                                             max_length=64000,
                                             blank=True,
                                             default="")
    credentials_documentation = MySqlTextField("Credentials / documentation",
                                               max_length=64000,
                                               blank=True,
                                               default="")
    preapplication_coordination = MySqlTextField("Preapplication coordination",
                                                 max_length=64000,
                                                 blank=True,
                                                 default="")
    application_procedure = MySqlTextField("Application procedure",
                                           max_length=64000,
                                           blank=True,
                                           default="")
    award_procedure = MySqlTextField("Award procedure",
                                     max_length=64000,
                                     blank=True,
                                     default="")
    deadlines = MySqlTextField("Deadlines",
                               max_length=64000,
                               blank=True,
                               default="")
    range_of_approval_disapproval_time = MySqlTextField("Range of approval / disapproval time",
                                                        max_length=64000,
                                                        blank=True,
                                                        default="")
    appeals = MySqlTextField("Appeals",
                             max_length=64000,
                             blank=True,
                             default="")
    renewals = MySqlTextField("Renewals",
                              max_length=64000,
                              blank=True,
                              default="")
    formula_and_matching_requirements = MySqlTextField("Formula and matching requirements",
                                                       max_length=64000,
                                                       blank=True,
                                                       default="")
    length_and_time_phasing_of_assistance = MySqlTextField("Length and time phasing of assistance",
                                                           max_length=64000,
                                                           blank=True,
                                                           default="")
    reports = MySqlTextField("Reports",
                             max_length=64000,
                             blank=True,
                             default="")
    audits = MySqlTextField("Audits",
                            max_length=64000,
                            blank=True,
                            default="")
    records = MySqlTextField("Records",
                             max_length=64000,
                             blank=True,
                             default="")
    account_identification = models.ManyToManyField(ProgramAccount)
    range_and_average_of_financial_assistance = MySqlTextField("Range and average of financial assistance",
                                                               max_length=64000,
                                                               blank=True,
                                                               default="")
    program_accomplishments = MySqlTextField("Program accomplishments",
                                             max_length=64000,
                                             blank=True,
                                             default="")
    regulations_guidelines_and_literature = MySqlTextField("Regulations guidelines and literature",
                                                           max_length=64000,
                                                           blank=True,
                                                           default="")
    regional_or_local_office = MySqlTextField("Regional or local office",
                                              max_length=64000,
                                              blank=True,
                                              default="")
    headquarters_office = MySqlTextField("Headquarters office",
                                         max_length=64000,
                                         blank=True,
                                         default="")
    web_site_address = MySqlTextField("Web site address",
                                      max_length=64000,
                                      blank=True,
                                      default="")
    related_programs = MySqlTextField("Related programs",
                                      max_length=64000,
                                      blank=True,
                                      default="")
    examples_of_funded_projects = MySqlTextField("Examples of funded projects",
                                                 max_length=64000,
                                                 blank=True,
                                                 default="")
    criteria_for_selecting_proposals = MySqlTextField("Criteria for selecting proposals",
                                                      max_length=64000,
                                                      blank=True,
                                                      default="")
    published_date = MySqlTextField("Published Date",
                                    max_length=64000,
                                    blank=True,
                                    default="")
    parent_shortname = MySqlTextField("Parent Shortname",
                                      max_length=64000,
                                      blank=True,
                                      default="")
    url = MySqlTextField("URL on CFDA website",
                         max_length=64000,
                         blank=True,
                         default="")
    recovery = models.BooleanField(default=False)

    cfda_edition = models.IntegerField("CFDA Edition", blank=True, null=True)
    load_date = models.DateTimeField("Load Date", auto_now=True)    
    caveat = MySqlTextField("Caveats about the spending of this program",
                            max_length=64000,
                            blank=True,
                            null=True)


def guess_obligation_type(program_assistance_types, assistance_type_text):
    re_loan = re.compile('loan', re.I)
    re_guar = re.compile('guarantee', re.I)
    re_insur = re.compile('insur', re.I)
    re_grants = re.compile('((formula|project|flex|incentive) )?grants', re.I)

    if len(re_guar.findall(assistance_type_text)) > 0:
        return 2

    if len(re_loan.findall(assistance_type_text)) > 0:
        return 2

    if len(re_insur.findall(assistance_type_text)) > 0:
        return 1

    if len(re_grants.findall(assistance_type_text)) > 0:
        return 1

    if len(set(program_assistance_types) & set([5,6,7])) > 0:
        return 2

    # print >>sys.stderr, "Defaulting to obligation type GRANTS for assistance type {0} for program {1}".format(asst_type, self.program.program_number)
    return 1

IGNORED_ASSISTANCE_TYPES = [u'salaries',
                            u'training',
                            u'contracts and interagency agreements',
                            u'provision of specialized services',
                            u'sales',
                            u'sale, exchange, or donation or property']
RE_IGNORED_ASSISTANCE_TYPES = re.compile(u'|'.join(IGNORED_ASSISTANCE_TYPES), re.I)
def parse_obligations(program_assistance_types, obligations_text):
    """ Parses obligations text into a list of tuples:
            (asst_type, fiscal_year, amount)

            asst_type: 'Direct Loans' | 'Loan Guarantees' | 'Formula Grants' | etc
            fiscal_year: int
            amount: int
            
        If the text contains duplications of (asst_type, fiscal_year) then all such
        tuples are combined by summing the amounts.
    """
    re_funding = re.compile('FY ((?:20)?[\d]{2})( est. | est | )[\$]([0-9,]+)')
#    re_funding_type = re.compile('\((.*?(?:\(.*?\))?)\)')
    re_funding_type = re.compile(ur'\((.*?)[ ]?(?:\(.*?\))?\)')
    funding_matches = re_funding.findall(obligations_text)
    type_matches = re_funding_type.findall(obligations_text)
    matches = [(int('20' + fy),
                int(amt.replace(',', '')))
               for (fy, _est, amt) in funding_matches]
    chunked_matches = list(chunk_list(matches,
                                      # Break when fiscal year doesn't increase
                                      lambda prev, curr: curr[0] <= prev[0]))
    flat_obligations = [(asst_type, fy, amt)
                        for (asst_type, obs) in izip(type_matches,
                                                     chunked_matches)
                        for (fy, amt) in obs
                        if RE_IGNORED_ASSISTANCE_TYPES.search(asst_type) is None]

    """ Map the assistance types to obligation types """
    flat_obligations1 = [(guess_obligation_type(program_assistance_types,
                                                asst_type),
                          fy,
                          amt)
                         for (asst_type, fy, amt) in flat_obligations]


    """ We've flattened the list of obligations to:
            [(obligation_type, fy, amt) ...]
        but there will be duplicates for (obligation_type, fy) pairs so we need
        to sum those values. """
    asst_type_fy_groups = grouped(flat_obligations1,
                                  key=lambda (ob_type, fy, amt): (ob_type, fy))

    def add_amounts(a, b):
        (a_type, a_year, a_amount) = a
        (b_type, b_year, b_amount) = b
        return (a_type, a_year, a_amount + b_amount)
    def sum_amounts(obs):
        return reduce(add_amounts, obs)
    parsed_obligations = [sum_amounts(grp)
                          for grp in asst_type_fy_groups]

    return parsed_obligations


class ProgramManager(models.Manager):
    
    FIELD_MAPPINGS = [
        'program_title',
        'program_number',
        'popular_name',
        'federal_agency',
        'authorization',
        'objectives',
        'types_of_assistance',
        'uses_and_use_restrictions',
        'applicant_eligibility',
        'beneficiary_eligibility',
        'credentials_documentation',
        'preapplication_coordination',
        'application_procedure',    
        'award_procedure',
        'deadlines',
        'range_of_approval_disapproval_time',
        'appeals',
        'renewals',
        'formula_and_matching_requirements',
        'length_and_time_phasing_of_assistance',
        'reports',
        'audits',
        'records',
        'account_identification',
        'obligations',
        'range_and_average_of_financial_assistance',
        'program_accomplishments',
        'regulations_guidelines_and_literature',
        'regional_or_local_office',
        'headquarters_office',
        'web_site_address',
        'related_programs',
        'examples_of_funded_projects',
        'criteria_for_selecting_proposals',
        'published_date',
        'parent_shortname',
        'url',
        'recovery'
    ]


    def __init__(self):
        self.programs = {}

    def import_programs_file(self, filepath):
        this_edition = int(filepath[-9:-4]) #pull the date off of the programs csv file
        with file(filepath) as inf:
            rdr = csv.DictReader(inf, fieldnames=self.FIELD_MAPPINGS)
            rdr.next() # Eat the header row -- we're supplying our own names
            for row in rdr:
                if not row:
                    continue
                if len(row) < 10:
                    continue

                program_number = row['program_number'].strip()
                row['program_number'] = program_number
                row['cfda_edition'] = this_edition

                previous_row = self.programs.get(program_number)
                if previous_row is None or previous_row['cfda_edition'] <= this_edition:
                    """This builds a list of the obligations value for each file read
                    paired with the CFDA version number for that file. This list will
                    be reconciled later.
                    """
                    previous_obligations = (previous_row['obligations']
                                            if previous_row is not None
                                            else [])
                    row['obligations'] = ([(row['cfda_edition'], row['obligations'])]
                                          + previous_obligations)

                    """Accumulate a list of account_identification fields.."""
                    previous_accounts = (previous_row['account_identification']
                                         if previous_row is not None
                                         else [])
                    row['account_identification'] = ([row['account_identification']]
                                                     + previous_accounts)

                    self.programs[program_number] = row

    def _decode_strings(self):
        for (program_number, row) in self.programs.iteritems():
            for (k, v) in row.items():
                if isinstance(v, (str, bytes)):
                    row[k] = decode_string(v)

    def _parse_fields(self):
        valid_assistance_types = dict(((name.upper(), t[0])
                                       for t in AssistanceType.CODE_OPTIONS
                                       for name in t[1:]))

        re_account = re.compile('[\d]{2}[-][\d]{4}[-][\d]{1}[-][\d]{1}[-][\d]{3}')

        for (program_number, row) in self.programs.iteritems():
            """ Parses a list of valid assistance types from those observed
                in the 'types_of_assistance' field. The result is a list
                of strings. """
            re_asst_type = re.compile(ur'^(.*?)(?: \(.*\))?$')
            if isinstance(row['types_of_assistance'], unicode):
                assistance_types = set([base_type.strip().upper()
                                        for t in row['types_of_assistance'].strip('.').split(';')
                                        for base_type in re_asst_type.findall(t.replace('\n', ' ').strip())
                                        if t and base_type])
                retained_assistance_types = set([code
                                                 for code in (valid_assistance_types.get(name)
                                                              for name in assistance_types)
                                                 if code is not None])
                if len(retained_assistance_types) == 0:
                    fmt = "No valid assistance types in {0} for {prog} from CFDA {ver}"
                    print >>sys.stderr, fmt.format(list(assistance_types),
                                                   prog=row['program_number'],
                                                   ver=row['cfda_edition'])
                row['parsed_types_of_assistance'] = list(retained_assistance_types)

            """ Parses obligations from the obligations text, reduces down to the most
                recently published values for each fiscal year. """
            flattened_obligations = [] # a flat list of all obligations from all cfda files
            for (cfda, obligations_text) in sorted(row['obligations'], key=itemgetter(0)):
                obligations = parse_obligations(row['parsed_types_of_assistance'],
                                                obligations_text)
                versioned_obligations = [(cfda, ob_type, fy, amt)
                                         for (ob_type, fy, amt) in obligations]
                flattened_obligations.extend(versioned_obligations)

            """ Flatten the list to facilitate sorting, which in turn ensures that
                later cfda versions overrite preceding ones when dictified. """
            flattened_obligations.sort(key=itemgetter(0))
            """ Here we get a dictionary mapping:
                    (obligation_type, fy) => (cfda_edition, amount) """
            row['parsed_obligations'] = dict((((ob_type, fy), (cfda, amt))
                                              for (cfda, ob_type, fy, amt) in flattened_obligations))


            """ Parses a list of account identifiers from the list built by the
                import_programs_file method, reducing it down to a unique set. """
            account_identifiers = set()
            for account_string in row['account_identification']:
                accounts = re_account.findall(account_string)
                account_identifiers.update(accounts)
            row['parsed_accounts'] = account_identifiers

            """Convert the recovery field to a boolean."""
            if isinstance(row.get('recovery'), (str, bytes, unicode)):
                row['recovery'] = (row.get('recovery', '').lower() in ('y', 'yes'))


    def commit_programs(self):
        print "Parsing typed values from text fields."
        self._decode_strings()
        self._parse_fields()

        print "Committing changes to the database."
        new_program_count = 0

        #regex to pull account numbers ONLY out of free text
        account = re.compile('[\d]{2}[-][\d]{4}[-][\d]{1}[-][\d]{1}[-][\d]{3}')

        text_fields = set([fld.attname
                           for fld in Program._meta.fields
                           if isinstance(fld, django.db.models.TextField)])
        naive_fields = list(set(self.FIELD_MAPPINGS) & text_fields)

        for row in self.programs.values():
            (program, created) = Program.objects.get_or_create(
                program_number=row['program_number'],
                defaults={'load_date': datetime.now()})

            if created or program.cfda_edition < row['cfda_edition']:
                for fld in naive_fields:
                    setattr(program, fld, unicode(row.get(fld)))
                if created:
                    new_program_count += 1

                try:
                    agency_code = int(program.program_number[:2])
                    program.agency = Agency.objects.get(code=agency_code)
                except Agency.DoesNotExist as e:
                    print "Unrecognized agency prefix {0} in CFDA program number {1}".format(
                        agency_code, program.program_number)
                except ValueError as e:
                    print "Invalid CFDA program number: {0}".format(program.program_number)
                    print "Program numbers must begin with two digits."
      

                for account_number in row['parsed_accounts']:
                    (account, created) = ProgramAccount.objects.get_or_create(account_number=account_number)
                    program.account_identification.add(account_number)

                for assistance_code in row['parsed_types_of_assistance']:
                    assistance_type = AssistanceType.objects.get(code=assistance_code)
                    program.types_of_assistance.add(assistance_type)

                for ((ob_type, fy), (ob_cfda_edition, amt)) in row['parsed_obligations'].items():
                    (obligation, created) = ProgramObligation.objects.get_or_create(
                        program=program,
                        fiscal_year=fy,
                        obligation_type=ob_type,
                        defaults={
                            'cfda_edition': ob_cfda_edition,
                            'obligation': amt
                        })
                    if obligation.cfda_edition < ob_cfda_edition:
                        obligation.cfda_edition = ob_cfda_edition
                        obligation.obligation = amt
                        obligation.save()
            
                program.save()

        # Remove programs from years outside our range
        # ProgramObligation.objects.exclude(fiscal_year__in=settings.FISCAL_YEARS).delete()

        print "Run complete. \n%s new programs were added" % new_program_count
        
    
    def compare(self):
        pass
