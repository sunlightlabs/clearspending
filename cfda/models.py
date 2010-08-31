
from django.db import models
import csv
import re
import sys
from django.utils.encoding import smart_unicode
import helpers.unicode as un
from datetime import datetime


class Agency(models.Model):
    def __unicode__(self):
        return self.name
    class Meta:
        ordering = ['name']
        
    code = models.IntegerField(primary_key=True, blank=False, null=False)
    name = models.TextField("Federal Agency", blank=True, default="")
    description = models.TextField("Description", blank=True, default="")

class AssistanceType(models.Model):
    def __unicode__(self):
        return "%s" % self.code
    
    class Meta:
        verbose_name = 'Assistance Type'
    
    CODE_OPTIONS = (
        (1, "Formula Grants", ("Formula Grants (Cooperative Agreements)")),
        (2, "Project Grants", ("Project Grants (Discretionary)", "Project Grants (Cooperative Agreements)", "Project Grants (Contracts)", "Project Grants (Special)", "Project Grants (Fellowships)")), 
        (3, "Direct Payments for Specified Use", ("Direct Payments for a Specified Use")),
        (4, "Direct Payments with Unrestricted Use"),
        (5, "Direct Loans"),
        (6, "Guaranteed/Insured Loans"),
        (7, "Insurance"),
        (8, "Sale, Exchange, or Donation of Property and Goods", ("Sale, Exchange, or Donation of Property or Goods")),
        (9, "Use of Property, Facilities, and Equipment"),
        (10, "Provision of Specialized Services"),
        (11, "Advisory Services and Counseling"),
        (12, "Dissemination of Technical Information"),
        (13, "Training"),
        (14, "Investigation of Complaints"),
        (15, "Federal Employment"),
        (16, "Cooperative Agreements"),
    )

    code = models.IntegerField("Numeric Code", max_length=2, blank=False)
    financial = models.BooleanField(default=True)
     
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

class ProgramObligation(models.Model):

    program = models.ForeignKey('Program', blank=False, null=False)
    fiscal_year = models.IntegerField(blank=False, null=False)
    obligation = models.DecimalField(max_digits=27, decimal_places=2, blank=False, null=False)
    usaspending_obligation = models.DecimalField(max_digits=27, decimal_places=2, blank=True, null=True)
    delta = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    weighted_delta = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    cfda_version = models.IntegerField(blank=False, null=False)
    corrected = models.BooleanField(default=False)

    TYPE_CHOICES = (
        (1, 'Grants'),
        (2, 'Loans'),
        (3, 'Loan Guarantees'),
        (4, 'Insurance')
    )

    type = models.IntegerField(max_length=1, choices=TYPE_CHOICES) #for simplicity's sake this has been collapsed in the actual processing, grants=1 everything else=2
    GRADE_CHOICES = (
        ('p', 'Pass'),
        ('o', 'Overreporting Obligations'),
        ('u', 'Underreporting Obligations'),
        ('n', 'Not reporting Obligations'),
        ('t', 'Late reporting'),
        ('c', 'Incomplete reporting')
    )
    grade = models.TextField(choices=GRADE_CHOICES)

class ProgramAccount(models.Model):

    account_number = models.TextField(blank=False, null=False)


class Program(models.Model):

    def __unicode__(self):
        return "%s %s" % (self.program_number, self.program_title)

    program_number = models.CharField("Program number", max_length=7)
    program_title = models.CharField("Program title", max_length=255)
    federal_agency = models.TextField("Federal agency", blank=True, default="")
    agency = models.ForeignKey('Agency', blank=True, null=True)
    authorization = models.TextField("Authorization",blank=True,default="")
    objectives = models.TextField("Objectives",blank=True,default="")
    types_of_assistance = models.ManyToManyField(AssistanceType)
    uses_and_use_restrictions = models.TextField("Uses and use restrictions",blank=True,default="")
    applicant_eligibility = models.TextField("Applicant eligibility",blank=True,default="")
    beneficiary_eligibility = models.TextField("Beneficiary eligibility",blank=True,default="")
    credentials_documentation = models.TextField("Credentials / documentation",blank=True,default="")
    preapplication_coordination = models.TextField("Preapplication coordination",blank=True,default="")
    application_procedure = models.TextField("Application procedure",blank=True,default="")
    award_procedure = models.TextField("Award procedure",blank=True,default="")
    deadlines = models.TextField("Deadlines",blank=True,default="")
    range_of_approval_disapproval_time = models.TextField("Range of approval / disapproval time",blank=True,default="")
    appeals = models.TextField("Appeals",blank=True,default="")
    renewals = models.TextField("Renewals",blank=True,default="")
    formula_and_matching_requirements = models.TextField("Formula and matching requirements",blank=True,default="")
    length_and_time_phasing_of_assistance = models.TextField("Length and time phasing of assistance",blank=True,default="")
    reports = models.TextField("Reports",blank=True,default="")
    audits = models.TextField("Audits",blank=True,default="")
    records = models.TextField("Records",blank=True,default="")
    account_identification = models.ManyToManyField(ProgramAccount)
    range_and_average_of_financial_assistance = models.TextField("Range and average of financial assistance",blank=True,default="")
    program_accomplishments = models.TextField("Program accomplishments",blank=True,default="")
    regulations_guidelines_and_literature = models.TextField("Regulations guidelines and literature",blank=True,default="")
    regional_or_local_office = models.TextField("Regional or local office",blank=True,default="")
    headquarters_office = models.TextField("Headquarters office",blank=True,default="")
    web_site_address = models.TextField("Web site address",blank=True,default="")
    related_programs = models.TextField("Related programs",blank=True,default="")
    examples_of_funded_projects = models.TextField("Examples of funded projects",blank=True,default="")
    criteria_for_selecting_proposals = models.TextField("Criteria for selecting proposals",blank=True,default="")
    published_date = models.TextField("Published Date", blank=True, default="")
    parent_shortname = models.TextField("Parent Shortname", blank=True, default="")
    url = models.TextField("URL on CFDA website", blank=True, default="")
    recovery = models.BooleanField(default=False)

    cfda_edition = models.IntegerField("CFDA Edition", blank=True, null=True)
    load_date = models.DateTimeField("Load Date", auto_now=True)    


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
        'load_date'
    ]

    def import_programs(self, file):
        date = datetime.today()
        new_program_count = 0
        f = open(file, 'rU')
        this_version = int(file[-9:-4]) #pull the date off of the programs csv file
        #updated kevin's regex to include 2010 funding
        re_funding = re.compile('FY ([0-1][0,6-9]{1,1})( est. | est | )[\$]([0-9,]+)')
        re_funding_type = re.compile('\((.*?)\)')
        re_exclude = re.compile('[sS]alaries')
        re_loan = re.compile('[lL]oan')
        re_guar = re.compile('[gG]uarantee')
        re_insur = re.compile('[iI]nsur')
        
        #regex to pull account numbers ONLY out of free text
        account = re.compile('[\d]{2}[-][\d]{4}[-][\d]{1}[-][\d]{1}[-][\d]{3}')

        re_writer = csv.writer(open('csv/regex_check.csv', 'w')) 

        reader = csv.reader(f)
        reader.next() # skip headers
        while True:
            try:
                row = reader.next()
            except:
                break

            if not row:
                break
            
            if len(row) == 0 or len(row) < 10:
                continue 

            program_number = row[1].strip()
            matching_programs = Program.objects.filter(program_number=program_number)
           
            if len(matching_programs)==0:
                matching_program = Program()
                new_program_count += 1
            else:
                matching_program = matching_programs[0]
       
            try:
                agency = Agency.objects.get(code=int(program_number[:2]))
                matching_program.agency = agency
            
            except Exception,e:
                print "cfda program: %s, %s" % (program_number, e)
        
            for (i,s) in enumerate(self.FIELD_MAPPINGS):
                if s is None or i==2:
                    continue

                elif s == 'obligations':
                    # do obligations parsing
                    try:
                        clean_obs = smart_unicode(un.kill_gremlins(row[i]))
                        matches = re_funding.findall(clean_obs)
                        type_matches = re_funding_type.findall(clean_obs)
                        edited = []
                        type_iter = iter(type_matches)
                        if type_matches:
                            curr_type = type_iter.next()
                        else:
                            curr_type = 'default'
                        curr_year = '2000'
                        for tuple in matches:
                            year = '20' + tuple[0]

                            if year < curr_year:
                                try:
                                    curr_type = type_iter.next()

                                except StopIteration:
                                    pass
                                                                    
                            curr_year = year
                                 
                            if len(re_exclude.findall(curr_type)) <= 0:
                                obligation = tuple[2].replace(",", "")
                                
                                if len(re_guar.findall(curr_type)) > 0: type = 2  #guarantees and insurance had their own types but it was getting complicated so I collapsed them
                                elif len(re_loan.findall(curr_type)) > 0: type = 2
                                elif len(re_insur.findall(curr_type)) > 0: type = 2
                                else:
                                    try: 
                                        assist_types = matching_program.types_of_assistance.all()
                                        if assist_types[0].code == 6:
                                            type = 2
                                        elif assist_types[0].code == 7:
                                            type = 2
                                        elif assist_types[0].code == 5:
                                            type = 2
                                        else:
                                            type = 1

                                    except Exception:
                                        type = 1
                                    
                                matching_obligation = ProgramObligation.objects.filter(program=matching_program, fiscal_year=int(year), type=type)
                                if len(matching_obligation) == 0 or matching_obligation[0].cfda_version <= this_version:
                                    try:
                                        #either it doesn't exist yet or this is a newer version of cfda
                                        if len(matching_obligation) == 0:
                                            matching_ob = ProgramObligation(program=matching_program, fiscal_year=int(year), type=type)
                                        else:
                                            matching_ob = matching_obligation[0]
                                        
                                        if not matching_ob.corrected: #if it's been corrected don't update it
                                            matching_ob.cfda_version = this_version
                                            if matching_ob in edited:
                                                #there are multiple line items for this type, year and program in the obligation text, so we add instead of replacing
                                                matching_ob = edited[edited.index(matching_ob)]
                                                matching_ob.obligation += int(obligation)
                                            else:
                                                matching_ob.obligation = int(obligation)
                                                edited.append(matching_ob)
                                            
                                            matching_ob.delta = (matching_ob.usaspending_obligation or 0) - (matching_ob.obligation or 0)
                                            try:
                                                matching_ob.weighted_delta = matching_ob.delta / matching_ob.obligation
                                            except:
                                                matching_ob.weighted_delta = 0
    
                                            matching_ob.save()

                                    except Exception, e:
                                        print "in obs %s" % e


                    except Exception, e:
                        print "in obs exception %s" % e
                        print "\n"

                elif s == 'types_of_assistance':
                    # do extra assistance classifying
                    test = ''
                    try:
                        asst_types = smart_unicode(un.kill_gremlins(row[i])).strip('.').split(';')
                        for asst in asst_types:

                            clean_asst = asst.lower().strip().replace("\n", "")

                            for type_tuple in AssistanceType.CODE_OPTIONS:
                                if clean_asst == type_tuple[1].lower():
                                            
                                    matching_assistance_relations = matching_program.types_of_assistance.filter(code=type_tuple[0])
                                    if len(matching_assistance_relations) == 0:
                                        #need to add
                                        matching_program.types_of_assistance.add(AssistanceType.objects.get(code=type_tuple[0]))
                                        matching_program.save()
                                    
                                    test = 'match'

                                elif len(type_tuple) > 2:
                                    for other_name in type_tuple[2]:
                                        if clean_asst == other_name.lower():
                                            matching_assistance_relations = matching_program.types_of_assistance.filter(code=type_tuple[0])
                                            if len(matching_assistance_relations) == 0:
                                                #need to add
                                                matching_program.types_of_assistance.add(AssistanceType.objects.get(code=type_tuple[0]))
                                                matching_program.save()
                                    test = 'match'

                            if test != 'match':
                                print "Assistance type didn't match: %s" % asst
                                test = ''

                    except Exception, e:
                        print str(e) + 'bla'

                elif s == 'account_identification':
                    # do extra accounts parsing
                    try:
                        #account is a regex described above 
                        accts = account.findall(un.kill_gremlins(row[i]))

                        for a in accts:
                            matching_accounts = ProgramAccount.objects.filter(account_number=a)
                            if len(matching_accounts) == 0:
                                matching_account = ProgramAccount(account_number=a)
                                matching_account.save()

                            else:
                                matching_account = matching_accounts[0]
                            
                            if matching_account not in matching_program.account_identification.all():
                                matching_program.account_identification.add(matching_account)
                                matching_program.save()

                    except Exception, e:
                        print "account error %s" % e

                elif s == 'recovery':
                    # do extra parsing to change "No" and "Yes" to bool
                    try:
                        rec = smart_unicode(un.kill_gremlins(row[i]))
                        if rec == 'Yes' or rec == 'yes': 
                            setattr(matching_program, s, True)
                        else:
                            setattr(matching_program, s, False)
                    except Exception, e:
                        print "recovery field error %s" % e 
                else:
                    #everything else
                    try:
                        prepared_string = smart_unicode(un.kill_gremlins(row[i]))
                        setattr(matching_program, s, prepared_string)
                        if i == 1:
                            #we have the program vitals, save so we can use as foreign key for other attributes
                            matching_program.save()
                        
                    except Exception, e:
                        continue

            matching_program.save()
        f.close()

        print "Run complete. \n%s new programs were added" % new_program_count
        
    
    def compare(self):
        pass
