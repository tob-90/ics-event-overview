# Calendar Overview Notification Script

## Description
This Python script regularly checks ICS calendar files for changes and sends notifications via email if new events are added, existing events are modified, or removed. The script supports both German and English languages. It is particularly designed for shared calendars, ensuring that all participants stay informed about updates in a structured and automated way. It was specifically developed for Radicale (https://radicale.org/), but it also works with other services such as Google Calendar. 

![calendar_overview](https://github.com/user-attachments/assets/9b8e4351-7faf-48b4-89d0-99218ceb8bca)

## Features
- Automatically retrieves events from ICS files
- Comparison of the current and previous versions of the calendar
- Detection of added, modified, and removed events
- Sending a structured HTML email with the changes
- Support for multiple recipients
- Simple configurable via a single `.env` file
- Multi-language (german/english)

## Installation
### Requirements
This script requires Python 3 and the following dependencies:

```bash
pip install urllib3 pytz requests icalendar python-decouple
```

### Setup
1. Copy the file `calendar_overview.py` to a folder of your choice.
2. Copy the HTML template file `template_overview.html` for email notifications to a folder of your choice.
3. Create a `.env` file in the folder containing `calendar_overview.py` with __at least__ the following parameters:
   
   ```ini
   SMTP_HOST = '<Your SMTP server>'
   SMTP_PORT = '<Your SMTP port>'
   SMTP_USERNAME = '<Your SMTP username>'
   SMTP_PASSWORD = '<Your SMTP password>'
   SENDER_EMAIL = '<Your sender email>'
   SENDER_NAME = '<Your name>'
   RECEIVER_EMAIL_OVERVIEW = '<Recipient emails, comma-separated for multiple recipients>'
   ICS_URL_OVERVIEW = '<ICS URLs, comma-separated for multiple urls>'
   TEMPLATE_OVERVIEW_PATH = '/path/to/template_overview.html'
   ```
4. Secure the `.env` file by restricting permissions:
   ```bash
   chmod 600 .env
   ```  
5. Make the script executable:
   ```bash
   chmod +x calendar_overview.py
   ```

## Usage
> [!NOTE]
> On the first execution of the script, no email will be sent. Instead, the current state of the calendar is saved as a reference. Only from the second run onward will changes be detected and notifications sent.

### Automated Execution with Cronjob (Recommended) 
To run the script automatically at a set interval (e.g., every 2 hours), add a Cronjob:

1. Open the Crontab editor:
   ```bash
   crontab -e
   ```
2. Add the following line to execute the script every 30 minutes:
   ```bash
   55 */2 * * * /usr/bin/python3 /path/to/calendar_overview.py
   ```
   Ensure the correct path to Python and the script is used.

### Manual Execution
Run the script with:
```bash
python3 calendar_overview.py
```

## Customization
- **TEST_MODE:** For testing purposes, set `TEST_MODE = True` within the script to save emails locally as HTML files instead of sending them.

### Additional `.env` Parameters
| Parameter               | Description                          | Example Value             | Default Value           |
|-------------------------|--------------------------------------|---------------------------|-------------------------|
| `TIMEZONE`             | Timezone for event processing       | `Europe/Berlin`, `UTC`           | `Europe/Berlin`                   |
| `DATE_FORMAT`          | Date format for events           | `%d.%m.%Y ⋅ %H:%M Uhr`, `%m/%d/%Y ⋅ %I:%M %p`    | `%d.%m.%Y ⋅ %H:%M Uhr`     |
| `LANGUAGE`            | Language setting (`EN` or `DE`)     | `EN`, `DE`                       | `EN`                    |
| `OLD_ICS_PATH_TEMPLATE=old_{}.ics`   | Path to save the old ics files           | `/path/to/old_{}.ics`       | `old_{}.ics`     |
| `NEW_ICS_PATH_TEMPLATE=new_{}.ics`   | Path to save the new ics files            | `/path/to/new_{}.ics`       | `new_{}.ics`     |

## Disclaimer
> [!CAUTION]
> This script is provided "as is," without any warranties or guarantees. The author is not responsible for any data loss, missed reminders, or unintended consequences resulting from the use of this script. Users are responsible for configuring and testing the script to ensure it meets their needs. Use at your own risk.
