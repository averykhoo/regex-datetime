#   regex-datetime
*   use regex (`re`) and `dateutil` to find datetimes in text
*   you almost certainly want to use a real library like `ctparse` or `dateparser` instead
*   does not support date ranges (e.g. "12-15 May 2021")
*   does not support time ranges (e.g. "1200-1530pm")
*   does not support month-only references (e.g. "March 2019")
*   does not support quarter-year references (e.g. "Q1 FY 2001")

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
-   drop dateutil? (maybe try `arrow`/`moment`/`maya`/`delorean`/`dateparser`)
