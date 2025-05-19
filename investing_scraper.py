from datetime import date, timedelta
from ai_utils import extract_macro_event_time, extract_earnings_time

# Sets für gepostete Ereignisse
posted_events = set()
posted_earnings = set()

# 📅 Wirtschaftskalender (heute oder morgen)
def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '',  # GPT erkennt
            'actual': '6.3%',
            'forecast': '6.1%',
            'previous': '6.5%',
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '',  # GPT erkennt
            'actual': '190k',
            'forecast': '180k',
            'previous': '175k',
        }
    ]

    # Datum setzen
    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    # GPT-Zeiten ergänzen
    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].strip().lower() in ['n/a', '-', '', 'unbekannt']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data

# 💰 Earnings Kalender
def get_earnings_calendar():
    dummy_data = [
        {
            'ticker': 'AAPL',
            'company': 'Apple Inc.',
            'time': '',  # GPT erkennt
            'eps_actual': '1,45',
            'eps_estimate': '1,39',
            'revenue_actual': '81,2',
            'revenue_estimate': '79,5',
        }
    ]

    date_str = date.today().strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].strip().lower() in ['n/a', '-', '', 'unbekannt']:
            description = f"{event['company']} ({event['ticker']}) reports after market close"
            event['time'] = extract_earnings_time(description)

    return dummy_data
