from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import os
import requests
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import cloudinary
import cloudinary.uploader

# إعداد Flask
app = Flask(__name__)
app.secret_key = 'secret@123'

# إعداد Cloudinary
cloudinary.config(
    cloud_name="dbjm14xbf",
    api_key="329374832568726",
    api_secret="gPanxHzfrwl2DW7C3cHHEnpspeU"
)

# إعداد Supabase
SUPABASE_URL = "https://kbyxdwrmsxerpyrqhsyk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtieXhkd3Jtc3hlcnB5dnFoc3lrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI5NDMyMTcsImV4cCI6MjA2ODUxOTIxN30.uiBqnNe-7r4OteS7HjYqEh_CzhFRZJelKBqIJiBsAz8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# بيانات الدخول
ADMIN_USERNAME = 'drgam'
ADMIN_PASSWORD = 'drgam'

# العداد البسيط
views_counter = 0

# الصفحة الرئيسية
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

# صفحة about
@app.route('/about.html')
def about():
    return render_template('about.html')

# تسجيل الدخول
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

# تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('counted', None)
    return redirect('/login')

# لوحة التحكم
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files['image']

        # رفع الصورة إلى Cloudinary
        result = cloudinary.uploader.upload(image)
        image_url = result['secure_url']

        # إضافة إلى Supabase
        supabase.table("books").insert({
            "title": title,
            "content": content,
            "image": image_url
        }).execute()

        return redirect('/admin')

    response = supabase.table("books").select("*").execute()
    books = response.data or []
    return render_template('dashboard.html', books=books)

# API للكتب
@app.route('/api/books')
def get_books():
    response = supabase.table("books").select("*").execute()
    return jsonify(response.data or [])

# صفحة عرض كتاب
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

# حذف كتاب
@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    supabase.table("books").delete().eq("id", book_id).execute()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
