import datetime

################# General Utily Functions #################
def last_month():
    """
    Returns a list of the last 31 days including today
    """
    return [datetime.date.today() - datetime.timedelta(days = i)
            for i in range(31)]

def date_range(start_date, end_date):
    """
    Returns a list of the days between startDate and endDate inclusive.
    """
    date_list = []
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    while start_date <= end_date:
        date_list.append(start_date)
        start_date += datetime.timedelta(days = 1)
    return date_list
