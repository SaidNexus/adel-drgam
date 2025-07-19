from flask import Flask, render_template, request, redirect, session, url_for
import json
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

BOOKS_FILE = 'books.json'
COUNTER_FILE = 'counter.json'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# دوال التحميل والحفظ
def load_books():
    if not os.path.exists(BOOKS_FILE):
        return []
    with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_books(books):
    with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, 'r') as f:
        return json.load(f).get("count", 0)

def save_counter(count):
    with open(COUNTER_FILE, 'w') as f:
        json.dump({"count": count}, f)

# الصفحة الرئيسية
@app.route('/')
@app.route('/index.html')
def home():
    books = load_books()
    session_key = 'visited_home'
    if not session.get(session_key):
        count = load_counter() + 1
        save_counter(count)
        session[session_key] = True
    else:
        count = load_counter()
    return render_template('index.html', books=books, count=count)

# عرض كتاب
@app.route('/book/<string:book_id>')
def view_book(book_id):
    books = load_books()
    book = next((b for b in books if b.get("id") == book_id), None)
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
        image = request.files['image']

        filename = ""
        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)

        new_book = {
            "id": str(uuid.uuid4()),
            "title": title,
            "image": f"{UPLOAD_FOLDER}/{filename}" if filename else "",
            "content": content
        }

        books = load_books()
        books.append(new_book)
        save_books(books)

        return redirect('/dashboard')

    books = load_books()
    return render_template('dashboard.html', books=books)

# حذف كتاب
@app.route('/delete/<string:book_id>')
def delete_book(book_id):
    if not session.get("logged_in"):
        return redirect('/admin')

    books = load_books()
    books = [book for book in books if book.get("id") != book_id]
    save_books(books)
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
