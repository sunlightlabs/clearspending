
from cfda.models import *

def main():

    file = "csv/programs-full10100.csv"
    if len(sys.argv) > 1:
        file = sys.argv[1]
    
    man = ProgramManager()
    man.import_programs(file)

if __name__ == '__main__':
    main()


