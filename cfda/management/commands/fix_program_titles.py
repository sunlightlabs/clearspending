import re
from optparse import make_option
from unidecode import unidecode
from django.core.management.base import BaseCommand
from cfda.models import Program
from utils import highlight_matches

class Command(BaseCommand):
    help = "Remove unwanted characters from program titles."
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    action='store_true',
                    default=False,
                    dest='dry_run',
                    help='Do not make any database changes.'),
        make_option('--pattern',
                    action='store',
                    default=ur'[^-/,\.:&\' a-zA-Z0-9()]+',
                    dest='pattern',
                    help='Regex pattern for matching bad characters.'),
    )

    def update_database(self):
        for (pro, fixed_title) in self.fixes:
            pro.program_title = fixed_title
            pro.save()
        self.fixes = []

    def handle(self, *args, **options):
        bad_pattern = re.compile(options['pattern'])
        self.fixes = []
        programs = Program.objects.all()
        for pro in programs:
            match = bad_pattern.search(pro.program_title)
            if match is not None:
                translated = unidecode(pro.program_title)
                fixed = bad_pattern.sub(' ', translated)
                highlighted = highlight_matches(bad_pattern, pro.program_title)
                print u"{orig}\n\t=> {fixed}\n".format(orig=highlighted,
                                                       fixed=fixed)
                self.fixes.append((pro, fixed))

        if len(self.fixes) == 0:
            print "No titles to fix."

        elif options.get('dry_run') is False:
            print "Should I commit these changes to the database?"
            while True:
                answer = raw_input("[y]es or [n]o >").lower()
                if answer in ("yes", "y"):
                    self.update_database()
                    break
                elif answer in ("no", "n"):
                    break

