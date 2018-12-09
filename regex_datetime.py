"""
Var     Meaning
%a      Locale's abbreviated weekday name.
%A      Locale's full weekday name.
%b      Locale's abbreviated month name.
%B      Locale's full month name.
%c      Locale's appropriate date and time representation.
%d      Day of the month as a decimal number.
%H      Hour (24-hour clock) as a decimal number [00,23].
%I      Hour (12-hour clock) as a decimal number [01,12].
%j      Day of the year as a decimal number [001,366].
%m      Month as a decimal number [01,12].
%M      Minute as a decimal number [00,59].
%p      Locale's equivalent of either AM or PM.
%S      Second as a decimal number [00,61].
%U      Week number of the year (Sunday as the first day of the week) as a decimal number [00,53].
        All days in a new year preceding the first Sunday are considered to be in week 0.
%w      Weekday as a decimal number [0(Sunday),6].
%W      Week number of the year (Monday as the first day of the week) as a decimal number [00,53].
        All days in a new year preceding the first Monday are considered to be in week 0.
%x      Locale's appropriate date representation.
%X      Locale's appropriate time representation.
%y      Year without century as a decimal number [00,99].
%Y      Year with century as a decimal number.
%Z      Time zone name (no characters if no time zone exists).
%%      A literal '%' character.

TODO: named groups
"""
import csv
import fnmatch
import io
import json
import os
import re

import scandir

REGEX_PARTS = {

    u'Y':       r"(?:19[4-9]\d|20[0-3]\d)",  # 1940 to 2039
    u'y':       r"(?:\d\d)",  # 00 to 99
    u'm':       r"(?:1[012]|0?[1-9])",  # 0?1 to 12
    u'mz':      r"(?:1[012]|0[1-9])",  # 01 to 12
    u'B':       r"(?:"
                r"D?JAN(?:UAR[IY])?|"
                r"[FP]EB(?:RUAR[IY])?|"
                r"MAC|MAR(?:CH|ET)?|MRT|"
                r"APR(?:IL)?|"
                r"M[EA]I|MAY|"
                r"JUNE?|D?JUNI?|"
                r"JUL(?:Y|AI)?|D?JULI?|"
                r"OG(?:OS)?|AUG(?:UST)?|AGT?(?:USTUS)?|"
                r"SEP(?:T(?:EMBER)?)?|"
                r"O[KC]T(?:OBER)?|"
                r"NO[VP](?:EMBER)?|"
                r"D[EI][SC](?:EMBER)?"
                r")",
    u'd':       r"(?:3[01]|[12]\d|0?[1-9])",  # 0?1 to 31
    u'd_range': r"(?:3[01]|[12]\d|0?[1-9])(?: ?[-] ?(?:3[01]|[12]\d|0?[1-9]))?",  # 14-15
    u'dz':      r"(?:3[01]|[12]\d|0[1-9])",  # 01 to 31
    u'j':       r"(?:36[0-6]|3[0-5]\d|[12]\d\d|0?[1-9]\d|0?0?[1-9])",  # 0?0?1 to 366
    u'H':       r"(?:2[0-4]|[01]?\d)",  # 0?0 to 24
    u'HZ':      r"(?:2[0-4]|[01]\d)",  # 0?0 to 24
    u'I':       r"(?:1[012]|0?[1-9])",  # 0?1 to 12
    u'M':       r"(?:[1-5]\d|0\d)",  # 00 to 59
    u'S':       r"(?:6[01]|[0-5]\d)",  # 00 to 61 (leap second)
    u'p':       r'(?:MIDNI(?:GHT|TE)|AFTERNOON|MORNING|NOON|[MN]N|H(?:RS?)?|[AP]\.? ?M\.?)',
    u'p2':      r'(?:MIDNI(?:GHT|TE)|NOON|[AP]\.? ?M\.?)',
    u'Z':       r"(?:A(?:C(?:DT|ST|T|WST)|DT|E(?:DT|ST)|FT|K(?:DT|ST)|M(?:ST|T)|RT|ST|WST"
                r"|Z(?:O(?:ST|T)|T))|B(?:DT|I(?:OT|T)|OT|R(?:ST|T)|ST|TT)|C(?:AT|CT|DT|E("
                r"?:ST|T)|H(?:A(?:DT|ST)|O(?:ST|T)|ST|UT)|I(?:ST|T)|KT|L(?:ST|T)|O(?:ST|T"
                r")|ST|T|VT|WST|XT)|D(?:AVT|DUT|FT)|E(?:A(?:S(?:ST|T)|T)|CT|DT|E(?:ST|T)|"
                r"G(?:ST|T)|IT|ST)|F(?:ET|JT|K(?:ST|T)|NT)|G(?:A(?:LT|MT)|ET|FT|I(?:LT|T)"
                r"|MT|ST|YT)|H(?:AEC|DT|KT|MT|OV(?:ST|T)|ST)|I(?:CT|D(?:LW|T)|OT|R(?:DT|K"
                r"T|ST)|ST)|JST|K(?:ALT|GT|OST|RAT|ST)|L(?:HST|INT)|M(?:A(?:GT|RT|WT)|DT|"
                r"E(?:ST|T)|HT|I(?:ST|T)|MT|S(?:K|T)|UT|VT|YT)|N(?:CT|DT|FT|PT|ST|T|UT|Z("
                r"?:DT|ST))|O(?:MST|RAT)|P(?:DT|ET(?:T)?|GT|H(?:OT|T)|KT|M(?:DT|ST)|ONT|S"
                r"T|Y(?:ST|T))|R(?:ET|OTT)|S(?:A(?:KT|MT|ST)|BT|CT|DT|GT|LST|R(?:ET|T)|ST"
                r"|YOT)|T(?:AHT|FT|HA|JT|KT|LT|MT|OT|RT|VT)|U(?:LA(?:ST|T)|TC|Y(?:ST|T)|Z"
                r"T)|V(?:ET|LAT|O(?:LT|ST)|UT)|W(?:A(?:KT|ST|T)|E(?:ST|T)|IT|ST)|Y(?:AKT|"
                r"EKT))",  # FROM: en.wikipedia.org/wiki/List_of_time_zone_abbreviations
    u'z':       r"(?:[+-](?:0\d|1[0-4]):?(?:00|15|30|45))",  # [+-] 00:00 to 14:45
    u'A':       r"(?:"
                r"MON(?:DAY)?|(?:IS|SE)N(?:[IE]N)?|"
                r"TUE(?:S(?:DAY)?)?|SEL(?:ASA)?|"
                r"WED(?:NESDAY)?|RABU?|"
                r"THU(?:RS(?:DAY)?)?|KH?A(?:M(?:IS)?)?|"
                r"FRI(?:DAY)?|JUM(?:[AM]A?T)?|"
                r"SAT(?:URDAY)?|SAB(?:TU)?|"
                r"SUN(?:DAY)?|AHA?D|MIN(?:GGU)?"
                r")",
    u'th':      r"(?:ST|ND|RD|TH)",
}
REGEX_PATTERNS_PARSERS = {

    # 14/8/1991
    u'dd_mm_YYYY_1':          r"(?:{d}/{m}/{Y})",
    u'dd_mm_YYYY_2':          r"(?:{d}\\{m}\\{Y})",
    u'dd_mm_YYYY_3':          r"(?:{d}[-]{m}[-]{Y})",
    u'dd_mm_YYYY_4':          r"(?:{d}\.{m}\.{Y})",
    # u'dd_mm_YYYY_5':          r"(?:{d}{m}{Y})",  # too many phone numbers
    u'dd_mm_YYYY_6':          r"(?:{d} ?{m} ?{Y})",
    u'dd_mm_YYYY_7':          r"(?:{dz}{mz}{Y})",

    # 14/8/91
    u'dd_mm_yy_1':            r"(?:{d}/{m}/{y})",
    u'dd_mm_yy_2':            r"(?:{d}\\{m}\\{y})",
    u'dd_mm_yy_3':            r"(?:{d}[-]{m}[-]{y})",
    u'dd_mm_yy_4':            r"(?:{d}\.{m}\.{y})",
    # u'dd_mm_yy_5':            r"(?:{dz}{mz}{y})",  # too many phone numbers

    # 14 Aug, 1991
    u'dd_mmm_YYYY_1':         r"(?:{d}{th}? ?/ ?{B} ?/ ?{Y})",
    u'dd_mmm_YYYY_2':         r"(?:{d}{th}? ?\\ ?{B} ?\\ ?{Y})",
    u'dd_mmm_YYYY_3':         r"(?:{d}{th}? ?[-] ?{B} ?[ -] ?{Y})",
    u'dd_mmm_YYYY_4':         r"(?:{d}{th}? ?[ -]? ?{B} ?,? ?{Y})",
    u'dd_mmm_YYYY_5':         r"(?:{d}{th}? ?\. ?{B} ?\. ?{Y})",

    # 14 Aug '91
    u'dd_mmm_yy_1':           r"(?:{d}{th}? ?/ ?{B} ?/ ?'?{y})",
    u'dd_mmm_yy_2':           r"(?:{d}{th}? ?\\ ?{B} ?\\ ?'?{y})",
    u'dd_mmm_yy_3':           r"(?:{d}{th}? ?[-] ?{B} ?[-] ?'?{y})",
    u'dd_mmm_yy_4':           r"(?:{d}{th}? ?[ -]? ?{B} ?,? ?'?{y})",
    u'dd_mmm_yy_5':           r"(?:{d}{th}? ?\. ?{B} ?\. ?'?{y})",

    # 14th Aug
    u'dd_mmm':                r"(?:{d}{th}? ?[/\\. -] ?{B})",

    # 08/14/1991
    u'mm_dd_YYYY_1':          r"(?:{m}/{d}/{Y})",
    u'mm_dd_YYYY_2':          r"(?:{m}\\{d}\\{Y})",
    u'mm_dd_YYYY_3':          r"(?:{m}[-]{d}[-]{Y})",
    u'mm_dd_YYYY_4':          r"(?:{m} {d} {Y})",
    u'mm_dd_YYYY_5':          r"(?:{m}\.{d}\.{Y})",
    u'mm_dd_YYYY_6':          r"(?:{mz}{dz}{Y})",

    # 8/14/91
    u'mm_dd_yy_1':            r"(?:{m}/{d}/{y})",
    u'mm_dd_yy_2':            r"(?:{m}\\{d}\\{y})",
    u'mm_dd_yy_3':            r"(?:{m}[-]{d}[-]{y})",
    u'mm_dd_yy_4':            r"(?:{m}\.{d}\.{y})",
    # u'mm_dd_yy_5':            r"(?:{mz}{dz}{y})",  # too many phone numbers

    # Aug 14th, 1991
    u'mmm_dd_YYYY_1':         r"(?:{B} ?/ ?{d}{th}? ?/ ?{Y})",
    u'mmm_dd_YYYY_2':         r"(?:{B} ?\\ ?{d}{th}? ?\\ ?{Y})",
    u'mmm_dd_YYYY_3':         r"(?:{B} ?[-] ?{d}{th}? ?[ -] ?{Y})",
    u'mmm_dd_YYYY_4':         r"(?:{B} ?[ -]? ?{d}{th}? ?, ?{Y})",
    u'mmm_dd_YYYY_5':         r"(?:{B} ?\. ?{d}{th}? ?\. ?{Y})",

    # Aug-14 '91
    u'mmm_dd_yy_1':           r"(?:{B} ?/ ?{d}{th}? ?/ ?'?{y})",
    u'mmm_dd_yy_2':           r"(?:{B} ?\\ ?{d}{th}? ?\\ ?'?{y})",
    u'mmm_dd_yy_3':           r"(?:{B} ?[-] ?{d}{th}? ?[-] ?'?{y})",
    u'mmm_dd_yy_4':           r"(?:{B} ?[. -]? ?{d}{th}?, '?{y})",
    u'mmm_dd_yy_5':           r"(?:{B} ?\. ?{d}{th}? ?\. ?'?{y})",

    # Aug-14
    u'mmm_dd':                r"(?:{B} ?[/\\. -] ?{d}{th}?)",

    # # Aug-91
    # u'mmm_yy':                r"(?:{B} ?[/\\. -] ?'{y})",  # too many false positives

    # # August 1991
    # u'mmm_YYYY':              r"(?:{B} ?[/\\. -] ?{Y})",  # too many non-useful dates

    # 1991-8-14
    u'YYYY_mm_dd_1':          r'(?:{Y}/{m}/{d})',
    u'YYYY_mm_dd_2':          r'(?:{Y}\\{m}\\{d})',
    u'YYYY_mm_dd_3':          r'(?:{Y}[-]{m}[-]{d})',
    u'YYYY_mm_dd_4':          r'(?:{Y} {m} {d})',
    u'YYYY_mm_dd_5':          r'(?:{Y}\.{m}\.{d})',
    u'YYYY_mm_dd_6':          r'(?:{Y}{mz}{dz})',

    # 910814 (ISO 8601)
    # u'yy_mm_dd_1':            r"(?:{y} {m} {d})",  # too many random numbers
    u'yy_mm_dd_2':            r"(?:{y}/{m}/{d})",
    u'yy_mm_dd_3':            r"(?:{y}\\{m}\\{d})",
    u'yy_mm_dd_4':            r"(?:{y}[-]{m}[-]{d})",
    u'yy_mm_dd_5':            r"(?:{y}\.{m}\.{d})",
    # u'yy_mm_dd_6':            r"(?:{y}{mz}{dz})",  # too many phone numbers

    # 1991-Aug-14
    u'YYYY_mmm_dd_1':         r"(?:{Y} ?/ ?{B} ?/ ?{d})",
    u'YYYY_mmm_dd_2':         r"(?:{Y} ?\\ ?{B} ?\\ ?{d})",
    u'YYYY_mmm_dd_3':         r"(?:{Y} ?[-] ?{B} ?[-] ?{d})",
    u'YYYY_mmm_dd_4':         r"(?:{Y} ?{B} ?[ -]? ?{d}{th}?)",

    # 1991-Aug-14
    u'yy_mmm_dd_1':           r"(?:'?{y} ?/ ?{B} ?/ ?{d})",
    u'yy_mmm_dd_2':           r"(?:'?{y} ?\\ ?{B} ?\\ ?{d})",
    u'yy_mmm_dd_3':           r"(?:'?{y} ?[-] ?{B} ?[-] ?{d})",
    u'yy_mmm_dd_4':           r"(?:'?{y} ?{B} ?[ -]? ?{d}{th}?)",

    # # 1991.226 (Aug 14 = day 226 in 1991)
    # u'YYYY_ddd_1':            r"(?:{Y}\.{j})",  # too many random numbers
    # u'YYYY_ddd_2':            r"(?:{Y}[-]{j})",  # too many random numbers

    # time
    u'HH_MM_SS':              r"(?:{H}:{M}:{S}(?: ?{p})?(?: ?(?:Z|{Z}|{z}))?)",
    u'HH_MZ_pp_1':            r"(?:{H}:{M}(?: ?{p})?(?: ?(?:Z|{Z}|{z}))?)",
    u'HH_MZ_pp_2':            r"(?:(?<!\.){HZ}[. ]?{M}(?: ?{p})(?: ?(?:Z|{Z}|{z}))?)",
    u'HH_pp':                 r"(?:(?<!\.){H} ?{p2}(?: ?(?:Z|{Z}|{z}))?)",

    # # 910814094500 (9:45am)
    # u'yy_mm_dd_HH_MM_SS':     r"(?:{y}{mz}{dz}{H}{M}{S})",  # too many phone numbers

    # 1991-08-14T09:45:00Z
    u'YYYY_mm_dd_HH_MM':      r"(?:{Y}[-]{m}[-]{d}[T ]{H}:{M}(?: ?(?:Z|{Z}|{z}))?)",
    u'YYYY_mm_dd_HH_MM_SS_1': r"(?:{Y}[-]{m}[-]{d}[T ]{H}:{M}:{S}(?: ?(?:Z|{Z}|{z}))?)",
    u'YYYY_mm_dd_HH_MM_SS_2': r"(?:{Y}{mz}{d}T?{H}{M}{S}(?: ?(?:Z|{Z}|{z}))?)",

    # # standalone
    # u'day':                   r"{A}",  # too many false positives
    # u'month':                 r"{B}",  # too many false positives
    # u'year':                  r"{Y}",  # too many random numbers
    # u'timezone':              r"(?:Z|{Z}|{z})",  # too many malay words
}

#  unicode fixes
REGEX_FORMATTED = {label: u'\\b' +
                          unicode(pattern)
                              .format(**REGEX_PARTS)  # fill in the chunks
                              .replace(u"-]", u"\u2009\u2010\u2011\u2012\u2013\u2014-]")  # unicode dashes
                              .replace(u"'?", u"['\u2018\u2019]?")  # unicode quotes
                          + u'\\b'
                   for label, pattern in REGEX_PATTERNS_PARSERS.items()}

# match emails and urls to avoid returning chunks of them
REGEX_FORMATTED[u'eml'] = r'''[a-zA-Z0-9][^\s`!@%$^={}\[\]/\\"',()<>:;]+@[a-zA-Z0-9][-_a-zA-Z0-9~.]+\.[a-zA-Z]{2,15}'''
REGEX_FORMATTED[u'url'] = r'\b(?:(?:https?|ftp|file)://|www\.|ftp\.)[-A-Z0-9+&@#/%=~_|$?!:,.]*[A-Z0-9+&@#/%=~_|$]'
REGEX_FORMATTED[u'dot'] = r'(?:\d+\.){3,}\d+'

# compile all the regex patterns
REGEX_COMPILED = {label: re.compile(pattern, flags=re.I | re.U) for label, pattern in REGEX_FORMATTED.items()}

HEADERS = [u'PATH',
           u'FILE_ID',
           u'REGEX_LABEL',
           u'LINE_NUM',
           u'MATCH',
           u'START',
           u'END',
           u'MATCH_LEN',
           u'LINE_LEN',
           u'CONTEXT',
           ]


def crawl(top, file_pattern='*'):
    for root_path, dir_list, file_list in scandir.walk(top):
        for file_name in fnmatch.filter(file_list, file_pattern):
            yield os.path.join(root_path, file_name)


def parse_txt(path):
    with io.open(path, mode='r', encoding='utf8') as f:
        return os.path.basename(path), f.readlines()


def parse_json(path):
    with io.open(path, mode='r', encoding='utf8') as f:
        json_obj = json.load(f)

    lines = []
    lines.append(json_obj[u'subject'] + u'\n\n')
    lines.extend(line + u'\n' for line in json_obj[u'content'].split(u'\n'))

    return json_obj[u'recvDocId'], lines


def regex_file(path, parser=parse_json, longest=True, context_max_len=999):
    path = os.path.abspath(path)
    file_name, file_lines = parser(path)  #
    for line_num, line in enumerate(file_lines):

        # join multiple spaces, convert tabs, strip leading/trailing whitespace
        line = u' '.join(line.split())

        # find all matches
        line_matches = []
        for regex_label, regex_obj in REGEX_COMPILED.items():
            for m in regex_obj.finditer(line):
                context_start = max(0, (m.start() + m.end() - context_max_len) // 2)
                context_end = min(len(line), context_start + context_max_len)
                context_str = line[context_start:context_end]
                if context_start != 0:
                    context_str = u'\u2026' + context_str[1:]
                if context_end != len(line):
                    context_str = context_str[:-1] + u'\u2026'
                line_matches.append([path,
                                     file_name,
                                     regex_label,
                                     line_num,
                                     m.group(),
                                     m.start(),
                                     m.end(),
                                     m.end() - m.start(),
                                     len(line),
                                     context_str,
                                     ])

        # narrow to longest match
        for row in line_matches:
            if not longest or all(other[5] >= row[5] and other[6] <= row[6] for other in line_matches):

                # don't return emails or urls
                if row[2] not in {u'eml', u'url', u'dot'}:
                    yield row


if __name__ == '__main__':
    SOURCE_DIR = u'.'
    OUTPUT_CSV = u'found.csv'

    print u'READING FROM:', os.path.abspath(SOURCE_DIR)
    print u'OUTPUT CSV:  ', os.path.abspath(OUTPUT_CSV)

    with open(OUTPUT_CSV, 'wb') as f:
        c = csv.writer(f)
        c.writerow(HEADERS)

        for path in crawl(SOURCE_DIR, '*.txt'):
            print path
            for row in regex_file(path, parser=parse_txt):
                c.writerow([unicode(elem).encode('utf8') for elem in row])

        for path in crawl(SOURCE_DIR, '*.json'):
            print path
            for row in regex_file(path):
                c.writerow([unicode(elem).encode('utf8') for elem in row])
