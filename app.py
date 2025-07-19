from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import os
from werkzeug.utils import secure_filename
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'secret@123'  # مفتاح الجلسات
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# بيانات الدخول
ADMIN_USERNAME = 'drgam'
ADMIN_PASSWORD = 'drgam'

# ----------- اتصال قاعدة البيانات -----------
def get_db_connection():
    # جلب رابط الاتصال من متغير البيئة
    database_url = os.environ.get('DATABASE_URL')
    
    # إذا لم يكن هناك رابط (لتجربة محلية)، يمكنك وضع رابط محلي
    if not database_url:
        # ضع هنا رابط قاعدة البيانات المحلية إن كنت تجرب محلياً
        database_url = "postgresql://user:password@localhost:5432/mydb"
    
    # إنشاء الاتصال باستخدام psycopg2
    conn = psycopg2.connect(database_url)
    return conn

# ----------- تهيئة الجداول -----------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # جدول الكتب
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            image TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    
    # جدول العداد
    cur.execute('''
        CREATE TABLE IF NOT EXISTS counter (
            id SERIAL PRIMARY KEY,
            views INTEGER DEFAULT 0
        )
    ''')
    
    # تهيئة العداد إذا كان الجدول فارغاً
    cur.execute("INSERT INTO counter (views) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM counter)")
    
    conn.commit()
    cur.close()
    conn.close()

# استدعاء تهيئة قاعدة البيانات عند بدء التشغيل
init_db()

# تحميل الكتب من قاعدة البيانات
def load_books():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, image, content FROM books ORDER BY id")
    books = [
        {"id": row[0], "title": row[1], "image": row[2], "content": row[3]}
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return books

# تحميل العداد
def load_counter():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT views FROM counter LIMIT 1")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else 0

# زيادة العداد
def increment_counter():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE counter SET views = views + 1 RETURNING views")
    new_views = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return new_views

# الصفحة الرئيسية
@app.route('/')
@app.route('/index.html')
def home():
    if not session.get('counted'):
        views = increment_counter()
        session['counted'] = True
    else:
        views = load_counter()
    return render_template('index.html', views=views)

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
    session.pop('counted', None)  # إعادة تفعيل العداد عند الخروج
    return redirect('/login')

# لوحة التحكم
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        image = request.files['image']
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # إضافة كتاب جديد إلى قاعدة البيانات
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO books (title, image, content) VALUES (%s, %s, %s)",
            (request.form['title'], f"/static/uploads/{filename}", request.form['content'])
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect('/admin')

    # عرض الكتب
    books = load_books()
    return render_template('dashboard.html', books=books)

# API للكتب
@app.route('/api/books')
def get_books_api():
    books = load_books()
    return jsonify(books)

# صفحة عرض كتاب
@app.route('/book.html')
def view_book():
    book_id = request.args.get('id', type=int)
    if book_id is None:
        return "الكتاب غير موجود", 404

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, image, content FROM books WHERE id = %s", (book_id,))
    book = cur.fetchone()
    cur.close()
    conn.close()

    if book:
        book_dict = {
            "id": book[0],
            "title": book[1],
            "image": book[2],
            "content": book[3]
        }
        return render_template('book.html', book=book_dict)
    return "الكتاب غير موجود", 404

# حذف كتاب
@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not session.get('logged_in'):
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
