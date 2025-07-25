import re
from datetime import datetime, timedelta

def is_valid_date_range_filename(filename: str) -> bool:
    # Match pattern like 'CPT Report - 07-06-25 to 07-12-25.xlsx'
    match = re.match(r"CPT Report - (\d{2}-\d{2}-\d{2}) to (\d{2}-\d{2}-\d{2})(?:.*)?\.xlsx$", filename)
    if not match:
        return False

    try:
        start = datetime.strptime(match.group(1), "%m-%d-%y")
        end = datetime.strptime(match.group(2), "%m-%d-%y")
    except ValueError:
        return False

    # Validate that the range is exactly 6 days (i.e., 7 total including start & end)
    if (end - start).days != 6:
        return False

    # Validate start is a Sunday and end is a Saturday
    if start.weekday() != 6 or end.weekday() != 5:
        return False

    return True


# print(is_valid_cpt_filename("CPT Report - 06-08-25 to 06-14-25.xlsx"))
# print(is_valid_cpt_filename("CPT Report - 06-08-25 to 06-14-25.xlsx"))
# print(is_valid_cpt_filename("CPT Report - 02-01-25 to 06-19-25.xlsx"))