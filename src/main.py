from google.cloud import firestore

def visitor_count(req):
    database = firestore.Client()
    visitor_nb = 0
    visitor_ref = database.collection(u'visitors').document(u'visitor_count')
    doc = visitor_ref.get()
    if doc.exists:
        visitor_nb = int(doc.to_dict()['lebergarrett.com'])

    hitcount = str(visitor_nb + 1)
    visitor_ref.set({ 'lebergarrett.com': visitor_nb })

    return {
        "isBase64Encoded": "false",
        "statusCode": 200,
        "headers": { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Credentials": "true" },
        "body": hitcount
    }