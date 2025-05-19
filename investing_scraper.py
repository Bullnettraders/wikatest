from datetime import date, timedelta
from ai_utils import extract_macro_event_time, extract_earnings_time

posted_events = set()
posted_earnings = set()

def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'EZB Zinsentscheid',
            'country': 'germany',
            'time': '',
            'actual': '',
            'forecast': '3.50%',
            'previous': '3.25%',
        }
    ]

    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    for event in dummy_data:
        event['date'] = target_date.strftime("%d.%m.%Y")
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], event['country'])
    return dummy_data

def get_earnings_calendar():
    dummy_data = [
        {
            'ticker': 'AAPL',
            'company': 'Apple Inc.',
            'time': '',
            'eps_actual': '1,45',
            'eps_estimate': '1,39',
            'revenue_actual': '81,2',
            'revenue_estimate': '79,5',
        }
    ]
    today_str = date.today().strftime("%d.%m.%Y")
    for event in dummy_data:
        event['date'] = today_str
        if not event['time']:
            event['time'] = extract_earnings_time(f"{event['company']} reports after market close")
    return dummy_data
