#!/usr/bin/python3
import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from icalendar import Calendar
from decouple import config
from datetime import datetime, date
import pytz
import urllib3

# SSL-Warnungen unterdrücken
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Konfigurations-ENV abrufen
smtp_server = config('SMTP_HOST')
smtp_port = config('SMTP_PORT', cast=int)
smtp_username = config('SMTP_USERNAME')
smtp_password = config('SMTP_PASSWORD')
sender_email = config('SENDER_EMAIL')
sender_name = config('SENDER_NAME')
to_email = [email.strip() for email in config('RECEIVER_EMAIL_OVERVIEW').split(',')]
ics_urls = [url.strip() for url in config('ICS_URL_OVERVIEW').split(',')]
old_ics_path_template = config('OLD_ICS_PATH_TEMPLATE', default='old_{}.ics')
new_ics_path_template = config('NEW_ICS_PATH_TEMPLATE', default='new_{}.ics')
template_file_path = config('TEMPLATE_OVERVIEW_PATH', default='template_overview.html')
local_timezone = config('TIMEZONE', default='Europe/Berlin')
DATE_FORMAT = config("DATE_FORMAT", default='%d.%m.%Y ⋅ %H:%M Uhr') # US-Format: '%m/%d/%Y ⋅ %I:%M %p'
language = config('LANGUAGE', default='EN')

# Test-Mode aktivieren (True) oder deaktivieren (False)
TEST_MODE = False

# Wörterbuch für die Texte
texts = {
    'DE': {
        'subject': "Ihre Kalenderaktualisierungen",
        'header': "Termin-Übersicht",
        'added': "Hinzugefügte Termine:",
        'modified': "Geänderte Termine:",
        'removed': "Entfernte Termine:",
        'event': "Termin:",
        'start': "Start:",
        'end': "Ende:",
        'location': "Ort:",
        'changes': "Änderungen:",
        'footer': "Diese E-Mail wurde automatisch generiert. Bitte nicht antworten."
    },
    'EN': {
        'subject': "Your calendar updates",
        'header': "Event Overview",
        'added': "Added events:",
        'modified': "Modified events:",
        'removed': "Removed events:",        
        'event': "Event:",
        'start': "Start:",
        'end': "End:",
        'location': "Location:",
        'changes': "Changes:",
        'footer': "This email was automatically generated. Please do not reply."
    }
}

# Wähle die Texte basierend auf der Sprache aus
selected_texts = texts.get(language, texts['EN'])  # Fallback auf Englisch, wenn die Sprache nicht gefunden wird
field_labels = {
    'SUMMARY': selected_texts['event'].replace(':', ''),
    'DTSTART': selected_texts['start'].replace(':', ''),
    'DTEND': selected_texts['end'].replace(':', ''),
    'LOCATION': selected_texts['location'].replace(':', '')
}

# Funktion zum Herunterladen der ICS-Datei
def download_ics(url, path):
    response = requests.get(url, verify=False)
    with open(path, 'wb') as file:
        file.write(response.content)

# Funktion zum Lesen der ICS-Datei
def read_ics(path):
    with open(path, 'rb') as file:
        return Calendar.from_ical(file.read())

# Funktion zum Lokalisieren von Datumsangaben
def localize_datetime(dt):
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime.combine(dt, datetime.min.time())
    return dt if dt.tzinfo else pytz.timezone(local_timezone).localize(dt)

# Funktion zum Extrahieren von Event-Details
def extract_event_details(event):
    return {
        'start': localize_datetime(event.get('DTSTART').dt),
        'end': localize_datetime(event.get('DTEND').dt if event.get('DTEND') else None),
        'summary': event.get('SUMMARY'),
        'location': event.get('LOCATION')
    }

# Funktion zum Formatieren der Events-Liste
def format_events(events, changes=None):
    return ''.join(
        format_event_details(extract_event_details(event), changes[i] if changes else [])
        + ('<hr size="1" />' if i < len(events) - 1 else '')
        for i, event in enumerate(events)
    )

# Funktion zum Formatieren von Event-Details
def format_event_details(event, changes):
    start = event['start'].astimezone(pytz.timezone(local_timezone)).strftime(DATE_FORMAT)
    end = event['end'].astimezone(pytz.timezone(local_timezone)).strftime(DATE_FORMAT) if event['end'] else 'N/A'
    summary = event['summary']
    location = event['location'] if event['location'] else 'N/A'
    
    change_text = ''
    if changes:
        change_text = f'<div style="padding-left: 20px;"><span class="symbol">✏️</span><i><strong>{selected_texts["changes"]}</strong> {", ".join(changes)}</i></div>'

    location_text = ''
    if location != 'N/A':
        location_text = f'<div style="padding-left: 20px;"><span class="symbol">📍</span><strong>{selected_texts["location"]}</strong>&nbsp;<span>{location}</span></div>'
    return (f'<div style="padding-left: 20px;"><span class="symbol">📅</span><strong>{selected_texts["event"]}</strong>&nbsp;<span>{summary}</span></div>'
            f'<div style="padding-left: 20px;"><span class="symbol">⏰</span><strong>{selected_texts["start"]}</strong>&nbsp;<span>{start}</span></div>'
            f'<div style="padding-left: 20px;"><span class="symbol">⏰</span><strong>{selected_texts["end"]}</strong>&nbsp;<span>{end}</span></div>'
            f'{location_text}'
            f'{change_text}')



# Funktion zum Generieren des E-Mail-Bodys
def generate_email_body(added, removed, modified):
    with open(template_file_path, 'r') as file:
        template = file.read()

    added_events = f"<h3>{selected_texts['added']}</h3>{format_events(added)}" if added else ""
    removed_events = f"<h3>{selected_texts['removed']}</h3>{format_events(removed)}" if removed else ""
    modified_events = f"<h3>{selected_texts['modified']}</h3>{format_events([e['event'] for e in modified], [e['changes'] for e in modified])}" if modified else ""

    body = template.replace("{{lang}}", "de" if language == "DE" else "en")\
                   .replace("{{header}}", selected_texts['header'])\
                   .replace("{{footer}}", selected_texts['footer'])\
                   .replace("{{added_events}}", added_events)\
                   .replace("{{removed_events}}", removed_events)\
                   .replace("{{modified_events}}", modified_events)

    return body

def save_html_to_file(body):
    # Erhalte die aktuelle Zeit mit Millisekunden
    current_time = datetime.now().strftime("%Y%m%d%H%M%S%f")
    # Erzeuge den Dateinamen mit angehängten Millisekunden
    file_name = f"calendar-overview_{current_time}.html"
    # Speichere die Datei
    with open(file_name, "w") as file:
        file.write(body)
    print(f"HTML-Datei erfolgreich gespeichert als {file_name}.")

# Funktion zum Extrahieren des Kalendernamens
def extract_calendar_name(calendar):
    return calendar.get('X-WR-CALNAME', 'Unbekannter Kalender')

# Funktion zum Senden der E-Mail
def send_email(added, removed, modified, calendar_name):
    body = generate_email_body(added, removed, modified)

    if TEST_MODE:
        save_html_to_file(body)
    else:
        msg = MIMEText(body, 'html')
        msg['Subject'] = f'{selected_texts["subject"]} ({calendar_name})'
        msg['From'] = formataddr((sender_name, sender_email))
        msg['To'] = ', '.join(to_email)
        msg['Date'] = formatdate(localtime=True)

        try:
            if smtp_port == 587:
                # Verwende STARTTLS für Port 587
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls() 
                    server.login(smtp_username, smtp_password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            else:
                # Verwende SSL für alle anderen Ports
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(smtp_username, smtp_password)
                    server.sendmail(sender_email, to_email, msg.as_string())
            print("E-Mail erfolgreich verschickt.")
        except Exception as e:
            print(f"Fehler beim Versenden der E-Mail: {e}")

# Funktion zum Vergleichen der Kalender
def compare_calendars(old_cal, new_cal):
    old_events = {e.get('UID'): e for e in old_cal.subcomponents if e.name == 'VEVENT'}
    new_events = {e.get('UID'): e for e in new_cal.subcomponents if e.name == 'VEVENT'}

    added = [e for uid, e in new_events.items() if uid not in old_events]
    removed = [e for uid, e in old_events.items() if uid not in new_events]
    modified = []
    for uid in new_events:
        if uid in old_events:
            changes = events_are_equal(old_events[uid], new_events[uid])
            if changes:
                modified.append({'event': new_events[uid], 'changes': changes})

    return added, removed, modified

# Funktion zum Vergleichen der Events
def events_are_equal(event1, event2):  
    return [field_labels[field] for field in ['SUMMARY', 'DTSTART', 'DTEND', 'LOCATION'] if event1.get(field) != event2.get(field)]

# Hauptfunktion
def main():
    for ics_url in ics_urls:
        sanitized_url = ics_url.replace("https://", "").replace("/", "_").replace(".ics", "")
        truncated_url = sanitized_url[-35:]  # Kürze auf maximal 40 Zeichen von hinten
        old_ics_path = old_ics_path_template.format(truncated_url)
        new_ics_path = new_ics_path_template.format(truncated_url)
        
        download_ics(ics_url, new_ics_path)

        if not os.path.exists(old_ics_path):
            os.rename(new_ics_path, old_ics_path)
            print(f"Alte ICS-Datei nicht gefunden. Neue Datei gespeichert.")
            continue

        old_cal = read_ics(old_ics_path)
        new_cal = read_ics(new_ics_path)

        added, removed, modified = compare_calendars(old_cal, new_cal)
        calendar_name = extract_calendar_name(new_cal)

        if added or removed or modified:
            send_email(added, removed, modified, calendar_name)
            os.replace(new_ics_path, old_ics_path)
        else:
            print("Keine Änderungen gefunden.")
            os.remove(new_ics_path)

if __name__ == "__main__":
    main()
