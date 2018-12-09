
import collections
import datetime
import fnmatch
import glob
import io
import math
import os
import random
import re
import time

import psutil

PUNCTUATION = set(u'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
NUMBERS = set(u'1234567890')
ALPHABET = set(u'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

UNPRINTABLE_CHARS = {
    u'\u0000',  # null
    u'\u0001',  # start of heading
    u'\u0002',  # start of text
    u'\u0003',  # end of text
    u'\u0004',  # end of transmission
    u'\u0005',  # enquiry
    u'\u0006',  # acknowledge (ACK)
    u'\u0007',  # bell (also used as bullet point)
    u'\u0008',  # backspace
    u'\u000e',  # shift out
    u'\u000f',  # shift in
    u'\u0010',  # data link escape
    u'\u0011',  # device control 1
    u'\u0012',  # device control 2
    u'\u0013',  # device control 3
    u'\u0014',  # device control 4
    u'\u0015',  # negative acknowledge
    u'\u0016',  # synchronous idle
    u'\u0017',  # end of transmission block
    u'\u0018',  # cancel
    u'\u0019',  # end of medium
    u'\u001a',  # substitute
    u'\u001b',  # escape (ESC)
    u'\u007f',  # delete (DEL)
    u'\ufffd',  # unicode replacement char
}

UNICODE_SPACES = {
    u'\u0009',  # horizontal tab == '\t'
    u'\u000a',  # line feed (new line) == '\n'
    u'\u000b',  # vertical tab == '\v'
    u'\u000c',  # form feed (new page)
    u'\u000d',  # carriage return == '\r'
    u'\u001c',  # file separator == '\f'
    u'\u001d',  # group separator
    u'\u001e',  # record separator
    u'\u001f',  # unit separator
    u'\u0020',  # space == ' '
    u'\u0085',  # next line
    u'\u00a0',  # non-breaking space
    u'\u1680',  # ogham space
    u'\u180e',  # mongolian vowel separator
    u'\u200b',  # zero width space
    u'\u200c',  # zero width non-joiner
    u'\u200d',  # zero width joiner
    u'\u2000',  # en quad
    u'\u2001',  # em quad
    u'\u2002',  # en space
    u'\u2003',  # em space
    u'\u2004',  # 3/em space
    u'\u2005',  # 4/em space
    u'\u2006',  # 6/em space
    u'\u2007',  # figure space
    u'\u2008',  # punctuation space
    u'\u2009',  # thin space
    u'\u200a',  # hair space
    u'\u2028',  # line separator
    u'\u2029',  # paragraph separator
    u'\u202f',  # narrow non-breaking space
    u'\u205f',  # medium mathematical space
    u'\u2060',  # word joiner
    u'\u2800',  # braille blank
    u'\u3000',  # ideographic space
    u'\ufeff',  # zero width non-breaking space (also byte order mark)
}


def crawl(top=u'.', pattern=u'*'):
    for potential_path in glob.glob(os.path.abspath(top)):
        if os.path.isdir(potential_path):
            for path, dir_list, file_list in os.walk(potential_path):
                for file_name in fnmatch.filter(file_list, pattern):
                    yield os.path.join(path, file_name)
        elif os.path.isfile(potential_path):
            if fnmatch.fnmatch(os.path.basename(potential_path), pattern):
                yield potential_path


def format_bytes(num):
    """
    string formatting
    :type num: int
    :rtype: str
    """
    num = abs(num)
    if num == 0:
        return u'0 Bytes'
    elif num == 1:
        return u'1 Byte'
    unit = 0
    while num >= 1024 and unit < 8:
        num /= 1024.0
        unit += 1
    unit = [u'Bytes', u'KiB', u'MiB', u'GiB', u'TiB', u'PiB', u'EiB', u'ZiB', u'YiB'][unit]
    return (u'%.2f %s' if num % 1 else u'%d %s') % (num, unit)


def format_seconds(num):
    """
    string formatting
    :type num: int | float
    :rtype: str
    """
    num = abs(num)
    if num == 0:
        return u'0 seconds'
    elif num == 1:
        return u'1 second'
    if num < 1:
        # display 2 significant figures worth of decimals
        return (u'%%0.%df seconds' % (1 - int(math.floor(math.log10(abs(num)))))) % num
    unit = 0
    denominators = [60.0, 60.0, 24.0, 7.0]
    while num >= denominators[unit] and unit < 4:
        num /= denominators[unit]
        unit += 1
    unit = [u'seconds', u'minutes', u'hours', u'days', u'weeks'][unit]
    return (u'%.2f %s' if num % 1 else u'%d %s') % (num, unit[:-1] if num == 1 else unit)


def char_group_tokenize(text, token_max_len=65535):
    """
    unused function
    tokenizes alphabet, numbers, and other unicode separately
    about 10% slower than the simpler tokenizer
    :param text:
    :param token_max_len:
    """
    # character classes
    punctuation = PUNCTUATION | UNPRINTABLE_CHARS
    spaces = UNICODE_SPACES
    numbers = NUMBERS
    alphabet = ALPHABET

    # init
    is_space = u''
    is_num = False
    is_alpha = False
    temp = u''

    # main loop over all text
    for char in text:

        # 1) chunks of alphabets (most common case first)
        if char in alphabet:
            if is_alpha and len(temp) < token_max_len:
                temp += char
            else:
                if temp:
                    yield temp
                temp = char
                is_space = u''
                is_alpha = True
                is_num = False

        # 2) numbers tokenized as chunks of digits
        elif char in numbers:
            if is_num and len(temp) < token_max_len:
                temp += char
            else:
                if temp:
                    yield temp
                temp = char
                is_space = u''
                is_alpha = False
                is_num = True

        # 3) spaces tokenized in groups of the same char
        elif char in spaces:
            if char == is_space and len(temp) < token_max_len:
                temp += char
            else:
                if temp:
                    yield temp
                temp = is_space = char
                is_alpha = False
                is_num = False

        # 4) punctuation tokenized as individual chars
        elif char in punctuation:
            if temp:
                yield temp
            yield char
            temp = is_space = u''
            is_alpha = False
            is_num = False

        # 5) arbitrary unicode, first token
        elif is_space or is_num or is_alpha:
            if temp:
                yield temp
            temp = char
            is_space = u''
            is_num = False
            is_alpha = False

        # 6) arbitrary unicode, next token
        elif len(temp) < token_max_len:
            temp += char

        # 7) arbitrary unicode, max token
        else:
            yield temp
            temp = char

    # finally, yield the last chunk
    if temp:
        yield temp


def space_tokenize(text, token_max_len=65535, emit_space=True, emit_punc=True):
    """
    tokenize by whitespace (and punctuation)
    :param text: to be split
    :param token_max_len: truncate tokens after this length
    :param emit_space: emit spaces
    :param emit_punc: emit punctuation
    """
    # character classes
    punctuation = PUNCTUATION | UNPRINTABLE_CHARS
    spaces = UNICODE_SPACES

    # init
    is_space = u''
    temp = u''

    # main loop over all text
    for char in text:
        # 1) spaces
        if char in spaces:
            if char == is_space and len(temp) < token_max_len:
                temp += char
            else:
                if temp:
                    yield temp
                temp = is_space = char if emit_space else ''

        # 2) punctuation
        elif char in punctuation:
            if temp:
                yield temp
            if emit_punc:
                yield char
            temp = is_space = u''

        # 3) first char
        elif is_space:
            if temp:
                yield temp
            temp = char
            is_space = u''

        # 4) next char
        elif len(temp) < token_max_len:
            temp += char

        # 5) max char
        else:
            yield temp
            temp = char

    # finally, yield the last chunk
    if temp:
        yield temp


def yield_lines(file_path, make_lower=False, threshold_len=0):
    """
    yields all non-empty lines in a file
    :param file_path: file to read
    :param make_lower: force line to lowercase
    :param threshold_len: ignore lines equal <= this length
    """
    with io.open(file_path, mode='r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if make_lower:
                line = line.lower()
            if len(line) > threshold_len:
                yield line


_SENTINEL = object()


class AhoCorasickReplace(object):
    """

    to find and replace lots of things in one pass
    something like aho-corasick search
    but at a token level
    """

    __slots__ = ('head', 'tokenizer')

    @staticmethod
    def fromkeys(keys, default='', verbose=False):
        _trie = AhoCorasickReplace()
        _trie.update(((key, default) for key in keys), verbose=verbose)
        return _trie

    class Node(dict):
        __slots__ = ('REPLACEMENT',)

        # noinspection PyMissingConstructor
        def __init__(self):
            self.REPLACEMENT = _SENTINEL

    def __init__(self, lexer=None, replacements=None):
        """
        :type lexer: Iterable -> Iterable
        """
        self.head = self.Node()

        if lexer is None:
            def lexer(seq):
                for elem in seq:
                    yield elem
        self.tokenizer = lexer

        if replacements is not None:
            self.update(replacements)

    def __contains__(self, key):
        head = self.head
        for token in self.tokenizer(key):
            if token not in head:
                return False
            head = head[token]
        return head.REPLACEMENT is not _SENTINEL

    def _item_slice(self, start, stop, step=None):
        out = []
        for key, value in self.items():
            if key >= stop:
                return out[::step]
            elif key >= start:
                out.append((key, value))
        return out[::step]

    def __getitem__(self, key):
        if type(key) is slice:
            return [value for key, value in self._item_slice(key.start, key.stop, key.step)]
        head = self.head
        for token in self.tokenizer(key):
            if token not in head:
                raise KeyError(key)
            head = head[token]
        if head.REPLACEMENT is _SENTINEL:
            raise KeyError(key)
        return head.REPLACEMENT

    def setdefault(self, key, value):
        head = self.head
        for token in self.tokenizer(key):
            head = head.setdefault(token, self.Node())
        if head.REPLACEMENT is not _SENTINEL:
            return head.REPLACEMENT
        head.REPLACEMENT = value
        return value

    def __setitem__(self, key, value):
        head = self.head
        for token in self.tokenizer(key):
            head = head.setdefault(token, self.Node())
        head.REPLACEMENT = value
        return value

    def pop(self, key=None):
        if key is None:
            for key in self.keys():
                break

        head = self.head
        breadcrumbs = [(None, head)]
        for token in self.tokenizer(key):
            head = head.setdefault(token, self.Node())
            breadcrumbs.append((token, head))
        if head.REPLACEMENT is _SENTINEL:
            raise KeyError(key)
        out = head.REPLACEMENT
        head.REPLACEMENT = _SENTINEL
        prev_token, _ = breadcrumbs.pop(-1)
        for token, head in breadcrumbs[::-1]:
            if len(head[prev_token]) == 0:
                del head[prev_token]
                prev_token = token
            else:
                break
            if head.REPLACEMENT is not _SENTINEL:
                break
        return out

    def items(self):
        _path = []
        _stack = [(self.head, sorted(self.head.keys(), reverse=True))]
        while _stack:
            head, keys = _stack.pop(-1)
            if keys:
                key = keys.pop(-1)
                _stack.append((head, keys))
                head = head[key]
                _path.append(key)
                if head.REPLACEMENT is not _SENTINEL:
                    yield ''.join(_path), head.REPLACEMENT
                _stack.append((head, sorted(head.keys(), reverse=True)))
            elif _path:
                _path.pop(-1)
            else:
                assert not _stack

    def to_regex(self, fix_spaces=True, fix_quotes=True, fix_fffd=True):
        _parts = [[], []]
        _stack = [(self.head, sorted(self.head.keys(), reverse=True))]
        while _stack:
            head, keys = _stack.pop(-1)
            if keys:
                key = keys.pop(-1)
                _stack.append((head, keys))
                head = head[key]

                # add new item
                if _parts[-1]:
                    _parts[-1].append('|')

                # character escaping and whitespace handling
                key = re.escape(key)
                if fix_fffd:
                    key = key.replace(u'\ufffd', '.')  # unicode replacement character
                if fix_quotes:
                    key = key.replace(u'\u2019', u"[\u2019']")  # quote
                if fix_spaces:
                    key = re.sub(u'\\s', u'\\s', key)
                _parts[-1].append(key)

                # one level down
                _stack.append((head, sorted(head.keys(), reverse=True)))
                _parts.append([])

            else:
                _current_parts = _parts.pop()
                if _current_parts:
                    if head.REPLACEMENT is not _SENTINEL:
                        _parts[-1].append('(?:')
                        _parts[-1].extend(_current_parts)
                        _parts[-1].append(')?')
                    elif len(head) != 1:
                        _parts[-1].append('(?:')
                        _parts[-1].extend(_current_parts)
                        _parts[-1].append(')')
                    else:
                        _parts[-1].extend(_current_parts)

        assert len(_parts) == 1
        re_pattern = ''.join(_parts[0])
        # simplify singleton groups
        re_pattern = re.sub(r'\(\?:(\\?.)\)', r'\1', re_pattern)
        # simplify single-char option groups
        re_pattern = re.sub(r'\(\?:(\\?.)(?:\|(\\?.))(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?'
                            r'(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?(?:\|(\\?.))?\)',
                            lambda x: '[%s]'%(''.join(y for y in x.groups() if y is not None)), re_pattern)
        return re_pattern

    def keys(self):
        for key, value in self.items():
            yield key

    def values(self):
        for key, value in self.items():
            yield value

    def __delitem__(self, key):
        if type(key) is slice:
            for key, value in self._item_slice(key.start, key.stop, key.step):
                self.pop(key)
        else:
            self.pop(key)

    def update(self, replacements, verbose=True):
        """
        :type replacements: list[(str, str)] | dict[str, str] | Generator[(str, str), Any, None]
        :type verbose: bool
        """
        if type(replacements) is list:
            print_str = u'(%%d pairs loaded out of %d)' % len(replacements)
        elif type(replacements) is dict:
            print_str = u'(%%d pairs loaded out of %d)' % len(replacements)
            replacements = replacements.items()
        else:
            print_str = u'(%d pairs loaded)'

        for index, (sequence, replacement) in enumerate(replacements):
            if verbose and (index + 1) % 50000 == 0:
                print(print_str % (index + 1))
            self[sequence] = replacement
        return self

    def _yield_tokens(self, file_path, encoding='utf8'):
        """
        yield tokens from a file given its path
        :param file_path: file to read
        """
        with io.open(file_path, mode=('r', 'rb')[encoding is None], encoding=encoding) as f:
            for token in self.tokenizer(char for line in f for char in line):
                yield token

    def translate(self, input_sequence):
        """
        processes text and yields output one token at a time
        :param input_sequence: iterable of hashable objects, preferably a string
        :type input_sequence: str | Iterable
        """
        output_buffer = collections.deque()  # [(index, token), ...]
        matches = dict()  # {span_start: (span_end + 1, REPLACEMENT), ...} <-- because: match == seq[start:end+1]
        spans = dict()  # positions that are partial matches: {span_start: span_head, ...}
        matches_to_remove = set()  # positions where matches may not start
        spans_to_remove = set()  # positions where matches may not start, or where matching failed

        for index, input_item in enumerate(input_sequence):
            # append new item to output_buffer
            output_buffer.append((index, input_item))

            # append new span to queue
            spans[index] = self.head

            # reset lists of things to remove
            matches_to_remove.clear()  # clearing is faster than creating a new set
            spans_to_remove.clear()

            # process spans in queue
            for span_start, span_head in spans.items():
                if input_item in span_head:
                    new_head = span_head[input_item]
                    spans[span_start] = new_head
                    if new_head.REPLACEMENT is not _SENTINEL:
                        matches[span_start] = (index + 1, new_head.REPLACEMENT)

                        # longest subsequence matching does not allow one match to start within another match
                        matches_to_remove.update(xrange(span_start + 1, index + 1))
                        spans_to_remove.update(xrange(span_start + 1, index + 1))

                else:
                    # failed to match the current token
                    spans_to_remove.add(span_start)

            # remove impossible spans and matches from queues
            for span_start in matches_to_remove:
                if span_start in matches:
                    del matches[span_start]
            for span_start in spans_to_remove:
                if span_start in spans:
                    del spans[span_start]

            # get indices of matches and spans
            first_match = min(matches) if matches else index
            first_span = min(spans) if spans else index

            # emit all matches that start before the first span
            while first_match < first_span:
                # take info
                match_end, match_replacement = matches[first_match]
                # emit until match start
                while output_buffer and output_buffer[0][0] < first_match:
                    yield output_buffer.popleft()[1]
                # clear output_buffer until match end
                while output_buffer and output_buffer[0][0] < match_end:  # remember match_end already has the +1
                    output_buffer.popleft()
                # emit replacement
                for item in match_replacement:
                    yield item
                # grab next match and retry
                del matches[first_match]
                first_match = min(matches) if matches else index

            # emit until span
            while output_buffer and output_buffer[0][0] < first_span:
                yield output_buffer.popleft()[1]

        # ignore remaining unmatched spans, yield matches only
        for match_start, (match_end, match_replacement) in sorted(matches.items()):
            # emit until match start
            while output_buffer and output_buffer[0][0] < match_start:  # remember match_end already has the +1
                yield output_buffer.popleft()[1]
            # clear output_buffer until match end
            while output_buffer and output_buffer[0][0] < match_end:  # remember match_end already has the +1
                output_buffer.popleft()
            # emit replacement one token at a time
            for token in self.tokenizer(match_replacement):
                yield token

        # emit remainder of output_buffer
        while output_buffer:
            yield output_buffer.popleft()[1]

    def find_all(self, input_sequence, allow_overlapping=False, tokenizer=True):
        """
        finds all occurrences within a string
        :param input_sequence: iterable of hashable objects
        :type input_sequence: str | Iterable
        :param allow_overlapping: yield all overlapping matches (soar -> so, soar, oar)
        :type allow_overlapping: bool
        :param tokenizer: fundtoin to tokenize input, or True to use pre-defined tokenizer
        :type tokenizer: bool | function
        """
        matches = dict()  # {span_start: (span_end + 1, [span_stuff, ...]), ...} <-- because: match == seq[start:end+1]
        spans = dict()  # positions that are partial matches: {span_start: (span_head, [span_stuff, ...]), ...}
        matches_to_remove = set()  # positions where matches may not start
        spans_to_remove = set()  # positions where matches may not start, or where matching failed

        if tokenizer is True:
            tokenizer = self.tokenizer

        for index, input_item in enumerate(tokenizer(input_sequence)):
            # append new span to queue
            spans[index] = (self.head, [])

            # reset lists of things to remove
            matches_to_remove.clear()  # clearing is faster than creating a new set
            spans_to_remove.clear()

            # process spans in queue
            for span_start, (span_head, span_seq) in spans.items():
                if input_item in span_head:
                    new_head = span_head[input_item]
                    span_seq.append(input_item)
                    spans[span_start] = (new_head, span_seq)
                    if new_head.REPLACEMENT is not _SENTINEL:
                        matches[span_start] = (index + 1, span_seq[:])

                        # longest subsequence matching does not allow one match to start within another match
                        if not allow_overlapping:
                            matches_to_remove.update(xrange(span_start + 1, index + 1))
                            spans_to_remove.update(xrange(span_start + 1, index + 1))

                else:
                    # failed to match the current token
                    spans_to_remove.add(span_start)

            # remove impossible spans and matches from queues
            for span_start in matches_to_remove:
                if span_start in matches:
                    del matches[span_start]
            for span_start in spans_to_remove:
                if span_start in spans:
                    del spans[span_start]

            # get indices of matches and spans
            first_span = min(spans) if spans else index
            while matches:
                match_start = min(matches)
                if match_start < first_span or allow_overlapping:
                    yield ''.join(matches[match_start][1])
                    del matches[match_start]
                else:
                    break

        for match_start, (match_end, match_replacement) in sorted(matches.items()):
            yield ''.join(match_replacement)

    def process_path(self, input_path, output_path, overwrite=False, encoding='utf8'):
        """
        given a path
        make a copy and clean it
        :type input_path: str
        :type output_path: str
        :type overwrite: bool
        :type encoding: str
        """

        if os.path.exists(output_path) and not overwrite:
            # skip and log to screen once per thousand files
            if random.random() < 0.001:
                print(u'skipped: %s' % output_path)
        else:
            # recursively make necessary folders
            if not os.path.isdir(os.path.dirname(output_path)):
                os.makedirs(os.path.dirname(output_path))

            # process to temp file
            print(u'=' * 100)
            print(u'processing: %s' % input_path)
            print(u'input size: %s' % format_bytes(os.path.getsize(input_path)))
            temp_path = output_path + u'.partial'
            t0 = time.time()

            try:
                with io.open(temp_path, mode=('w', 'wb')[encoding is None], encoding=encoding) as f:
                    for output_chunk in self.translate(self._yield_tokens(input_path, encoding=encoding)):
                        f.write(output_chunk)

                print(u'    output: %s' % temp_path[:-8])

            except Exception:
                os.remove(temp_path)
                print(u'    failed: %s' % temp_path)
                raise

            # rename to output
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)
            t1 = time.time()
            print(u'total time: %s' % format_seconds(t1 - t0))


def self_test():
    # regex self-tests
    try:
        assert set(re.sub(u'\\s', u'', ''.join(UNICODE_SPACES), flags=re.U)) in [
            set(u'\u200b\u200c\u200d\u2060\u2800\ufeff'),
            set(u'\u180e\u200b\u200c\u200d\u2060\u2800\ufeff')]

    except AssertionError:
        print(u'whatever version of re you have has weird unicode spaces')
        print(repr(re.sub(u'\\s', u'', ''.join(UNICODE_SPACES), flags=re.U)))
        raise
    except TypeError:
        print(u'gotta use python 2.7')
        print(u'#python2.7 use_gazeteer.py')
        raise

    # feed in a list of tuples
    _trie = AhoCorasickReplace()
    _trie.update([(u'asd', u'111'), (u'hjk', u'222'), (u'dfgh', u'3333'), (u'ghjkl;', u'44444'), (u'jkl', u'!')])
    assert ''.join(_trie.translate(u'erasdfghjkll')) == u'er111fg222ll'
    assert ''.join(_trie.translate(u'erasdfghjkl;jkl;')) == u'er111f44444!;'
    assert ''.join(_trie.translate(u'erassdfghjkl;jkl;')) == u'erass3333!;!;'
    assert ''.join(_trie.translate(u'ersdfghjkll')) == u'ers3333!l'

    # test regex
    permutations = []
    for a in u'abcde':
        for b in u'abcde':
            for c in u'abcde':
                for d in u'abcde':
                    for e in u'abcde':
                        permutations.append(a + b + c + d + e)

    for _ in xrange(1000):
        chosen = set()
        for i in xrange(10):
            chosen.add(random.choice(permutations))
        _trie = AhoCorasickReplace.fromkeys(chosen)
        r1 = re.compile(_trie.to_regex())
        for found in r1.findall(' '.join(permutations)):
            chosen.remove(found)
        assert len(chosen) == 0

    # feed in a generator
    _trie = AhoCorasickReplace()
    _trie.update(x.split('.') for x in u'a.b b.c c.d d.a'.split())
    assert ''.join(_trie.translate(u'acbd')) == u'bdca'

    # feed in a dict
    _trie = AhoCorasickReplace()
    _trie.update({
        u'aa':                     u'2',
        u'aaa':                    u'3',
        u'aaaaaaaaaaaaaaaaaaaaaa': u'~',
        u'bbbb':                   u'!',
    })

    assert u'aaaaaaa' not in _trie
    _trie[u'aaaaaaa'] = '7'

    assert u''.join(_trie.translate(u'a' * 12 + u'b' + u'a' * 28)) == u'732b~33'
    assert u''.join(_trie.translate(u'a' * 40)) == u'~773a'
    assert u''.join(_trie.translate(u'a' * 45)) == u'~~a'
    assert u''.join(_trie.translate(u'a' * 25)) == u'~3'
    assert u''.join(_trie.translate(u'a' * 60)) == u'~~772'

    del _trie[u'bbbb']
    assert u'b' not in _trie.head

    del _trie[u'aaaaaaa']
    assert u'aaa' in _trie
    assert u'aaaaaaa' not in _trie
    assert u'aaaaaaaaaaaaaaaaaaaaaa' in _trie

    _trie[u'aaaa'] = 4

    del _trie[u'aaaaaaaaaaaaaaaaaaaaaa']
    assert u'aaa' in _trie
    assert u'aaaaaaa' not in _trie
    assert u'aaaaaaaaaaaaaaaaaaaaaa' not in _trie

    assert len(_trie.head[u'a'][u'a'][u'a']) == 1
    assert len(_trie.head[u'a'][u'a'][u'a'][u'a']) == 0

    del _trie[u'aaa':u'bbb']
    assert _trie.to_regex() == u'aa'

    _trie = AhoCorasickReplace.fromkeys(u'mad gas scar madagascar scare care car career error err are'.split())

    test = u'madagascareerror'
    assert list(_trie.find_all(test)) == [u'madagascar', u'error']
    assert list(_trie.find_all(test, True)) == \
           [u'mad', u'gas', u'madagascar', u'scar', u'car', u'scare', u'care', u'are', u'career', u'err', u'error']


if __name__ == '__main__':
    self_test()

    # define input/output
    input_folder = os.path.abspath(u'./regex_datetime')
    output_folder = os.path.abspath(u'./temp')
    file_name_pattern = u'*'

    # you can use a generator for the mapping to save memory space
    mapping = [(line.split()[0], line.split()[-1][::-1]) for line in yield_lines(u'new 1.txt')]
    print(u'%d pairs of replacements' % len(mapping))

    # parse mapping list into trie with a tokenizer
    print(u'parse map to trie...')
    t_init = datetime.datetime.now()
    m_init = psutil.virtual_memory().used

    # set tokenizer
    trie = AhoCorasickReplace(space_tokenize)
    trie.update(mapping, verbose=True)

    # no tokenizer is better if you want to build a regex
    # no tokenizer matches and replaces any substring, not just words
    trie2 = AhoCorasickReplace()
    trie2.update(mapping, verbose=True)

    m_end = psutil.virtual_memory().used
    t_end = datetime.datetime.now()
    print(u'parse completed!', format_seconds((t_end - t_init).total_seconds()))
    print(format_bytes(m_end - m_init))

    # start timer
    t_init = datetime.datetime.now()
    print(u'processing start...', t_init)

    # process everything using the same tokenizer
    for path in crawl(input_folder, file_name_pattern):
        if os.path.isfile(path):
            new_path = path.replace(input_folder, output_folder)
            trie.process_path(path, new_path, overwrite=True)

    # stop timer
    t_end = datetime.datetime.now()
    print(u'')
    print(u'processing complete!', t_end)
    print(u'processing total time:', format_seconds((t_end - t_init).total_seconds()))
    print(u'processing total time:', (t_end - t_init))

    # just find all matches, don't replace
    t = time.time()
    with io.open(u'new 1.txt', mode='r', encoding='utf8') as f:
        content = f.read()
    for i, match in enumerate(trie.find_all(content)):
        print(i, match)
    print(format_seconds(time.time() - t))

    # create regex
    print(trie2.to_regex())

