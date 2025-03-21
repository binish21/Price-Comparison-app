from google.cloud import vision
from google.oauth2 import service_account

GOOGLE_CREDENTIALS_PATH = "/Users/binish/Desktop/Deal Detective /capstone-450717-1c52b7f39ad7.json"

def detect_product(image_data):
    credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH)
    client = vision.ImageAnnotatorClient(credentials=credentials)
    image = vision.Image(content=image_data)

    web_response = client.web_detection(image=image).web_detection
    web_entities = web_response.web_entities if web_response.web_entities else []

    detected_objects = [entity.description for entity in web_entities if entity.score > 0.7]
    print("Identified Objects:", detected_objects)

    if detected_objects:
        search_term = max(detected_objects, key=len)
        print("Selected Search Term:", search_term)
        return search_term
    return "Unknown Product"