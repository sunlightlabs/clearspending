from django.core.management.base import NoArgsCommand
from faads_scorecard.timeliness import parse
import sys

class Command(NoArgsCommand):
    help = "Parse raw USASpending into tab delimited file containing new awards by submission date (used for subsequent analysis)."

    def handle_noargs(self, **options):
        parse()
                