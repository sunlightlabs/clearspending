
from django.db import models
import csv
import re
import sys
from django.utils.encoding import smart_unicode
import faads_scorecard.helpers.unicode
from datetime import datetime

#assistance types generally separated by semicolon
#obligations should be parsed out and entered as their own object, by fiscal year
#account identification has periods on the end and multiples are separated by semicolon
#website address should have period stripped off the end


class AssistanceType(models.Model):
    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Assistance Type'

    code = models.IntegerField("Numeric Code", max_length=2, blank=False)
    name = models.CharField("Descriptive Name", max_length=255, blank=False)    
    financial = models.BooleanField(default=True)
    
    CODE_OPTIONS = (
        (1, "Formula Grants"),
        (2, "Project Grants"), 
        (3, "Direct Payments for Specified Use"),
        (4, "Direct Payments with Unrestricted Use"),
        (5, "Direct Loans"),
        (6, "Guaranteed/Insured Loans"),
        (7, "Insurance"),
        (8, "Sale, Exchange, or Donation of Property and Goods"),
        (9, "Use of Property, Facilities, and Equipment"),
        (10, "Provision of Specialized Services"),
        (11, "Advisory Services and Counseling"),
        (12, "Dissemination of Technical Information"),
        (13, "Training"),
        (14, "Investigation of Complaints"),
        (15, "Federal Employment")
    )

class ProgramObligation(models.Model):

    program_number = models.ForeignKey('Program', blank=False, null=False)
    fiscal_year = models.IntegerField(blank=False, null=False)
    obligation = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False)

class ProgramAccount(models.Model):

    program_number = models.ForeignKey('Program', blank=False, null=False)
    account_number = models.TextField(blank=False, null=False)

class Program(models.Model):

    def __unicode__(self):
        return "%s %s" % (self.program_number, self.program_title)

    program_number = models.CharField("Program number", max_length=7)
    program_title = models.CharField("Program title", max_length=255)
    federal_agency = models.TextField("Federal agency", blank=True, default="")
    authorization = models.TextField("Authorization",blank=True,default="")
    objectives = models.TextField("Objectives",blank=True,default="")
    
    types_of_assistance = models.ForeignKey('AssistanceType', blank=True, null=True)   #classifier for financial/non-financial programs
    
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
    account_identification = models.TextField("Account identification",blank=True,default="")
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
        
        new_program_log = open('new_programs_log_%s' % date, 'w')
        error_log = open('cfda_import_error_log_%s' % date, 'w')

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
                print row
                continue 

            program_number = row[0].strip()
            matching_programs = Program.objects.filter(program_number=program_number)
           
            print row 
            sys.stdout.write(",".join(row))  #DEBUG
            sys.stdout.flush()

            if len(matching_programs)==0:
                matching_program = Program()
                new_program_log.write("%s \n" % (program_number))
                new_program_count += 1
            else:
                matching_program = matching_programs[0]
        
            for (i,s) in enumerate(self.FIELD_MAPPINGS):
                if s is None:
                    continue

                elif s == 'obligations':
                    pass # do obligations parsing
                elif s == 'types_of_assistance':
                    # do extra assistance classifying
                    try:
                        asst_types = smart_unicode(kill_gremlins(row[i])).strip('.').split(';')
                        for asst in asst_types:
                            for type_tuple in AssistanceType.CODE_OPTIONS:
                                if asst == type_tuple[1]:
                                    matching_assistance_types = AssistanceType.objects.filter(program_number=program_number, code=type_tuple[0])
                                    if len(matching_assistance_types) == 0:
                                        matching_assistance = AssistanceType()
                                    else:
                                        matching_assistance = matching_assistance_types[0]

                                    setattr(matching_assistance, 'program_number', program_number)
                                    setattr(matching_assistance, 'code', type_typle[0])
                                    if type_tuple[0] < 6: #is financial type?
                                        setattr(matching_assistance, 'financial', True)

                    except Exception, e:
                        error_log.write("unicode or parsing error on program %s, assistance type: %s, error: %s" % (program_number, row[i], str(e)))                            

                elif s == 'account_identification':
                    # do extra accounts parsing
                    try:
                        #accounts are usually split on semicolons and the line usually has a period at the end
                        accts = smart_unicode(kill_gremlins(row[i])).strip('.').split(';') 
                        for a in accts:
                            matching_accounts = ProgramAccount.objects.filter(program_number=program_number, account_number=a)
                            if len(matching_accounts) == 0:
                                matching_account = ProgramAccount()
                            else:
                                matching_account = matching_accounts[0]

                            setattr(matching_account, 'program_number', program_number)
                            setattr(matching_account, 'account_number', a)

                    except Exception, e:
                        error_log.write("error processing account id, program: %s, error: %s" % (program_number, str(e)))

                elif s == 'recovery':
                    # do extra parsing to change "No" and "Yes" to bool
                    try:
                        rec = smart_unicode(kill_gremlins(row[i]))
                        if rec == 'Yes' or rec == 'yes': 
                            setattr(matching_program, s, True)
                        else:
                            setattr(matching_program, s, False)
                    except Exception, e:
                        error_log.write("unicode error on recovery field, program: %s, error: %s" % (program_number, str(e)))
                else:
                    #everything else
                    try:
                        prepared_string = smart_unicode(kill_gremlins(row[i]))
                        setattr(matching_program, s, prepared_string)
                        
                    except Exception, e:
                        error_log.write("unicode error on field %s, program: %s, %s" % (s, program_number, str(e)))
                        continue


            matching_program.save()

        f.close()
        new_program_log.close()
        error_log.close()
        
    
    def compare(self):
        pass
