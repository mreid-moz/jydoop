import inspect
import time
defaultglobals = dict(globals())

class LocalContext:
    def __init__(self, combinefunc=None):
        self.result = {}
        self.combinefunc = combinefunc
        if combinefunc is not None:
            self.combined = LocalContext()

    def write(self, key, value):
        self.result.setdefault(key, []).append(value)
        if self.combinefunc and len(self.result[key]) > 5:
            items = self.result.pop(key)
            self.combinefunc(key, items, self.combined)

    def __iter__(self):
        for k, values in self.result.iteritems():
            for v in values:
                yield k, v

    def finish(self):
        """
        Put the combine results back together with any uncombined map
        results.
        """
        if self.combinefunc is None:
            return
        for k, vlist in self.combined.result.iteritems():
            for v in vlist:
                self.result.setdefault(k, []).append(v)

def outputwithkey(rlist):
    for k, v in rlist:
        print "%s\t%s" % (k, v)

def outputnokey(rlist):
    for k, v in rlist:
        print v

def map_reduce(module, fd, outputpath):
    setupfunc = getattr(module, 'setupjob', None)
    mapfunc = getattr(module, 'map', None)
    reducefunc = getattr(module, 'reduce', None)
    combinefunc = getattr(module, 'combine', None)

    if setupfunc is None or not callable(setupfunc):
        print >>sys.stderr, "Analysis script doesn't define the required function `setupjob`."
        sys.exit(1)

    if mapfunc is None or not callable(mapfunc):
        print >>sys.stderr, "Analysis script doesn't define the required function `map`."
        sys.exit(1)
    include_timestamp = False
    argspec = inspect.getargspec(mapfunc)
    if len(argspec.args) > 3:
        # This is not perfect, since it will also pass timestamps in to multi-
        # column HBase map() functions, but those won't work right anyways.
        include_timestamp = True

    context = LocalContext(combinefunc)

    # We make fake keys by keeping track of the file offset from the incoming
    # file.
    total_lines = 0;
    for line in fd:
        total_lines += 1;
        if len(line) == 0:
            continue
        if include_timestamp:
            mapfunc('line_%s' % total_lines, line, int(time.time() * 1000), context)
        else:
            mapfunc('line_%s' % total_lines, line, context)

    context.finish()

    if reducefunc:
        reduced_context = LocalContext()
        for key, values in context.result.iteritems():
            module.reduce(key, values, reduced_context)
        context = reduced_context

    # By default, if the job has a reduce function, we want to print both
    # the key and the value.
    # If no reduction is happening, users usually don't care about the key.
    if hasattr(module, 'output'):
        outputfunc = module.output
    elif reducefunc:
        import jydoop
        outputfunc = jydoop.outputWithKey
    else:
        import jydoop
        outputfunc = jydoop.outputWithoutKey

    outputfunc(outputpath, iter(context))
    
if __name__ == '__main__':
    import imp, sys, os

    if len(sys.argv) != 4:
        print >>sys.stderr, "Usage: FileDriver.py <jobscript.py> <input.data or -> <outputpath>"
        sys.exit(1)

    modulepath, filepath, outputpath = sys.argv[1:]

    if filepath == "-":
        fd = sys.stdin
    else:
        fd = open(filepath)

    modulefd = open(modulepath)

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pylib'))
    sys.path.insert(0, os.path.dirname(modulepath))

    module = imp.load_module('pydoop_main', modulefd, modulepath, ('.py', 'U', 1))
    map_reduce(module, fd, outputpath)
