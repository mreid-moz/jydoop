"""
UserProfile a.k.a. User Personalization is a feature of firefox in development.

It is an API we are implementing that exposes a user's interests based on their
browsing patterns, with user opt-in.

This script dumps the data collected via a TestPilot study, submitted to
data.mozilla.com
"""
import re
import hbaseutils

NOOP_PATTERN = re.compile("no-?op")

def setupjob(job, args):
    """
    Set up a job to run full table scans for UserProfile data.

    We don't expect any arguments.
    """
    hbaseutils.setup_full_scan_job("user_profile", job, args)

    # inform HadoopDriver about the columns we expect to receive
    job.getConfiguration().set("org.mozilla.jydoop.hbasecolumns", "data:json")
    job.getConfiguration().set("org.mozilla.jydoop.include_row_timestamp", "true")

def map(key, value, timestamp, context):
    if not NOOP_PATTERN.search(value):
        output = "[{0},{1}]".format(value,timestamp)
        context.write(timestamp,output)
