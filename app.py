from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import os
import psycopg2
import logging
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# ============ إعدادات التطبيق الأساسية ============
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # للرفع المؤقت فقط
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============ إعدادات Cloudinary ============
cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)

# ============ إعدادات قاعدة البيانات ============
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        database_url = "postgresql://user:password@localhost:5432/mydb"
    return psycopg2.connect(database_url)

# ============ تهيئة قاعدة البيانات ============
def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # جدول الكتب
            cur.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    image TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول العداد
            cur.execute('''
                CREATE TABLE IF NOT EXISTS counter (
                    id SERIAL PRIMARY KEY,
                    views INTEGER DEFAULT 0
                )
            ''')
            
            # تهيئة العداد
            cur.execute("INSERT INTO counter (views) SELECT 0 WHERE NOT EXISTS (SELECT 1 FROM counter)")
        conn.commit()

# ============ دوال مساعدة ============
def load_books():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, image, content FROM books ORDER BY created_at DESC")
            return [
                {"id": row[0], "title": row[1], "image": row[2], "content": row[3]}
                for row in cur.fetchall()
            ]

def load_counter():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT views FROM counter LIMIT 1")
            result = cur.fetchone()
            return result[0] if result else 0

def increment_counter():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE counter SET views = views + 1 RETURNING views")
            new_views = cur.fetchone()[0]
            conn.commit()
            return new_views

# ============ تهيئة التطبيق ============
init_db()

# ============ إعدادات التسجيل (Logging) ============
if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=1024*1024, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

# ============ المسارات (Routes) ============
@app.route('/')
@app.route('/index.html')
def home():
    if not session.get('counted'):
        views = increment_counter()
        session['counted'] = True
    else:
        views = load_counter()
    return render_template('index.html', views=views)

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == os.environ.get('ADMIN_USER', 'admin') and password == os.environ.get('ADMIN_PASS', 'admin'):
            session['logged_in'] = True
            return redirect('/admin')
        return render_template('login.html', error='بيانات الدخول غير صحيحة')
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
        if 'image' not in request.files:
            return render_template('dashboard.html', error='لم يتم اختيار صورة', books=load_books())

        image = request.files['image']
        if image.filename == '':
            return render_template('dashboard.html', error='لم يتم اختيار صورة', books=load_books())

        try:
            # رفع الصورة إلى Cloudinary
            upload_result = cloudinary.uploader.upload(
                image,
                folder="book_covers",
                quality="auto",
                fetch_format="auto",
                width=800,
                height=800,
                crop="limit"
            )
            image_url = upload_result['secure_url']

            # إضافة الكتاب إلى قاعدة البيانات
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO books (title, image, content) VALUES (%s, %s, %s)",
                        (request.form['title'], image_url, request.form['content'])
                    )
                    conn.commit()

            return redirect('/admin')

        except Exception as e:
            app.logger.error(f"Upload failed: {str(e)}")
            return render_template('dashboard.html', error='فشل رفع الصورة', books=load_books())

    return render_template('dashboard.html', books=load_books())

@app.route('/api/books')
def get_books_api():
    return jsonify(load_books())

@app.route('/book.html')
def view_book():
    book_id = request.args.get('id', type=int)
    if book_id is None:
        return render_template('404.html'), 404

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, image, content FROM books WHERE id = %s", (book_id,))
            book = cur.fetchone()

    if book:
        return render_template('book.html', book={
            "id": book[0],
            "title": book[1],
            "image": book[2],
            "content": book[3]
        })
    return render_template('404.html'), 404

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if not session.get('logged_in'):
        return redirect('/login')

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # جلب رابط الصورة أولاً
                cur.execute("SELECT image FROM books WHERE id = %s", (book_id,))
                image_url = cur.fetchone()[0]
                
                # حذف الصورة من Cloudinary
                public_id = image_url.split('/')[-1].split('.')[0]
                cloudinary.uploader.destroy(f"book_covers/{public_id}")
                
                # حذف الكتاب من قاعدة البيانات
                cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
                conn.commit()

        return redirect('/admin')

    except Exception as e:
        app.logger.error(f"Delete failed: {str(e)}")
        return render_template('dashboard.html', error='فشل حذف الكتاب', books=load_books())

# ============ معالجة الأخطاء ============
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
