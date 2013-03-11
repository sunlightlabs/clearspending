import sys
import csv
from metrics.models import ProgramCompletenessDetail
from django.db.models import Sum
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    args = '<fiscal year>'
    help = "Show the dollars associated with each completeness field for the given fiscal year."

    def handle(self, fiscal_year, **options):
        fiscal_year = int(fiscal_year)
        completeness_aggregates = (ProgramCompletenessDetail.objects
                                                            .filter(fiscal_year=fiscal_year)
                                                            .aggregate(recipient_type=Sum('recipient_type_is_not_empty'),
                                                                       federal_agency_code=Sum('federal_agency_code_is_not_empty'),
                                                                       cfda_program_num=Sum('cfda_program_num_is_descriptive'),
                                                                       federal_funding_amount=Sum('federal_funding_amount_is_not_empty'),
                                                                       recipient_name=Sum('recipient_name_not_empty'),
                                                                       principal_place_code=Sum('principal_place_code_not_empty'),
                                                                       recipient_state=Sum('recipient_state_code_not_empty'),
                                                                       recipient_county_code=Sum('recipient_county_code_not_empty_or_too_long'),
                                                                       recipient_county_name=Sum('recipient_county_name_not_empty'),
                                                                       recipient_city_code=Sum('recipient_city_code_not_empty'),
                                                                       principal_place_state=Sum('principal_place_state_not_empty'),
                                                                       record_type=Sum('record_type_is_not_empty'),
                                                                       action_type=Sum('action_type_is_not_empty'),
                                                                       recipient_cong_district=Sum('recipient_cong_district_is_not_empty'),
                                                                       obligation_action_date=Sum('obligation_action_date_is_properly_formatted'),
                                                                       principal_place_cc=Sum('principal_place_cc_not_empty'),
                                                                       assistance_type=Sum('assistance_type_is_not_empty'),
                                                                       federal_award_id=Sum('federal_award_id_is_not_empty'),
                                                                       recipient_city_name=Sum('recipient_city_name_not_empty')))

        wrt = csv.writer(sys.stdout)
        wrt.writerow(['Field', 'FailedDollars'])
        for pair in completeness_aggregates.items():
            wrt.writerow(pair)
