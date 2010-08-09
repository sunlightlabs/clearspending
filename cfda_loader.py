
from cfda.models import *

agency_map = {'10': 'Department of Agriculture', '11': 'Department of Commerce', '12': 'Department of Defense', '14':'Department of Housing and Urban Development', '15': 'Department of the Interior', '16':'Department of Justice', '17': 'Department of Labor', '19': 'U.S. Department of State', '20':'Department of Transportation', '21':'Department of the Treasury', '23':'Appalachian Regional Commission', '27':'Office of Personnel Management', '29':'Commission on Civil Rights', '30':'Equal Employment Opportunity Commission', '31':'Export Import Bank of the United States', '32':'Federal Communications Commission','33':'Federal Maritime Commission', '34': 'Federal Mediation and Concillation Service', '36':'Federal Trade Commission', '39':'General Services Administration', '40': 'Government Printing Office', '42':'Library of Congress', '43':'National Aeronautics and Space Administration', '44':'National Credit Union Administration', '45':'National Endowment for the Arts', '46':'National Labor Relations Board', '47':'National Science Foundation', '57':'Railroad Retirement Board', '58':'Securities and Exchange Commission', '59':'Small Business Administraton', '64':'Department of Veterans Affairs', '66':'Environmental Protection Agency', '68':'National Gallery of Art', '70':'Overseas Private Investment Corporation', '77':'Nuclear Regulatory Commission', '78':'Commodity Futures Trading Commission', '81':'Department of Energy', '84':'Department of Education', '85': 'Various Scholarship and Fellowship Foundations', '86':'Pension Benefit Guaranty Corporation', '88':'Architectural and Transportation Barriers Compliance Board', '89':'National Archives and Records Administration', '90':'Denali Commission, Delta Regional Authority, Japan US Friendship Commission, US Election Assistance Commission, Broadcasting Board of Governors', '91':'United States Institute of Peace', '93':'Department of Health and Human Services', '94':'Corporation for National and Community Service', '95': 'Executive Office of the President', '96':'Social Security Administration', '97':'Department of Homeland Security', '98':'United States Agency for International Development' }


def main():
    
    #generate/update assistance types
    at = AssistanceTypeManager()
    at.generate()
    
    for k in agency_map.keys():
        try:
            ag = Agency.objects.get(code=int(k))

        except Agency.DoesNotExist:
            ag = Agency(code=int(k), name=agency_map[k])

        ag.save()

    file = "csv/programs-full10121.csv"
    file_old = "csv/programs-full09164.csv"
    if len(sys.argv) > 1:
        file = sys.argv[1]
    
    man = ProgramManager()
    man.import_programs(file)
    man.import_programs(file_old) #for 2007 data

if __name__ == '__main__':
    main()


