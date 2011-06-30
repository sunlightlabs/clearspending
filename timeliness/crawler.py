"""
Enumerates and downloads agency submission files from USASpending.gov.

Enumeration is done by using the AJAX JSON API that the site uses to
construct the table of files.
"""

import os
import sys
import pickle
import urllib
import urllib2
import demjson
import stream
from datetime import date, time, datetime
from BeautifulSoup import BeautifulSoup
from utils import pretty_bytes



from timeliness import DATA_DIR, DOWNLOAD_DIR, FISCAL_YEARS

URL_PATTERN = ("http://www.usaspending.gov/trendslist"
               + "?type=1"
#               + "&qcount="  This parameter seems to limit the search
#                             results but it isn't clear to me how it
#                             is supposed to be used.
               + "&trendreport=assistance"
               + "&fiscalyear=%(fiscalyear)s"
               + "&agencySelect="
               + "&startdate=%(startdate)s"
               + "&enddate=%(enddate)s"
               + "&page=%(page)s"
               + "&rp=50"
               + "&sortname=agency_submission_date"
               + "&sortorder=desc"
               + "&query="
               + "&qtype=")
DATA_URL_BASE = "http://www.usaspending.gov"


def request_listing(fy, startdate, enddate):
    json = demjson.JSON()
    params = {
        'fiscalyear': fy,
        'startdate': startdate.strftime('%Y-%m-%d') if startdate else '',
        'enddate': enddate.strftime('%Y-%m-%d') if enddate else '',
        'page': 1
    }
    rows_processed = 0
    listing = []
    try:
        sys.stdout.write("Listing agency submission files for fiscal year %s" % fy)
        while True:
            sys.stdout.write(".")
            sys.stdout.flush()

            url = URL_PATTERN % params
            response = urllib2.urlopen(url)
            if response.code == 200: # OK
                response_obj = json.decode(response.read())
                row_count = len(response_obj['rows'])
                total_rows = response_obj['total']

                for row in response_obj['rows']:
                    (agency, html, datetime) = row['cell']
                    href = extract_href(html)
                    if href:
                        listing.append((href, datetime))
                    rows_processed += 1

                if rows_processed == total_rows:
                    break
                else:
                    params['page'] += 1

            else:
                raise Exception("Unexpected response status code: %s" 
                                % str(response.code))
        sys.stdout.write("\n")
        return listing
    except urllib2.URLError, err:
        print "URLError encountered for fiscal year %s" % fy
        print "Problematic URL: %s" % url
        raise


def update_download_schedule(schedule, listing):
    """schedule is a list of 3-tuples:
         (href, datetime, (head-status, content-length))
       listing is a list of 2-tuples:
         (href, datetime)
       This function submits a HEAD request for each href,
       storing the the status code and content-length value
       obtained from the server.
       """

    def obtain_head(href):
        url = url_for_href(href)
        request = urllib2.Request(url)
        request.get_method = lambda: 'HEAD'
        try:
            response = urllib2.urlopen(request)
            if response.code == 200:
                response_info = response.info()
                content_length = int(response_info['Content-Length'])
                return (response.code, content_length)
            else:
                return (response.code, None)
        except urllib2.HTTPError, http_err:
            return (http_err.code, None)

    sys.stdout.write("Determining files to download")
    for (href, datetime) in listing:
        sys.stdout.write(".")
        sys.stdout.flush()

        destination_path = data_file_destination_path(href)
        if os.path.exists(destination_path):
            continue

        head = obtain_head(href)
        schedule.append((href, datetime, head))
    sys.stdout.write("\n")


def confirm_download_schedule(schedule):
    """Reports the total number of bytes and total number of files
    to download. Also lists the inaccessible files (based on HEAD
    response). Then asks user to confirm downloading.
    """

    def content_length(tpl):
        return tpl[2][1]

    def status_code(tpl):
        return tpl[2][0]

    def href(tpl):
        return tpl[0]

    def is_OK(tpl):
        return status_code(tpl) == 200

    def not_OK(tpl):
        return status_code(tpl) != 200

    increment = lambda x, _: x + 1
    file_count = (schedule
                  >> stream.filter(is_OK)
                  >> stream.reduce(increment, 0))

    bytes_to_download = (schedule
                         >> stream.filter(is_OK)
                         >> stream.map(content_length)
                         >> sum)

    inaccessible_files = (schedule
                          >> stream.filter(not_OK)
                          >> list)

    if len(inaccessible_files) > 0:
        print
        print "Some files are inaccessible:"
        for (idx, sched) in enumerate(inaccessible_files):
            print "%d: %d %s" % (idx, status_code(sched), href(sched))

    if bytes_to_download > 0:
        print
        print "Need to download %s in %d files." % (
            pretty_bytes(bytes_to_download),
            file_count)
        print
        print "Are you sure you want to continue? [Y/n]"
        user_input = raw_input("> ")
        return (user_input.upper() in ("", "Y", "YES"))
    else:
        print
        print "Nothing to download."
        return False


def data_file_destination_path(href):
    return os.path.join(DOWNLOAD_DIR, href[1:])


def url_for_href(href):
    return DATA_URL_BASE + urllib.quote(href)


def download_data_file(href):
    destination_path = data_file_destination_path(href)
    try:
        url = url_for_href(href)
        response = urllib2.urlopen(url)
        if response.code == 200:
            destination_dir = os.path.dirname(destination_path)
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
            with file(destination_path, 'w') as destination_file:
                destination_file.write(response.read())
        else:
            raise Exception("Unexpected response code %s for data file: %s"
                            % (str(response.code), destination_path))
    except KeyboardInterrupt:
        os.remove(destination_path)
        raise


def extract_href(html):
    soup = BeautifulSoup(html)
    anchor = soup.find('a')
    if anchor is None:
        return None
    return anchor['href']


def exec_download_schedule(schedule):
    while len(schedule) > 0:
        (href, datetime, head) = schedule.pop(0)
        (code, content_length) = head
        if code == 200:
            download_data_file(href)


def log_inaccessible_files(schedule):
    with file(os.path.join(DATA_DIR, 'missing.txt'), 'w') as missing_file:
        for (href, datetime, head) in schedule:
            (code, content_length) = head
            if code != 200:
                missing_file.write(url_for_href(href))
                missing_file.write('\n')


def schedule_file_path():
    return os.path.join(DATA_DIR, 'schedule.pickle')


def restore_schedule():
    schedule_path = schedule_file_path()
    if os.path.exists(schedule_path):
        with file(schedule_path, 'r') as schedule_file:
            return pickle.load(schedule_file)
    else:
        print 
        print "No download schedule found."
        print "Try the crawl or refresh commands."
        return None


def save_schedule(schedule):
    schedule_path = schedule_file_path()
    schedule = [entry for entry in schedule if entry[2][0] == 200]
    if len(schedule) > 0:
        with file(schedule_path, 'w') as schedule_file:
            pickle.dump(schedule, schedule_file)
    elif os.path.exists(schedule_path):
        os.remove(schedule_path)


def offer_resume():
    schedule_path = schedule_file_path()
    if os.path.exists(schedule_path):
        try:
            schedule = restore_schedule()
        except EOFError:
            print "Deleting corrupt download schedule."
            os.remove(schedule_path)
            return False

        size = os.path.getsize(schedule_path)
        print "A download schedule file exists:"
        print "    %s (%s)" % (schedule_path, pretty_bytes(size))
        print "You can either resume or delete this schedule."
        print "What would you like to do?"
        user_input = raw_input("[r]esume or [d]elete> ")
        if 'DELETE'.startswith(user_input.upper()):
            os.remove(schedule_path)
            return False
        else:
            return True
    else:
        return False


def crawl_main(startdate=None, enddate=None):
    download_schedule = []
    try:
        for fy in FISCAL_YEARS:
            listing = request_listing(fy, startdate, enddate)
            update_download_schedule(download_schedule, listing)

        log_inaccessible_files(download_schedule)

        if confirm_download_schedule(download_schedule):
            exec_download_schedule(download_schedule)
    except KeyboardInterrupt:
        print
        print "Exiting due to CTRL-C"
    finally:
        save_schedule(download_schedule)


def resume_main():
    download_schedule = restore_schedule()
    try:
        if download_schedule and confirm_download_schedule(download_schedule):
            exec_download_schedule(download_schedule)
    except KeyboardInterrupt:
        print
        print "Exiting due to CTRL-C"
    finally:
        save_schedule(download_schedule)
    

