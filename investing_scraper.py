import json
import os
from datetime import date, timedelta
from ai_utils import extract_macro_event_time

POSTED_EVENTS_FILE = "posted_events.json"

def load_posted():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(tuple(x) for x in json.load(f))
    return set()

def save_posted(posted_events):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted_events), f)

posted_events = load_posted()

def add_posted_event(identifier):
    posted_events.add(identifier)
    save_posted(posted_events)

def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '',
            'actual': '',
            'forecast': '6.1%',
            'previous': '6.5%',
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '',
            'actual': '',
            'forecast': '180k',
            'previous': '175k',
        }
    ]
    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")

    for event in dummy_data:
        event['date'] = date_str
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])

    return dummy_data

async def post_today_events(bot, channel_id):
    events = get_investing_calendar()
    channel = bot.get_channel(channel_id)
    for event in events:
        identifier = (event['title'], event['date'], event['country'])
        if identifier not in posted_events:
            msg = f"📊 {event['title']} ({event['country'].capitalize()})\n" \
                  f"Zeit: {event['time']} | Prognose: {event['forecast']} | Vorher: {event['previous']}"
            await channel.send(msg)
            add_posted_event(identifier)

async def check_for_actual_updates(bot, channel_id):
    events = get_investing_calendar()
    channel = bot.get_channel(channel_id)
    for event in events:
        identifier = (event['title'], event['date'], event['country'])
        if event['actual'] and identifier not in posted_events:
            msg = f"✅ Zahlen veröffentlicht: {event['title']} ({event['country'].capitalize()})\n" \
                  f"Ergebnis: {event['actual']} | Prognose: {event['forecast']} | Vorher: {event['previous']}"
            await channel.send(msg)
            add_posted_event(identifier)
