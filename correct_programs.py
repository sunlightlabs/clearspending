
from metrics.models import ProgramCorrection
from cfda.models import ProgramObligation, Program
from datetime import datetime
import sys

def update_obligation(new_obligation, program):
    
    old_obligation = program.obligation
    program.obligation = int(new_obligation)
    if program.usaspending_obligation:
        program.delta = program.usaspending_obligation - program.obligation
    else:
        program.delta = -program.obligation
    try:
        program.weighted_delta = program.delta / program.obligation
    except Exception:
        if program.obligation == 0:
            if not program.usaspending_obligation:
                program.weighted_delta = 0
            else:
                program.weighted_delta = 1
    program.corrected = True
    program.save()

    correction = ProgramCorrection(program=program.program, program_obligation=program, corrected_obligation=program.obligation, old_obligation=old_obligation, note="Corrected manually in program run",  correction_date=datetime.today())
    correction.save()

if __name__ == '__main__':

    while True:

        input = raw_input("Enter CFDA number:")
        try:
            program = Program.objects.get(program_number=input)
            obs = ProgramObligation.objects.filter(program=program).order_by('fiscal_year')
            count = 0
            print "%s" % program.program_title
            for o in obs:
                print "%d: %s  (%s)  %s" % ( count, o.fiscal_year, o.obligation_type, o.obligation)
                count += 1

            number = raw_input("Select an item number to update:")
            new_ob = raw_input("Enter new obligation amount:")

            update_obligation(new_ob, obs[int(number)])
        except Program.DoesNotExist:
            print 'No CFDA program found with that number.'


        if input == 'q': sys.exit()

