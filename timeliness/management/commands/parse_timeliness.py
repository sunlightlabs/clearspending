from django.core.management.base import NoArgsCommand
from timeliness.parser import parser_main
import sys

class Command(NoArgsCommand):
    help = "Parse raw USASpending agency submission files for new awards and stores them for subsequent analysis."

    def handle_noargs(self, **options):
        parser_main()
                
