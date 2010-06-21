from django.db import models
from cfda.models import Program, Agency


TYPE_CHOICES = (
    (1, 'Grants'),
    (2, 'Loans and Loan Guarantees'),
    (3, 'Combo'),
)
class Metric(models.Model):
    
    fiscal_year = models.IntegerField(blank=False, null=False)
    agency = models.ForeignKey('cfda.Agency', blank=False, null=False)
    
    class Meta:
        abstract = True

class AgencyConsistency(Metric):
    

    total_cfda_obligations = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False)
    total_usa_obligations =  models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False)
    total_programs =  models.IntegerField(blank=True, null=True)
    non_reporting_programs = models.ManyToManyField(Program)
    non_reported_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    non_reported_pct =  models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    under_reported_dollars =  models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    under_reported_pct =  models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    over_reported_dollars =  models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    over_reported_pct =  models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True)
    type = models.IntegerField(blank=False, null=False, choices=TYPE_CHOICES)

class AgencyTimeliness(Metric):
        
    late_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False) 
    late_rows = models.IntegerField(blank=False, null=False)
    
    total_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False) 
    total_rows = models.IntegerField(blank=False, null=False)

    avg_lag_rows = models.IntegerField(blank=False, null=False)
    avg_lag_dollars = models.IntegerField(blank=False, null=False)
    
    

    
class ProgramMetric(Metric):
    
    program = models.ForeignKey('cfda.Program', blank=False, null=False)
    
    class Meta:
        abstract = True
    
class ProgramConsistency(ProgramMetric):
    over_reported_pct = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    under_reported_pct = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    non_reported_pct = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    over_reported_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    under_reported_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    non_reported_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=True, null=True) 
    type = models.IntegerField(blank=False, null=False, choices=TYPE_CHOICES)

class ProgramTimeliness(ProgramMetric):
        
    late_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False) 
    late_rows = models.IntegerField(blank=False, null=False)
    
    total_dollars = models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False) 
    total_rows = models.IntegerField(blank=False, null=False)
    
    late_pct =  models.DecimalField(max_digits=21, decimal_places=2, blank=False, null=False) 


    avg_lag_rows = models.IntegerField(blank=False, null=False)
    avg_lag_dollars = models.IntegerField(blank=False, null=False)


class ProgramCorrection(models.Model):
    
    program = models.ForeignKey('cfda.Program', null=False, blank=False)
    program_obligation = models.ForeignKey('cfda.ProgramObligation', null=False, blank=False)
    correction_date = models.DateTimeField(null=False, blank=False)
    corrected_obligation = models.DecimalField(max_digits=20, decimal_places=2, blank=False)
    old_obligation = models.DecimalField(max_digits=20, decimal_places=2, blank=False)
    note = models.TextField("Notes on Correction", blank=True, null=True)

class ProgramCompleteness(Metric):
    def __unicode__(self):
        return "%s %s (%d) / %2.2f%% / $%.1fm" % (self.program.program_title, self.program.program_number, self.fiscal_year, (self.completeness_pct*100), self.completeness_dollars/1000000)
    class Meta:
        verbose_name = 'Program Completeness'
        
    program = models.ForeignKey('cfda.Program', null=False, blank=False)
    
    completeness_failed_dollars = models.DecimalField("Dollar total of rows failing one or more completeness tests", max_digits=21, decimal_places=2, null=True)
    completeness_total_dollars = models.DecimalField("Dollar total of all rows", max_digits=21, decimal_places=2, null=True)

class ProgramCompletenessDetail(Metric):
    def __unicode__(self):
        pct_sum = 0
        dollar_sum = 0
        for name in self.FIELD_NAMES:
            dollar_sum += getattr(self, '%s' % name, 0)
        
        return "%s %s (%d) / $%.1fm" % (self.program.program_title, self.program.program_number, self.fiscal_year, dollar_sum / 1000000)
    class Meta:
        verbose_name = 'Program Completeness (Detail)'    
        
    program = models.ForeignKey('cfda.Program', null=False, blank=False)

    recipient_type_is_not_empty = models.DecimalField("Recipient Type is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    federal_agency_code_is_not_empty = models.DecimalField("Federal Agency Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    cfda_program_num_is_descriptive = models.DecimalField("CFDA Program Number is descriptive ($ misreported)", max_digits=21, decimal_places=2, null=True)
    federal_funding_amount_is_not_empty = models.DecimalField("Federal Funding Amount is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_name_not_empty = models.DecimalField("Recipient Name is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    principal_place_code_not_empty = models.DecimalField("Principal Place of Performance Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_zip_code_is_properly_formatted = models.DecimalField("Recipient Zip Code is properly formatted ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_state_code_not_empty = models.DecimalField("Recipient State Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_county_code_not_empty_or_too_long = models.DecimalField("Recipient County Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_county_name_not_empty = models.DecimalField("Recipient County Name is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_city_code_not_empty = models.DecimalField("Recipient City Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    principal_place_state_not_empty = models.DecimalField("Principal Place of Performance State is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    record_type_is_not_empty = models.DecimalField("Record Type is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    action_type_is_not_empty = models.DecimalField("Action Type is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_cong_district_is_not_empty = models.DecimalField("Recipient Congressional District is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    obligation_action_date_is_properly_formatted = models.DecimalField("Obligation Action Date is properly formatted ($ misreported)", max_digits=21, decimal_places=2, null=True)
    principal_place_cc_not_empty = models.DecimalField("Principal Place of Performance County Code is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    assistance_type_is_not_empty = models.DecimalField("Assistance Type is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    federal_award_id_is_not_empty = models.DecimalField("Federal Award ID is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
    recipient_city_name_not_empty = models.DecimalField("Recipient City Name is not empty ($ misreported)", max_digits=21, decimal_places=2, null=True)
