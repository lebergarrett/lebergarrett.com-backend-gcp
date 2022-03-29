from google.cloud import firestore

def visitor_count(req):
    database = firestore.Client()
    prev_count = 0
    visitor_ref = database.collection(u'visitors').document(u'visitor_count')
    doc = visitor_ref.get()
    if doc.exists:
        prev_count = int(doc.to_dict()['lebergarrett.com'])

    hit_count = str(prev_count + 1)
    visitor_ref.set({ 'lebergarrett.com': hit_count })

    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST",
    }

    return (hit_count, 200, headers)