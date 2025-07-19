from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
import uuid
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__)
app.secret_key = "supersecretkey"

# إعداد Supabase
SUPABASE_URL = "YOUR_SUPABASE_URL"  # من Supabase Dashboard
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"  # من Supabase Dashboard
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# إعداد Cloudinary
cloudinary.config(
    cloud_name="YOUR_CLOUD_NAME",  # من Cloudinary Dashboard
    api_key="YOUR_API_KEY",  # من Cloudinary Dashboard
    api_secret="YOUR_API_SECRET"  # من Cloudinary Dashboard
)

# الصفحة الرئيسية
@app.route('/')
@app.route('/index.html')
def home():
    # جلب الكتب من Supabase
    response = supabase.table('books').select('*').execute()
    books = response.data
    session_key = 'visited_home'
    if not session.get(session_key):
        count = load_counter() + 1
        save_counter(count)
        session[session_key] = True
    else:
        count = load_counter()
    return render_template('index.html', books=books, count=count)

# عداد الزيارات (محلي)
COUNTER_FILE = 'counter.json'

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, 'r') as f:
        return json.load(f).get("count", 0)

def save_counter(count):
    with open(COUNTER_FILE, 'w') as f:
        json.dump({"count": count}, f)

# عرض كتاب
@app.route('/book/<string:book_id>')
def view_book(book_id):
    response = supabase.table('books').select('*').eq('id', book_id).execute()
    book = response.data[0] if response.data else None
    if book:
        return render_template('book.html', book=book)
    return "الكتاب غير موجود", 404

# صفحة تسجيل الدخول
@app.route('/admin')
def admin():
    if not session.get("logged_in"):
        return render_template('login.html')
    return redirect('/dashboard')

# لوحة التحكم
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get("logged_in"):
        return redirect('/admin')
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')

        image_url = ""
        if image:
            # رفع الصورة لـ Cloudinary
            upload_result = cloudinary.uploader.upload(
                image,
                upload_preset="YOUR_UPLOAD_PRESET"  # من Cloudinary Dashboard
            )
            image_url = upload_result['secure_url']

        # إضافة الكتاب لـ Supabase
        new_book = {
            "id": str(uuid.uuid4()),
            "title": title,
            "content": content,
            "image": image_url
        }
        supabase.table('books').insert(new_book).execute()

        return redirect('/dashboard')

    # جلب الكتب من Supabase
    response = supabase.table('books').select('*').execute()
    books = response.data
    return render_template('dashboard.html', books=books)

# حذف كتاب
@app.route('/delete/<string:book_id>')
def delete_book(book_id):
    if not session.get("logged_in"):
        return redirect('/admin')

    # حذف الكتاب من Supabase
    supabase.table('books').delete().eq('id', book_id).execute()
    return redirect('/dashboard')

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "drgam" and password == "drgam":
            session["logged_in"] = True
            return redirect("/dashboard")
        else:
            error = "كلمة السر أو اسم المستخدم غير صحيحة"
    return render_template('login.html', error=error)

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

# صفحة النبذة
@app.route('/about.html', endpoint='about')
def about():
    return render_template('about.html')
