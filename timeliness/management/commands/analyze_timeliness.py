from django.core.management.base import NoArgsCommand
from faads_scorecard.timeliness import analyze
import sys

class Command(NoArgsCommand):
    help = "Analyze binary USASpending data."

    def handle_noargs(self, **options):
        analyze()