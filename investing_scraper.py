from datetime import date, timedelta
from ai_utils import extract_macro_event_time, extract_earnings_time

posted_events = set()
posted_earnings = set()

def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'EZB Zinsentscheid',
            'country': 'germany',
            'time': '',  # Wird durch GPT gesetzt
            'actual': '',
            'forecast': '3.50%',
            'previous': '3.25%',
        },
        {
            'title': 'US Arbeitsmarktdaten',
            'country': 'united states',
            'time': '',
            'actual': '',
            'forecast': '5.0%',
            'previous': '4.8%',
        }
    ]

    today = date.today()
    event_date = today + timedelta(days=1 if for_tomorrow else 0)
    date_str = event_date.strftime("%d.%m.%Y")

    for event in dummy_data:
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])
        event['date'] = date_str

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
        },
        {
            'ticker': 'MSFT',
            'company': 'Microsoft Corp.',
            'time': '',
            'eps_actual': '2,17',
            'eps_estimate': '2,00',
            'revenue_actual': '56,0',
            'revenue_estimate': '54,2',
        }
    ]

    date_str = date.today().strftime("%d.%m.%Y")

    for event in dummy_data:
        if not event['time']:
            description = f"{event['company']} ({event['ticker']}) reports after market close"
            event['time'] = extract_earnings_time(description)
        event['date'] = date_str

    return dummy_data
