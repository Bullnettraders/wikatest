from datetime import date, timedelta
from ai_utils import extract_macro_event_time, extract_earnings_time

# Verhindert doppelte Meldungen
posted_events = set()
posted_earnings = set()

def get_investing_calendar(for_tomorrow=False):
    # ✳ Beispiel-Daten: Du kannst später echte Scraper einsetzen
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '',  # GPT soll ergänzen
            'actual': '6.3%',
            'forecast': '6.1%',
            'previous': '6.5%',
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '',  # GPT soll ergänzen
            'actual': '190k',
            'forecast': '180k',
            'previous': '175k',
        }
    ]

    # Datum korrekt setzen
    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    # GPT-Zeitergänzung
    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].lower() in ['n/a', '-', '', 'unbekannt']:
            # GPT AUFRUF
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data


def get_earnings_calendar():
    dummy_data = [
        {
            'ticker': 'AAPL',
            'company': 'Apple Inc.',
            'time': '',  # GPT soll ergänzen
            'eps_actual': '1,45',
            'eps_estimate': '1,39',
            'revenue_actual': '81,2',
            'revenue_estimate': '79,5',
        }
    ]

    date_str = date.today().strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].lower() in ['n/a', '-', '', 'unbekannt']:
            description = f"{event['company']} ({event['ticker']}) reports after market close"
            event['time'] = extract_earnings_time(description)

    return dummy_data
