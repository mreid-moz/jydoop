def setup_full_scan_job(table, job, args):
    """
    Set up a job to run full HBase table scans.

    We don't expect any extra args.
    """

    import org.apache.hadoop.hbase.client.Scan as Scan
    import com.mozilla.hadoop.hbase.mapreduce.MultiScanTableMapReduceUtil as MSTMRU

    scan = Scan()
    scan.setCaching(500)
    scan.setCacheBlocks(False)
    scan.addColumn(bytearray('data'), bytearray('json'))

    # FIXME: do it without this multi-scan util
    scans = [scan]
    MSTMRU.initMultiScanTableMapperJob(
        table, scans,
        None, None, None, job)

    # inform HadoopDriver about the columns we expect to receive
    job.getConfiguration().set("org.mozilla.jydoop.hbasecolumns", "data:json");
