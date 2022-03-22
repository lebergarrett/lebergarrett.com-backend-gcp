from decimal import Decimal
# https://googleapis.dev/python/firestore/latest/index.html
from google.cloud import firestore


def visitor_app(request):
    firestore_client = firestore.Client()
    visitor_table = firestore_client.collection(
        u'visitorsapp').document(u'visitors')
    visitor_response = visitor_table.get()
    # If it exists, pull value, update it, return value
    # If it doesn't exist, create doc, return 1
    # Key should be site name "lebergarrett.com", val is number
