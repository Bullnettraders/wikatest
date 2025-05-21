import json
import os
from datetime import date, timedelta
from ai_utils import extract_macro_event_time

POSTED_EVENTS_FILE = "posted_events.json"

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

# Set initialisieren
posted_events = load_posted(POSTED_EVENTS_FILE)

# Hinzufügen von Event-Markierungen
def add_posted_event(identifier):
    posted_events.add(identifier)
    save_posted(posted_events, POSTED_EVENTS_FILE)

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
