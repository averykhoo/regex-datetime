import csv
import io
import os
import re

REGEX_PARTS = {

    'Y':       r"(?:19[4-9]\d|20[0-3]\d)",  # 1940 to 2039
    'y':       r"(?:\d\d)",  # 00 to 99
    'm':       r"(?:1[012]|0?[1-9])",  # 0?1 to 12
    'mz':      r"(?:1[012]|0[1-9])",  # 01 to 12
    'B':       r"(?:"
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
    'd':       r"(?:3[01]|[12]\d|0?[1-9])",  # 0?1 to 31
    'd_range': r"(?:3[01]|[12]\d|0?[1-9])(?: ?[-] ?(?:3[01]|[12]\d|0?[1-9]))?",  # 14-15
    'dz':      r"(?:3[01]|[12]\d|0[1-9])",  # 01 to 31
    'j':       r"(?:36[0-6]|3[0-5]\d|[12]\d\d|0?[1-9]\d|0?0?[1-9])",  # 0?0?1 to 366
    'H':       r"(?:2[0-4]|[01]?\d)",  # 0?0 to 24
    'HZ':      r"(?:2[0-4]|[01]\d)",  # 0?0 to 24
    'I':       r"(?:1[012]|0?[1-9])",  # 0?1 to 12
    'M':       r"(?:[1-5]\d|0\d)",  # 00 to 59
    'S':       r"(?:6[01]|[0-5]\d)",  # 00 to 61 (leap second)
    'p':       r'(?:MIDNI(?:GHT|TE)|AFTERNOON|MORNING|NOON|[MN]N|H(?:(?:OU)?RS?)?|[AP]\.? ?M\.?)',
    'p2':      r'(?:MIDNI(?:GHT|TE)|NOON|[AP]\.? ?M\.?)',
    'Z':       r"(?:A(?:C(?:DT|ST|T|WST)|DT|E(?:DT|ST)|FT|K(?:DT|ST)|M(?:ST|T)|RT|ST|WST"
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
    'z':       r"(?:[+-](?:0\d|1[0-4]):?(?:00|15|30|45))",  # [+-] 00:00 to 14:45
    'A':       r"(?:"
               r"MON(?:DAY)?|(?:IS|SE)N(?:[IE]N)?|"
               r"TUE(?:S(?:DAY)?)?|SEL(?:ASA)?|"
               r"WED(?:NESDAY)?|RABU?|"
               r"THU(?:RS(?:DAY)?)?|KH?A(?:M(?:IS)?)?|"
               r"FRI(?:DAY)?|JUM(?:[AM]A?T)?|"
               r"SAT(?:URDAY)?|SAB(?:TU)?|"
               r"SUN(?:DAY)?|AHA?D|MIN(?:GGU)?"
               r")",
    'th':      r"(?:ST|ND|RD|TH)",
}
REGEX_PATTERNS_PARSERS = {

    # 14/8/1991
    'dd_mm_YYYY_1':          r"(?:{d}/{m}/{Y})",
    'dd_mm_YYYY_2':          r"(?:{d}\\{m}\\{Y})",
    'dd_mm_YYYY_3':          r"(?:{d}[-]{m}[-]{Y})",
    'dd_mm_YYYY_4':          r"(?:{d}\.{m}\.{Y})",
    # 'dd_mm_YYYY_5':          r"(?:{d}{m}{Y})",  # too many phone numbers
    'dd_mm_YYYY_6':          r"(?:{d} ?{m} ?{Y})",
    'dd_mm_YYYY_7':          r"(?:{dz}{mz}{Y})",

    # 14/8/91
    'dd_mm_yy_1':            r"(?:{d}/{m}/{y})",
    'dd_mm_yy_2':            r"(?:{d}\\{m}\\{y})",
    'dd_mm_yy_3':            r"(?:{d}[-]{m}[-]{y})",
    'dd_mm_yy_4':            r"(?:{d}\.{m}\.{y})",
    # 'dd_mm_yy_5':            r"(?:{dz}{mz}{y})",  # too many phone numbers

    # 14 Aug, 1991
    'dd_mmm_YYYY_1':         r"(?:{d}{th}? ?/ ?{B} ?/ ?{Y})",
    'dd_mmm_YYYY_2':         r"(?:{d}{th}? ?\\ ?{B} ?\\ ?{Y})",
    'dd_mmm_YYYY_3':         r"(?:{d}{th}? ?[-] ?{B} ?[ -] ?{Y})",
    'dd_mmm_YYYY_4':         r"(?:{d}{th}? ?[ -]? ?{B} ?,? ?{Y})",
    'dd_mmm_YYYY_5':         r"(?:{d}{th}? ?\. ?{B} ?\. ?{Y})",

    # 14 Aug '91
    'dd_mmm_yy_1':           r"(?:{d}{th}? ?/ ?{B} ?/ ?'?{y})",
    'dd_mmm_yy_2':           r"(?:{d}{th}? ?\\ ?{B} ?\\ ?'?{y})",
    'dd_mmm_yy_3':           r"(?:{d}{th}? ?[-] ?{B} ?[-] ?'?{y})",
    'dd_mmm_yy_4':           r"(?:{d}{th}? ?[ -]? ?{B} ?,? ?'?{y})",
    'dd_mmm_yy_5':           r"(?:{d}{th}? ?\. ?{B} ?\. ?'?{y})",

    # 14th Aug
    'dd_mmm':                r"(?:{d}{th}? ?[/\\. -] ?{B})",

    # 08/14/1991
    'mm_dd_YYYY_1':          r"(?:{m}/{d}/{Y})",
    'mm_dd_YYYY_2':          r"(?:{m}\\{d}\\{Y})",
    'mm_dd_YYYY_3':          r"(?:{m}[-]{d}[-]{Y})",
    'mm_dd_YYYY_4':          r"(?:{m} {d} {Y})",
    'mm_dd_YYYY_5':          r"(?:{m}\.{d}\.{Y})",
    'mm_dd_YYYY_6':          r"(?:{mz}{dz}{Y})",

    # 8/14/91
    'mm_dd_yy_1':            r"(?:{m}/{d}/{y})",
    'mm_dd_yy_2':            r"(?:{m}\\{d}\\{y})",
    'mm_dd_yy_3':            r"(?:{m}[-]{d}[-]{y})",
    'mm_dd_yy_4':            r"(?:{m}\.{d}\.{y})",
    # 'mm_dd_yy_5':            r"(?:{mz}{dz}{y})",  # too many phone numbers

    # Aug 14th, 1991
    'mmm_dd_YYYY_1':         r"(?:{B} ?/ ?{d}{th}? ?/ ?{Y})",
    'mmm_dd_YYYY_2':         r"(?:{B} ?\\ ?{d}{th}? ?\\ ?{Y})",
    'mmm_dd_YYYY_3':         r"(?:{B} ?[-] ?{d}{th}? ?[ -] ?{Y})",
    'mmm_dd_YYYY_4':         r"(?:{B} ?[ -]? ?{d}{th}? ?, ?{Y})",
    'mmm_dd_YYYY_5':         r"(?:{B} ?\. ?{d}{th}? ?\. ?{Y})",

    # Aug-14 '91
    'mmm_dd_yy_1':           r"(?:{B} ?/ ?{d}{th}? ?/ ?'?{y})",
    'mmm_dd_yy_2':           r"(?:{B} ?\\ ?{d}{th}? ?\\ ?'?{y})",
    'mmm_dd_yy_3':           r"(?:{B} ?[-] ?{d}{th}? ?[-] ?'?{y})",
    'mmm_dd_yy_4':           r"(?:{B} ?[. -]? ?{d}{th}?, '?{y})",
    'mmm_dd_yy_5':           r"(?:{B} ?\. ?{d}{th}? ?\. ?'?{y})",

    # Aug-14
    'mmm_dd':                r"(?:{B} ?[/\\. -] ?{d}{th}?)",

    # # Aug-91
    # 'mmm_yy':                r"(?:{B} ?[/\\. -] ?'{y})",  # too many false positives

    # # August 1991
    # 'mmm_YYYY':              r"(?:{B} ?[/\\. -] ?{Y})",  # too many non-useful dates

    # 1991-8-14
    'YYYY_mm_dd_1':          r'(?:{Y}/{m}/{d})',
    'YYYY_mm_dd_2':          r'(?:{Y}\\{m}\\{d})',
    'YYYY_mm_dd_3':          r'(?:{Y}[-]{m}[-]{d})',
    'YYYY_mm_dd_4':          r'(?:{Y} {m} {d})',
    'YYYY_mm_dd_5':          r'(?:{Y}\.{m}\.{d})',
    'YYYY_mm_dd_6':          r'(?:{Y}{mz}{dz})',

    # 910814 (ISO 8601)
    # 'yy_mm_dd_1':            r"(?:{y} {m} {d})",  # too many random numbers
    'yy_mm_dd_2':            r"(?:{y}/{m}/{d})",
    'yy_mm_dd_3':            r"(?:{y}\\{m}\\{d})",
    'yy_mm_dd_4':            r"(?:{y}[-]{m}[-]{d})",
    'yy_mm_dd_5':            r"(?:{y}\.{m}\.{d})",
    # 'yy_mm_dd_6':            r"(?:{y}{mz}{dz})",  # too many phone numbers

    # 1991-Aug-14
    'YYYY_mmm_dd_1':         r"(?:{Y} ?/ ?{B} ?/ ?{d})",
    'YYYY_mmm_dd_2':         r"(?:{Y} ?\\ ?{B} ?\\ ?{d})",
    'YYYY_mmm_dd_3':         r"(?:{Y} ?[-] ?{B} ?[-] ?{d})",
    'YYYY_mmm_dd_4':         r"(?:{Y} ?{B} ?[ -]? ?{d}{th}?)",

    # 1991-Aug-14
    'yy_mmm_dd_1':           r"(?:'?{y} ?/ ?{B} ?/ ?{d})",
    'yy_mmm_dd_2':           r"(?:'?{y} ?\\ ?{B} ?\\ ?{d})",
    'yy_mmm_dd_3':           r"(?:'?{y} ?[-] ?{B} ?[-] ?{d})",
    'yy_mmm_dd_4':           r"(?:'?{y} ?{B} ?[ -]? ?{d}{th}?)",

    # # 1991.226 (Aug 14 = day 226 in 1991)
    # 'YYYY_ddd_1':            r"(?:{Y}\.{j})",  # too many random numbers
    # 'YYYY_ddd_2':            r"(?:{Y}[-]{j})",  # too many random numbers

    # time
    'HH_MM_SS':              r"(?:{H}:{M}:{S}(?: ?{p})?(?: ?(?:Z|{Z}|{z}))?)",
    'HH_MZ_pp_1':            r"(?:{H}:{M}(?: ?{p})?(?: ?(?:Z|{Z}|{z}))?)",
    'HH_MZ_pp_2':            r"(?:(?<!\.){HZ}[. ]?{M}(?: ?{p})(?: ?(?:Z|{Z}|{z}))?)",
    'HH_pp':                 r"(?:(?<!\.){H} ?{p2}(?: ?(?:Z|{Z}|{z}))?)",

    # # 910814094500 (9:45am)
    # 'yy_mm_dd_HH_MM_SS':     r"(?:{y}{mz}{dz}{H}{M}{S})",  # too many phone numbers

    # 1991-08-14T09:45:00Z
    'YYYY_mm_dd_HH_MM':      r"(?:{Y}[-]{m}[-]{d}[T ]{H}:{M}(?: ?(?:Z|{Z}|{z}))?)",
    'YYYY_mm_dd_HH_MM_SS_1': r"(?:{Y}[-]{m}[-]{d}[T ]{H}:{M}:{S}(?: ?(?:Z|{Z}|{z}))?)",
    'YYYY_mm_dd_HH_MM_SS_2': r"(?:{Y}{mz}{d}T?{H}{M}{S}(?: ?(?:Z|{Z}|{z}))?)",

    # # standalone
    # 'day':                   r"{A}",  # too many false positives
    # 'month':                 r"{B}",  # too many false positives
    # 'year':                  r"{Y}",  # too many random numbers
    # 'timezone':              r"(?:Z|{Z}|{z})",  # too many malay words
}

#  unicode fixes
REGEX_FORMATTED = {label: '\\b' +
                          pattern
                              .format(**REGEX_PARTS)  # fill in the chunks
                              .replace("-]", "\u2009\u2010\u2011\u2012\u2013\u2014-]")  # unicode dashes
                              .replace("'?", "['\u2018\u2019]?")  # unicode quotes
                          + '\\b'
                   for label, pattern in REGEX_PATTERNS_PARSERS.items()}

# match emails and urls to avoid returning chunks of them
REGEX_FORMATTED['eml'] = r'''[a-zA-Z0-9][^\s`!@%$^={}\[\]/\\"',()<>:;]+@[a-zA-Z0-9][-_a-zA-Z0-9~.]+\.[a-zA-Z]{2,15}'''
REGEX_FORMATTED['url'] = r'\b(?:(?:https?|ftp|file)://|www\.|ftp\.)[-A-Z0-9+&@#/%=~_|$?!:,.]*[A-Z0-9+&@#/%=~_|$]'
REGEX_FORMATTED['dot'] = r'(?:\d+\.){3,}\d+'

# compile all the regex patterns
REGEX_COMPILED = {label: re.compile(pattern, flags=re.I | re.U) for label, pattern in REGEX_FORMATTED.items()}

HEADERS = ['PATH',
           'FILE_ID',
           'REGEX_LABEL',
           'LINE_NUM',
           'MATCH',
           'START',
           'END',
           'MATCH_LEN',
           'NORM_LINE_LEN',
           'CONTEXT',
           ]


def parse_txt(path):
    with io.open(path, mode='r', encoding='utf8') as f:
        return os.path.basename(path), f.readlines()


def regex_text(text, longest=True, context_max_len=999):
    # join multiple spaces, convert tabs, strip leading/trailing whitespace
    text = ' '.join(text.split())
    matches = []

    for regex_label, regex_obj in REGEX_COMPILED.items():
        for m in regex_obj.finditer(text):

            context_start = max(0, (m.start() + m.end() - context_max_len) // 2)
            context_end = min(len(text), context_start + context_max_len)

            context_str = text[context_start:context_end]

            if context_start != 0:
                context_str = '\u2026' + context_str[1:]
            if context_end != len(text):
                context_str = context_str[:-1] + '\u2026'  # this is the `...` character

            matches.append({'REGEX_LABEL':   regex_label,
                            'MATCH':         m.group(),
                            'START':         m.start(),
                            'END':           m.end(),
                            'MATCH_LEN':     m.end() - m.start(),
                            'NORM_TEXT_LEN': len(text),
                            'CONTEXT':       context_str,
                            })

    # narrow to longest match
    for match in matches:
        if not longest or all((other['START'] >= match['START'] and other['END'] <= match['END']) or
                              other['START'] > match['END'] or
                              other['END'] < match['START']
                              for other in matches):

            # don't return emails or urls
            if match['REGEX_LABEL'] not in {u'eml', 'url', 'dot'}:
                yield match


def regex_file(path, parser=parse_txt):
    path = os.path.abspath(path)
    file_name, file_lines = parser(path)  #
    for line_num, line in enumerate(file_lines):
        for match_info in regex_text(line):
            yield [path,
                   file_name,
                   match_info['REGEX_LABEL'],
                   line_num,
                   match_info['MATCH'],
                   match_info['START'],
                   match_info['END'],
                   match_info['MATCH_LEN'],
                   match_info['NORM_TEXT_LEN'],
                   match_info['CONTEXT'],
                   ]


if __name__ == '__main__':
    SOURCE_FILES = ['regex_datetime_test.txt', 'README.md']
    OUTPUT_CSV = 'found.csv'

    with io.open(OUTPUT_CSV, mode='w', encoding='utf8', newline='') as f:
        c = csv.writer(f)
        c.writerow(HEADERS)

        for path in SOURCE_FILES:
            print('READING FROM:', os.path.abspath(path))

            for row in regex_file(path):
                c.writerow(row)

    print('OUTPUT CSV:  ', os.path.abspath(OUTPUT_CSV))
