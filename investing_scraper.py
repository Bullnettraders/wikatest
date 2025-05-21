import json
import os
import time
from datetime import date, datetime, timedelta
from ai_utils import extract_macro_event_time, extract_earnings_time  # <- deine Hilfsfunktionen

# 🔁 Dateipfade für persistente Speicherung
POSTED_EVENTS_FILE = "posted_events.json"
POSTED_EARNINGS_FILE = "posted_earnings.json"

# 📥 Bereits gepostete Events laden
def load_posted(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return set(tuple(x) for x in json.load(f))
    return set()

# 💾 Speicherung aktualisieren
def save_posted(data, file):
    with open(file, "w") as f:
        json.dump(list(data), f)

# Sets initialisieren
posted_events = load_posted(POSTED_EVENTS_FILE)
posted_earnings = load_posted(POSTED_EARNINGS_FILE)

# Funktionen zum Hinzufügen
def add_posted_event(identifier):
    posted_events.add(identifier)
    save_posted(posted_events, POSTED_EVENTS_FILE)

def add_posted_earning(identifier):
    posted_earnings.add(identifier)
    save_posted(posted_earnings, POSTED_EARNINGS_FILE)

# 🕒 Entscheide anhand der Uhrzeit, ob morgen angezeigt werden soll
def should_fetch_for_tomorrow():
    now = datetime.now()
    return now.hour >= 20  # Nach 20:00 Uhr wird für morgen vorbereitet

# 📅 Wirtschaftskalender (heute oder morgen)
def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '',
            'actual': '6.3%',
            'forecast': '6.1%',
            'previous': '6.5%',
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '',
            'actual': '190k',
            'forecast': '180k',
            'previous': '175k',
        }
    ]

    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].strip().lower() in ['n/a', '-', '', 'unbekannt']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data

# 💰 Earnings Kalender (heute oder morgen)
def get_earnings_calendar(for_tomorrow=False):
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

    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event.get('time') or event['time'].strip().lower() in ['n/a', '-', '', 'unbekannt']:
            description = f"{event['company']} ({event['ticker']}) reports after market close"
            event['time'] = extract_earnings_time(description)

    return dummy_data 

# 📋 Holen der Kalenderdaten mit Vorschau-Logik
def fetch_calendar_data():
    for_tomorrow = should_fetch_for_tomorrow()
    investing_events = get_investing_calendar(for_tomorrow=for_tomorrow)
    earnings_events = get_earnings_calendar(for_tomorrow=for_tomorrow)
    return investing_events, earnings_events

# 🖨️ Ausgabe formatieren
def print_calendar_summary():
    investing_events, earnings_events = fetch_calendar_data()

    print("📅 Wirtschaftstermine:")
    for event in investing_events:
        print(f"{event['date']} - {event['title']} ({event['country'].title()}) um {event['time']}")
        print(f"  Prognose: {event['forecast']}, Vorher: {event['previous']}, Tatsächlich: {event['actual']}\n")

    print("💰 Earnings Releases:")
    for event in earnings_events:
        print(f"{event['date']} - {event['company']} ({event['ticker']}) um {event['time']}")
        print(f"  EPS: {event['eps_actual']} (erwartet: {event['eps_estimate']}), Umsatz: {event['revenue_actual']} Mrd (erwartet: {event['revenue_estimate']} Mrd)\n")

# 🕓 Zeitfenster prüfen (volle und halbe Stunde)
def is_fetch_time(now):
    return now.minute in [0, 30] and now.second < 5  # innerhalb der ersten 5 Sekunden

# 🔁 Hauptloop
def wait_until_next_check():
    already_fetched = False
    print("🚀 Starte Kalender-Überwachung ...")
    while True:
        now = datetime.now()

        if is_fetch_time(now):
            if not already_fetched:
                print(f"\n⏰ Datenabruf um {now.strftime('%H:%M:%S')}")
                print_calendar_summary()
                already_fetched = True
        else:
            already_fetched = False

        time.sleep(1)

if __name__ == "__main__":
    wait_until_next_check()
