#!/bin/python

import re, datetime

# convenience decorators for metrics

# true/false tests
def boolean(target):
    target.is_metric = True
    target.metric_type = 'boolean'
    return target
        
# calculates more aggregate statistics
def real(target):
    target.is_metric = True
    target.metric_type = 'real'
    return target
    
# calculates the same statistics as float, but also assembles a histogram
def integer(target):
    target.is_metric = True
    target.metric_type = 'integer'
    return target

# /decorators

re_non_nummeric = re.compile(r'[^\d]')
re_good_date = re.compile(r'\d{4}\-\d{2}\-\d{2}')

@boolean
def cfda_program_num_is_descriptive(row):
    """Record is tied to single CFDA Program Number"""
    return row['cfda_program_num'].strip()!='MU.LTI' and row['cfda_program_num'].strip()!='00.000' and cfda_program_num_not_none(row) and cfda_program_num_not_multi(row) and len(row['cfda_program_num'].strip())>0
    
@boolean
def recipient_name_not_empty(row):
    """Recipient Name is not empty"""
    return len(row['recipient_name'].strip()) > 0

@boolean
def recipient_city_code_not_empty(row):
    """Recipient City Code is not empty"""
    return len(row['recipient_city_code'].strip()) > 0
    
@boolean
def recipient_city_name_not_empty(row):
    """Recipient City Name is not empty"""
    return len(row['recipient_city_name'].strip())>0

@boolean
def recipient_county_code_not_empty_or_too_long(row):
    """Recipient County Code is properly-formed"""
    x = row['recipient_county_code'].strip()
    return len(x)>0 and len(x)<=3
    
@boolean
def recipient_county_name_not_empty(row):
    """Recipient County Name is not empty"""
    return recipient_city_name_not_empty(row)

@boolean
def recipient_state_code_not_empty(row):
    """Recipient State Code is not empty"""
    return len(row['recipient_state_code'].strip())>0

@boolean
def recipient_zip_code_is_properly_formatted(row):
    """Recipient zip code is properly formatted"""
    return len(row['recipient_zip'].strip())>0 and (re_non_nummeric.search(str(row['recipient_zip'])) is None)

@boolean
def recipient_type_is_not_empty(row):
    """Recipient Type is not empty"""
    return len(row['recipient_type'].strip())>0

@boolean
def action_type_is_not_empty(row):
    """Action Type is not empty"""
    return len(row['action_type'].strip())>0

@boolean
def recipient_cong_district_is_not_empty(row):
    """Recipient Congressional District is not empty"""
    return len(row['recipient_cong_district'].strip())>0
    
@boolean
def federal_agency_code_is_not_empty(row):
    """Federal Agency Code is not empty"""
    return len(row['agency_code'])>0

@boolean
def federal_award_id_is_not_empty(row):
    """Federal Award ID is not empty"""
    return len(row['federal_award_id'].strip())>0

@boolean
def federal_funding_amount_is_not_empty(row):
    """Federal Funding Amount is not empty"""
    obligation_amount_is_not_empty = row['fed_funding_amount'] is not None and len(str(row['fed_funding_amount']).strip())>0
    loan_guarantee_amount_is_not_empty = row['face_loan_guran'] is not None and len(str(row['face_loan_guran']).strip())>0
    obligation_amount_is_numeric = re_non_nummeric.search(str(row['fed_funding_amount'])) is None
    loan_guarantee_amount_is_numeric = re_non_nummeric.search(str(row['face_loan_guran'])) is None
    return (obligation_amount_is_not_empty and obligation_amount_is_numeric) or (loan_guarantee_amount_is_not_empty and loan_guarantee_amount_is_numeric)

@boolean
def obligation_action_date_is_properly_formatted(row):
    """Obligation Action Date is properly formatted"""
    return not (re_good_date.match(str(row['obligation_action_date'].strip())) is None)
    
@boolean
def assistance_type_is_not_empty(row):
    """Assistance Type is not empty"""
    return len(row['assistance_type'])>0

@boolean
def record_type_is_not_empty(row):
    """Record Type is not empty"""
    return len(row['record_type'])>0

@boolean
def principal_place_code_not_empty(row):
    """Principal Place of Performance Code is not empty"""
    return len(row['principal_place_code'])>0

@boolean
def principal_place_state_not_empty(row):
    """Principal Place of Performance State is not empty"""
    return len(row['principal_place_state'].strip())>0

@boolean
def principal_place_cc_not_empty(row):
    """Principal Place of Performance County Code is not empty"""
    return len(row['principal_place_cc'].strip())>0
