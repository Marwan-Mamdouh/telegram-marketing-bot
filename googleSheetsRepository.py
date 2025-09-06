import gspread
import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

# Load env variables
GOOGLE_CREDENTIALS: str | None = os.getenv("GOOGLE_CREDENTIALS")
SHEET_NAME: str = os.getenv("SHEET_NAME", "Orders")

# Initialize client


def init_sheet() -> None:
    scope: list[str] = ["https://spreadsheets.google.com/feeds",
                        "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1  # first sheet
    return sheet


def add_order(order_data: dict):
    """
    Append order to Google Sheet
    order_data = {
        "user_id": 12345,
        "username": "john",
        "product_id": 1,
        "product_name": "Shoes",
        "quantity": 2,
        "price": 10.0,
        "subtotal": 20.0,
        "shipping_fee": 5.0,
        "total": 25.0,
        "address": "Cairo, Egypt"
    }
    """
    sheet = init_sheet()
    sheet.append_row([
        order_data.get("user_id"),
        order_data.get("username"),
        order_data.get("product_id"),
        order_data.get("product_name"),
        order_data.get("quantity"),
        order_data.get("price"),
        order_data.get("subtotal"),
        order_data.get("shipping_fee"),
        order_data.get("total"),
        order_data.get("address")
    ])
