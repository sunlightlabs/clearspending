from django.core.management.base import NoArgsCommand
from faads_scorecard.completeness import main
import sys

class Command(NoArgsCommand):
    help = "Run completeness tests"

    def handle_noargs(self, **options):
        main()
                
            
                
