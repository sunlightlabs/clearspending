from django.core.management.base import NoArgsCommand
from faads_scorecard.timeliness import download
import sys

class Command(NoArgsCommand):
    help = "Download USASpending submissions (creates directory with over 3GB of data)."

    def handle_noargs(self, **options):
        download()
                