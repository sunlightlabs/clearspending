import os
import random
from fnmatch import fnmatch

from cfda.models import *
from django.conf import settings

settings.DEBUG = False

agency_map = {'10': 'Department of Agriculture', '11': 'Department of Commerce', '12': 'Department of Defense', '14':'Department of Housing and Urban Development', '15': 'Department of the Interior', '16':'Department of Justice', '17': 'Department of Labor', '19': 'U.S. Department of State', '20':'Department of Transportation', '21':'Department of the Treasury', '23':'Appalachian Regional Commission', '27':'Office of Personnel Management', '29':'Commission on Civil Rights', '30':'Equal Employment Opportunity Commission', '31':'Export Import Bank of the United States', '32':'Federal Communications Commission','33':'Federal Maritime Commission', '34': 'Federal Mediation and Concillation Service', '36':'Federal Trade Commission', '39':'General Services Administration', '40': 'Government Printing Office', '42':'Library of Congress', '43':'National Aeronautics and Space Administration', '44':'National Credit Union Administration', '45':'National Endowment for the Arts', '46':'National Labor Relations Board', '47':'National Science Foundation', '57':'Railroad Retirement Board', '58':'Securities and Exchange Commission', '59':'Small Business Administraton', '64':'Department of Veterans Affairs', '66':'Environmental Protection Agency', '68':'National Gallery of Art', '70':'Overseas Private Investment Corporation', '77':'Nuclear Regulatory Commission', '78':'Commodity Futures Trading Commission', '81':'Department of Energy', '84':'Department of Education', '85': 'Various Scholarship and Fellowship Foundations', '86':'Pension Benefit Guaranty Corporation', '88':'Architectural and Transportation Barriers Compliance Board', '89':'National Archives and Records Administration', '90':'Denali Commission, Delta Regional Authority, Japan US Friendship Commission, US Election Assistance Commission, Broadcasting Board of Governors', '91':'United States Institute of Peace', '93':'Department of Health and Human Services', '94':'Corporation for National and Community Service', '95': 'Executive Office of the President', '96':'Social Security Administration', '97':'Department of Homeland Security', '98':'United States Agency for International Development' }


def main():
    
    #generate/update assistance types
    AssistanceType.objects.generate()
    
    for k in agency_map.keys():
        try:
            ag = Agency.objects.get(code=int(k))

        except Agency.DoesNotExist:
            ag = Agency(code=int(k), name=agency_map[k])

        ag.save()

    pattern = "programs-full" + ("[0-9]" * 5) + ".csv"
    files = [filename
             for filename in os.listdir(settings.CFDA_DOWNLOAD_DIR)
             if fnmatch(filename, pattern)]
    files.sort()

    if len(files) > 1000:
        sampled_files = list(set(random.sample(files, 1000)) | set(files[-1:]))
        sampled_files.sort()
    else:
        sampled_files = files
    print "Will import from:"
    for filename in sampled_files:
        print "\t{0}".format(filename)

    print
    print "{cnt} Programs before import.".format(cnt=Program.objects.count())
    man = ProgramManager()
    for (idx, filename) in enumerate(sampled_files):
        filepath = os.path.join(settings.CFDA_DOWNLOAD_DIR, filename)
        print "Importing {0}".format(filepath)
        man.import_programs_file(filepath)

    print "Committing changes to the database."
    man.commit_programs()

    print "{cnt} Programs after import.".format(cnt=Program.objects.count())

if __name__ == '__main__':
    main()


