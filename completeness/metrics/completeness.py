#!/bin/python

from metrics import *
import re

re_non_nummeric = re.compile(r'[^\d]')
re_good_date = re.compile(r'\d{4}\-\d{2}\-\d{2}')

@boolean
def cfda_program_num_not_multi(row):
    return row['cfda_program_num'].strip()!='MU.LTI'

@boolean
def cfda_program_num_not_none(row):
    return row['cfda_program_num'].strip()!='00.000'
    
@boolean
def cfda_program_num_is_descriptive(row):
    return cfda_program_num_not_none(row) and cfda_program_num_not_multi(row) and len(row['cfda_program_num'].strip())>0
    
@boolean
def recipient_name_not_empty(row):
    return len(row['recipient_name'].strip()) > 0

@integer
def recipient_name_length(row):
    return len(row['recipient_name'].strip())

@boolean
def recipient_city_code():
    """docstring for recipient_city_code"""
    # TODO
    pass
    
@boolean
def recipient_city_name_not_empty(row):
    return len(row['recipient_city_name'].strip())>0

@boolean
def recipient_county_code_not_empty_or_too_long(row):
    x = row['recipient_county_code'].strip()
    return len(x)>0 and len(x)<=3
    
@boolean
def recipient_county_name_not_empty(row):
    return recipient_city_name_not_empty(row)

@boolean
def recipient_state_code_not_empty(row):
    return len(row['recipient_state_code'].strip())>0

@integer
def recipient_state_code_length(row):
    return len(row['recipient_state_code'].strip())
    
@boolean
def recipient_zip_code_not_empty(row):
    return len(row['recipient_zip'].strip())>0

@integer
def recipient_zip_code_length(row):
    return len(row['recipient_zip'].strip())

@boolean
def recipient_zip_code_is_numeric(row):
    return re_non_nummeric.search(row['recipient_zip']) is None

@boolean
def recipient_type_is_not_empty(row):
    return len(row['recipient_type'].strip())>0

@boolean
def action_type_is_not_empty(row):
    return len(row['action_type'].strip())>0

@boolean
def recipient_cong_district_is_not_empty(row):
    return len(row['recipient_cong_district'].strip())>0
    
@boolean
def federal_agency_code_is_not_empty(row):
    return len(row['agency_code'])>0

@integer
def federal_agency_code_length(row):
    return len(row['agency_code'])

@boolean
def federal_award_id_is_not_empty(row):
    return len(row['federal_award_id'].strip())>0

@boolean
def federal_funding_amount_is_not_empty(row):
    return len(row['fed_funding_amount'].strip())>0

@boolean
def federal_funding_amount_is_numeric(row):
    return re_non_nummeric.search(row['fed_funding_amount']) is None

@boolean
def obligation_action_date_is_not_empty(row):
    return len(row['obligation_action_date'])>0

@boolean
def obligation_action_date_is_properly_formatted(row):
    return not (re_good_date.match(row['obligation_action_date']) is None)

@boolean
def assistance_type_is_not_empty(row):
    return len(row['assistance_type'])>0

@boolean
def record_type_is_not_empty(row):
    return len(row['record_type'])>0

@boolean
def principal_place_state_not_empty(row):
    return len(row['principal_place_state'].strip())>0

@integer
def principal_place_state_length(row):
    return len(row['principal_place_state'].strip())

@boolean
def principal_place_cc_not_empty(row):
    return len(row['principal_place_cc'].strip())>0

@integer
def principal_place_cc_length(row):
    return len(row['principal_place_cc'].strip())



    
# fyq   varchar(6)  YES MUL NULL    
# cfda_program_num  varchar(7)  YES MUL NULL    
# sai_number    varchar(20) YES MUL NULL    
# recipient_name    varchar(45) YES MUL NULL    
# recipient_city_code   varchar(5)  YES     NULL    
# recipient_city_name   varchar(21) YES MUL NULL    
# recipient_county_code char(3) YES     NULL    
# recipient_county_name varchar(21) YES MUL NULL    
# recipient_state_code  char(2) YES MUL NULL    
# recipient_zip varchar(9)  YES MUL NULL    
# recipient_type    char(2) YES MUL NULL    
# action_type   char(1) YES     NULL    
# recipient_cong_district   char(2) YES MUL NULL    
# agency_code   varchar(4)  YES MUL NULL    
# federal_award_id  varchar(16) YES MUL NULL    
# federal_award_mod varchar(4)  YES     NULL    
# fed_funding_amount    bigint(11)  YES     NULL    
# non_fed_funding_amount    bigint(11)  YES     NULL    
# total_funding_amount  bigint(12)  YES     NULL    
# obligation_action_date    date    YES     NULL    
# starting_date date    YES     NULL    
# ending_date   date    YES     NULL    
# assistance_type   char(2) YES MUL NULL    
# record_type   char(1) YES     NULL    
# correction_late_ind   char(1) YES     NULL    
# fyq_correction    varchar(5)  YES     NULL    
# principal_place_code  varchar(7)  YES MUL NULL    
# principal_place_state varchar(25) YES     NULL    
# principal_place_cc    varchar(25) YES MUL NULL    
# principal_place_zip   varchar(9)  YES MUL NULL    
# principal_place_cd    char(2) YES MUL NULL    
# cfda_program_title    varchar(74) YES     NULL    
# agency_name   varchar(72) YES     NULL    
# recipient_state_name  varchar(25) YES     NULL    
# project_description   varchar(149)    YES MUL NULL    
# duns_no   varchar(13) YES MUL NULL    
# duns_conf_code    char(2) YES MUL NULL    
# progsrc_agen_code char(2) YES MUL NULL    
# progsrc_acnt_code varchar(4)  YES MUL NULL    
# progsrc_subacnt_code  char(3) YES MUL NULL    
# receip_addr1  varchar(35) YES     NULL    
# receip_addr2  varchar(35) YES     NULL    
# receip_addr3  varchar(35) YES     NULL    
# face_loan_guran   bigint(16)  YES     0   
# orig_sub_guran    bigint(16)  YES     0   
# parent_duns_no    varchar(13) YES MUL NULL    
# record_id bigint(20)  NO  PRI NULL    auto_increment
# fiscal_year   smallint(6) YES MUL NULL    
# principal_place_state_code    char(2) YES MUL NULL    
# award_id  bigint(11)  YES     0   
# recip_cat_type    char(1) YES MUL NULL    
# asst_cat_type char(1) YES MUL NULL    
# recipient_cd  varchar(4)  YES MUL NULL    
# maj_agency_cat    char(2) YES MUL NULL    
# mod_name  varchar(45) YES MUL     
# recip_id  bigint(11)  YES MUL 0   
# lookup_record_id  bigint(20)  YES MUL 0   
# lookup_recip_id   bigint(20)  YES MUL 0   
# business_identifier   char(3) YES     NULL    
# rec_flag  char(1) YES    