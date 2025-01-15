
from flask import Flask, request, render_template, send_file
import fitz  # PyMuPDF for PDF processing
from PIL import Image
from io import BytesIO
import openai
import os
import requests

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Set your OpenAI API key as an environment variable

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

# Function to divide text into scenes
def divide_text_into_scenes(text):
    scenes = text.split("\n\n")  # Splitting based on paragraphs for simplicity
    return [scene.strip() for scene in scenes if scene.strip()]

# Function to generate images from text using OpenAI's DALL-E
def generate_images_from_text(scenes):
    images = []
    for scene in scenes:
        response = openai.Image.create(
            prompt=scene,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        images.append(image_url)
    return images

# Function to create a storyboard PDF
def create_storyboard_pdf(scenes, images, output_pdf_path):
    doc = fitz.open()
    for scene, image_url in zip(scenes, images):
        response = requests.get(image_url)
        img = BytesIO(response.content)

        # Create a new page
        page = doc.new_page(width=595, height=842)  # A4 size in points

        # Add image to the page
        img_rect = fitz.Rect(50, 50, 545, 545)  # Adjust image size/position as needed
        pixmap = fitz.Pixmap(img)
        page.insert_image(img_rect, pixmap=pixmap)

        # Add text to the page
        page.insert_text((50, 600), scene, fontsize=12)

    doc.save(output_pdf_path)
    doc.close()

@app.route('/')
def upload_file():
    return '''
    <!doctype html>
    <title>Upload PDF</title>
    <h1>Upload a PDF to Create a Storyboard</h1>
    <form action="/create_storyboard" method="post" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    '''

@app.route('/create_storyboard', methods=['POST'])
def create_storyboard():
    if 'file' not in request.files:
        return "No file uploaded"

    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    # Save the uploaded file
    input_pdf_path = "uploaded.pdf"
    file.save(input_pdf_path)

    # Process the PDF
    text = extract_text_from_pdf(input_pdf_path)
    scenes = divide_text_into_scenes(text)
    images = generate_images_from_text(scenes)

    # Create the storyboard PDF
    output_pdf_path = "storyboard_output.pdf"
    create_storyboard_pdf(scenes, images, output_pdf_path)

    return send_file(output_pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
