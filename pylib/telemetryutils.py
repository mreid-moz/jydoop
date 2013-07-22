"""Utilities for querying telemetry data using jydoop."""

# NOTE: When modifying this file, be careful to use java-specific imports
# only within setupjob, so that people can test scripts using python!

dateformat = 'yyyyMMdd'

def setupjob(job, args):
    """
    Set up a job to run on telemetry date ranges using data from HBase

    Telemetry jobs expect two arguments, startdate and enddate, both in yyyymmdd format.
    """

    import java.text.SimpleDateFormat as SimpleDateFormat
    import java.util.Calendar as Calendar
    import com.mozilla.hadoop.hbase.mapreduce.MultiScanTableMapReduceUtil as MSTMRU
    import com.mozilla.util.Pair

    if len(args) != 2:
        raise Exception("Usage: <startdate-YYYYMMDD> <enddate-YYYYMMDD>")

    sdf = SimpleDateFormat(dateformat)
    startdate = Calendar.getInstance()
    startdate.setTime(sdf.parse(args[0]))
    enddate = Calendar.getInstance()
    enddate.setTime(sdf.parse(args[1]))

    columns = [com.mozilla.util.Pair('data', 'json')]
    scans = MSTMRU.generateBytePrefixScans(startdate, enddate, dateformat,
                                           columns, 500, False)
    MSTMRU.initMultiScanTableMapperJob(
        'telemetry',
        scans,
        None, None, None, job)

    # inform HadoopDriver about the columns we expect to receive
    job.getConfiguration().set("org.mozilla.jydoop.hbasecolumns", "data:json");


hdfs_pathformat = '/data/telemetry/%s'
hdfs_dateformat = 'yyyy/MM/dd'

def hdfs_setupjob(job, args):
    """
    Similar to the above, but run telemetry data that's already been exported
    to HDFS.

    Jobs expect two arguments, startdate and enddate, both in yyyyMMdd format.
    """

    import java.text.SimpleDateFormat as SimpleDateFormat
    import java.util.Date as Date
    import java.util.Calendar as Calendar
    import com.mozilla.util.DateUtil as DateUtil
    import com.mozilla.util.DateIterator as DateIterator
    import org.apache.hadoop.mapreduce.lib.input.FileInputFormat as FileInputFormat
    import org.apache.hadoop.mapreduce.lib.input.SequenceFileAsTextInputFormat as MyInputFormat

    if len(args) != 2:
        raise Exception("Usage: <startdate-YYYYMMDD> <enddate-YYYYMMDD>")

    # use to collect up each date in the given range
    class MyDateIterator(DateIterator):
       def __init__(self):
          self._list = []
       def get(self):
          return self._list
       def see(self, aTime):
          self._list.append(aTime)

    sdf = SimpleDateFormat(dateformat)
    sdf_hdfs = SimpleDateFormat(hdfs_dateformat)
    startdate = Calendar.getInstance()
    startdate.setTime(sdf.parse(args[0]))

    enddate = Calendar.getInstance()
    enddate.setTime(sdf.parse(args[1]))

    dates = MyDateIterator()

    DateUtil.iterateByDay(startdate.getTimeInMillis(), enddate.getTimeInMillis(), dates)

    paths = []
    for d in dates.get():
       paths.append(hdfs_pathformat % (sdf_hdfs.format(Date(d))))

    job.setInputFormatClass(MyInputFormat)
    FileInputFormat.setInputPaths(job, ",".join(paths));

def hdfs_mappertype():
    return "TEXT"
