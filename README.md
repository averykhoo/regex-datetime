#   regex-datetime
use regex (`re`) and `dateutil` to find datetimes in text

##  notes
-   run `constants.py` to build regex for months/days/etc
    -   contains english and bahasa words for months/days
    -   should be straightforward to add more languages
-   run `regex_datetime.py` to find dates (like 2018-01-01 or 12th Oct 2018)
    -   open the resulting csv to find the hits
-   supports dates from 1940 to 2039 (regex can be edited)

-   datetime parsed via dateutil 
    -   not super accurate, maybe i should try `arrow`/`moment`/`maya`/`delorean`/`dateparser`

##  todo
-   use named capturing patterns
    -   use named groups to rebuild datetime, don't use dateutil
