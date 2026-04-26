import os
import sys

if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    BASE_DIR = sys._MEIPASS
else:
    # Running normally with python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDS_FILE = os.path.join(BASE_DIR, "service_account.json")

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

SHEET_NAME = "CanteenOrders"  # your Google Sheet name


def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    return gspread.authorize(creds)


def get_sheet(sheet_name):
    client = get_client()
    return client.open(SHEET_NAME).worksheet(sheet_name)
