# regex-datetime
use regex to find datetimes in text

## notes
-   run `constants.py` to build regex for months/days/etc
    -   contains english and bahasa words for months/days
    -   should be straightforward to add more languages
-   run `regex_datetime.py` to find dates (like 2018-01-01 or 12th Oct 2018)
    -   open the resulting csv to find the hits
-   supports dates from 1940 to 2039 (regex can be edited)
-   you can use dateutil (or arrow or moment or maya or delorean or dateparser)


## Todo
-   find month-year (january 2019)
-   parse into iso8601