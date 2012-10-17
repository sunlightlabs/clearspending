import locale
from itertools import chain, izip
try:
    import cPickle as pickle
except ImportError:
    import pickle
import os
from operator import itemgetter


def grouped(xs, key):
    groups = {}
    key = key if callable(key) else itemgetter(key)
    for x in xs:
        k = key(x)
        grp = groups.get(k, [])
        grp.append(x)
        groups[k] = grp
    return groups.values()

def freq(xs, key):
    ftable = {}
    key = key if callable(key) else itemgetter(key)
    for x in xs:
        k = key(x)
        cnt = ftable.get(k, 0)
        ftable[k] = cnt + 1
    return ftable

class flattened(object):
    """An iterator class that automatically chains sub-iterators."""

    def __init__(self, iterable, as_is=(str, unicode, bytes)):
        self.iterator = iter(iterable)
        self.as_is = as_is

    def __iter__(self):
        return self

    def next(self):
        item = self.iterator.next()
        
        if not isinstance(item, self.as_is):
            try:
                new_iter = iter(item)
                self.iterator = chain(new_iter, self.iterator)
                return self.next()
            except TypeError:
                pass
        
        return item


def recursive_listdir(dpath):
    listing = []
    for entry in os.listdir(dpath):
        entry_path = os.path.join(dpath, entry)
        if os.path.isdir(entry_path):
            listing.append(recursive_listdir(entry_path))
        else:
            listing.append(entry_path)
    return listing


def pretty_bytes(n, sizes=['B', 'KB', 'MB', 'GB', 'TB']):
    if n >= 1024:
        return pretty_bytes(float(n) / float(1024), sizes[1:])
    else:
        return "%s %s" % (round(n, 1), sizes[0])


def pretty_seconds(s):
    (h, s) = divmod(s, 3600)
    (m, s) = divmod(s, 60)

    if h > 0:
        return "{h}:{m!s:0>2}:{s!s:0>2}".format(h=int(h), 
                                                m=int(m), 
                                                s=int(s))
    else:
        return "{m}:{s!s:0>2}".format(m=int(m), s=int(s))


def short_money(n):
    sizes = [
        ('tril', 10**12),
        ('bil', 10**9),
        ('mil', 10**6),
        ('K', 10**3),
    ]
    for (label, dollars) in sizes:
        if n >= dollars:
            short_n = round(float(n) / float(dollars), 2)
            if short_n == int(short_n):
                short_n = int(short_n)
            return "${0} {1}".format(short_n, label)
    return n


def pretty_money(m):
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    return locale.currency(m, grouping=True)


class Accumulator(object):
    """Simple callable that returns its current value."""
    def __init__(self, initial=0):
        self.value = initial

    def __call__(self, incr=0):
        oldvalue = self.value
        self.value += incr
        return oldvalue

    def getvalue(self):
        return self.value


def unpickle(path):
    with file(path) as f:
        return pickle.load(f)


class DictSlicer(object):
    def __init__(self, *ks):
        self.ks = ks

    def __call__(self, d):
        return dict(((k, v) for (k, v) in d.iteritems() if k in self.ks))

   
def chunk_list(xs, pred):
    if len(xs) == 0:
        return
    chunk = [xs[0]]
    prev = xs[0]
    for x in xs[1:]:
        split = pred(prev, x)
        if split:
            yield chunk
            chunk = []
        chunk.append(x)
        prev = x
    yield chunk


def izip_with(xs, ys, combine):
    """
    [x] -> [y] -> (x -> y -> z) -> [z]
    """
    for (x, y) in izip(xs, ys):
        yield combine(x, y)

