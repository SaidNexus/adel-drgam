from flask import Flask, render_template, request, redirect, jsonify, session, url_for
import os, json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret@123'  # 🔐 مفتاح سري للجلسات
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['BOOKS_FILE'] = 'books.json'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# إعدادات تسجيل الدخول
ADMIN_USERNAME = 'drgam'
ADMIN_PASSWORD = 'drgam'

# تحميل الكتب
def load_books():
    if os.path.exists(app.config['BOOKS_FILE']):
        with open(app.config['BOOKS_FILE'], 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# حفظ الكتب
def save_books(books):
    with open(app.config['BOOKS_FILE'], 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

# الصفحة الرئيسية
@app.route('/')
@app.route('/index.html')
def home():
    return render_template('index.html')

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
    return redirect('/login')

# لوحة التحكم (محمية)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        image = request.files['image']
        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        books = load_books()
        books.append({
            "title": request.form['title'],
            "image": f"/static/uploads/{filename}",
            "content": request.form['content']
        })

        save_books(books)
        return redirect('/admin')

    return render_template('dashboard.html', books=load_books())

# API لجلب الكتب
@app.route('/api/books')
def get_books():
    return jsonify(load_books())

# صفحة عرض الكتاب
@app.route('/book.html')
def view_book():
    book_id = request.args.get('id', type=int)
    books = load_books()
    if book_id is not None and 0 <= book_id < len(books):
        return render_template('book.html', book=books[book_id])
    return "الكتاب غير موجود", 404

# حذف كتاب
@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    books = load_books()
    if 0 <= book_id < len(books):
        books.pop(book_id)
        save_books(books)
        return redirect('/admin')
    return "الكتاب غير موجود", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
