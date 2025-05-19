from ai_utils import extract_macro_event_time, extract_earnings_time

posted_events = set()
posted_earnings = set()

# Wirtschaftskalender (Dummy)
def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'EZB Zinsentscheid',
            'country': 'germany',
            'time': '',  # Wird durch AI gesetzt
            'actual': '3,75',
            'forecast': '3,50',
            'previous': '3,25',
        }
    ]

    for event in dummy_data:
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data

# Earnings (Dummy)
def get_earnings_calendar():
    dummy_data = [
        {
            'ticker': 'AAPL',
            'company': 'Apple Inc.',
            'time': '',  # Wird durch AI gesetzt
            'eps_actual': '1,45',
            'eps_estimate': '1,39',
            'revenue_actual': '81,2',
            'revenue_estimate': '79,5',
        }
    ]

    for event in dummy_data:
        if not event['time']:
            description = f"{event['company']} ({event['ticker']}) reports after market close"
            event['time'] = extract_earnings_time(description)

    return dummy_data
