from django.core.management.base import NoArgsCommand
from optparse import make_option
from timeliness import crawler
import sys
from datetime import datetime


def parse_date(date_candidate):
    formats = ('%Y-%m-%d', '%Y%m%d', '%m/%d/%Y', '%m/%d/%y')
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(date_candidate, fmt).date()
            return parsed_date
        except ValueError:
            pass
    raise ValueError(date_candidate)


class Command(NoArgsCommand):
    help = "Download USASpending submissions (creates directory with over 3GB of data)."
    option_list = NoArgsCommand.option_list + (
        make_option('--startdate', default=None,
                    help="Lower bound for the submission date."),
        make_option('--enddate', default=None,
                    help="Upper bound for the submission date.")
    )

    def handle_noargs(self, **options):
        startdate = options.get('startdate')
        enddate = options.get('enddate')

        try:
            if startdate is not None:
                startdate = parse_date(startdate)
            if enddate is not None:
                enddate = parse_date(enddate)
        except ValueError, err:
            print "Invalid date: %s" % err
            return

        if crawler.offer_resume():
            crawler.resume_main()
        else:
            crawler.crawl_main(startdate, enddate)

