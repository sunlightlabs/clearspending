from django.core.management.base import NoArgsCommand
from timeliness.analyzer import analyzer_main
import sys

class Command(NoArgsCommand):
    help = "Analyze binary USASpending data."

    def handle_noargs(self, **options):
        analyzer_main()
