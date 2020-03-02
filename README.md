#   regex-datetime
use regex (`re`) and `dateutil` to find datetimes in text

##  notes
-   run `constants.py` to build regex for months/days/etc
    -   contains english and bahasa words for months/days
    -   should be straightforward to add more languages
-   run `regex_datetime.py` to find dates (like 2018-01-01 or 12th Oct 2018)
    -   open the resulting csv to find the hits
-   short dates (dd/mm/yy) default to the year range 1940-2039 (regex can be edited)


##  todo
-   use named capturing patterns
    -   use named groups to rebuild datetime, don't use dateutil
-   drop dateutil (try `arrow`/`moment`/`maya`/`delorean`/`dateparser`)
