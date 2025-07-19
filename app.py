from flask import Flask, render_template, request, redirect, jsonify, session
import os
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from werkzeug.utils import secure_filename

# تحميل المتغيرات من .env
load_dotenv()

# إعداد Flask
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default_secret")

# إعداد Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# إعداد Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# بيانات الدخول
ADMIN_USERNAME = 'drgam'
ADMIN_PASSWORD = 'drgam'

# عداد مشاهدات
views_counter = 0

@app.route('/')
@app.route('/index.html')
def home():
    global views_counter
    if not session.get('counted'):
        views_counter += 1
        session['counted'] = True
    response = supabase.table("books").select("*").execute()
    books = response.data or []
    return render_template('index.html', books=books, views=views_counter)

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin')
        return render_template('login.html', error='بيانات غير صحيحة')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('counted', None)
    return redirect('/login')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']

        # رفع الصورة على Cloudinary
        result = cloudinary.uploader.upload(image)
        image_url = result['secure_url']

        # حفظ البيانات على Supabase
        supabase.table("books").insert({
            "title": title,
            "content": content,
            "image": image_url
        }).execute()

        return redirect('/admin')

    response = supabase.table("books").select("*").execute()
    books = response.data or []
    return render_template('dashboard.html', books=books)

@app.route('/api/books')
def get_books():
    response = supabase.table("books").select("*").execute()
    return jsonify(response.data or [])

@app.route('/book.html')
def view_book():
    book_id = request.args.get('id')
    if not book_id:
        return "الكتاب غير موجود", 404
    response = supabase.table("books").select("*").eq('id', book_id).single().execute()
    book = response.data
    if not book:
        return "الكتاب غير موجود", 404
    return render_template('book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    supabase.table("books").delete().eq("id", book_id).execute()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
