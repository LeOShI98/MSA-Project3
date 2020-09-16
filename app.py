# web app that anglyse image content and translate into selected language
import os, base64, json, requests
from flask import Flask, render_template, request, flash

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import ComputerVisionErrorException
from msrest.authentication import CognitiveServicesCredentials


# Create a ComputerVisionClient instance for calling the Computer Vision API
vision_key = os.environ["VISION_KEY"]
vision_endpoint = os.environ["VISION_ENDPOINT"]
vision_credentials = CognitiveServicesCredentials(vision_key)
vision_client = ComputerVisionClient(vision_endpoint, vision_credentials)
# Retrieve the Translator Text API key 
translate_key = os.environ["TRANSLATE_KEY"]
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Define a route for the app's home page


@app.route("/", methods=["GET", "POST"])
def index():

    language = "en"

    if request.method == "POST":
        # Display the image that was uploaded
        image = request.files["file"]
        uri = "data:image/jpg;base64," + base64.b64encode(image.read()).decode("utf-8")
        image.seek(0)

        # Use the Computer Vision API to extract text from the image
        lines = get_description(image, vision_client)

        # Use the Translator Text API to translate text extracted from the image
        language = request.form.get("language", "en")
        translated_lines = translate_text(lines, language, translate_key)

        # Flash the translated text
        for translated_line in translated_lines:
            flash(translated_line)

    else:
        # Display a placeholder image
        uri = "/static/placeholder.png"

    return render_template("index.html", image_uri=uri, language=language)

# Function that extracts text from images
def get_description(image, client):
    try:
        result = client.tag_image_in_stream(image=image)
        lines=[]

        if len(result.tags) == 0:
            lines.append("Photo contains no text to translate")

        else:
            for tag in result.tags:
                text = "This might be " + tag.name 
                lines.append(text)
        lines.append("This could be anything ")
        lines.append("As long as you want it to be")
        
        return lines

    except ComputerVisionErrorException as e:
        return ["Computer Vision API error: " + e.message]

    except:
        return ["Error calling the Computer Vision API"]

def translate_text(lines, language, key):
    uri = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=" + language

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Content-type': 'application/json'
    }

    input=[]

    for line in lines:
        input.append({ "text": line })

    try:
        response = requests.post(uri, headers=headers, json=input)
        response.raise_for_status() # Raise exception if call failed
        results = response.json()

        translated_lines = []

        for result in results:
            for translated_line in result["translations"]:
                translated_lines.append(translated_line["text"])

        return translated_lines

    except requests.exceptions.HTTPError as e:
        return ["Error calling the Translator Text API: " + e.strerror]

    except Exception as e:
        return ["Error calling the Translator Text API"]
