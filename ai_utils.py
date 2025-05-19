import os
from openai import OpenAI

# GPT-Client initialisieren (ab v1.0)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_macro_event_time(text, country="Germany"):
    prompt = f"""
Du bist ein KI-Assistent für Finanzdaten. Bestimme die typische Veröffentlichungszeit (MEZ, 24h) für folgendes Wirtschaftsevent in {country}, wenn möglich.

TEXT:
{text}

Antwort im Format „HH:MM Uhr“. Wenn unklar, antworte mit „unbekannt“.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT-Fehler:", e)
        return "unbekannt"

def extract_earnings_time(text):
    prompt = f"""
Du bist ein Finanzassistent. Erkenne aus folgendem Text die typische Veröffentlichungszeit in MEZ (24h-Format).

TEXT:
{text}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT-Fehler:", e)
        return "unbekannt"
