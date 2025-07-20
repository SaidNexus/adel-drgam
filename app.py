import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv
from flask import Flask, request, redirect, render_template, session
import cloudinary
import cloudinary.uploader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# إعداد Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# طباعة القيم للتحقق
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY: {SUPABASE_KEY}")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY is not set or invalid")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Supabase client created successfully")
except Exception as e:
    print(f"Failed to create Supabase client: {str(e)}")
    raise Exception(f"Supabase error: {str(e)}")

# إعداد Cloudinary
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET")

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get("logged_in"):
        return redirect('/admin')
    
    if request.method == 'POST':
        try:
            print("Starting book insertion process...")
            title = request.form['title']
            content = request.form['content']
            image = request.files.get('image')

            print(f"Received form data: title={title}, content={content}, image={image}")

            image_url = ""
            if image:
                print("Uploading image to Cloudinary...")
                upload_result = cloudinary.uploader.upload(
                    image,
                    upload_preset=CLOUDINARY_UPLOAD_PRESET,
                    folder="books"
                )
                image_url = upload_result['secure_url']
                print(f"Image uploaded successfully: {image_url}")

            new_book = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "image": image_url
            }
            print(f"Inserting book: {new_book}")

            response = supabase.table('books').insert(new_book).execute()
            print(f"Insert response: {response.data}")

            return redirect('/dashboard')
        except Exception as e:
            print(f"Error adding book: {str(e)}")
            return render_template('dashboard.html', books=[], error=f"خطأ في إضافة الكتاب: {str(e)}")

    try:
        response = supabase.table('books').select('*').execute()
        books = response.data or []
        print(f"Fetched books: {books}")
    except Exception as e:
        print(f"Error fetching books: {str(e)}")
        books = []
    return render_template('dashboard.html', books=books)

# باقي الكود...
