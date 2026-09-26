import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = 'library.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    create_tables()
    seed_data()

def create_tables():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            phone TEXT,
            registration_date TEXT,
            status TEXT DEFAULT 'Active'
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            isbn TEXT UNIQUE,
            publisher TEXT,
            publication_year INTEGER,
            quantity INTEGER NOT NULL,
            available_quantity INTEGER NOT NULL,
            shelf TEXT,
            description TEXT,
            cover_image TEXT,
            added_date TEXT
        );

        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT NOT NULL,
            fine REAL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        );
    ''')
    conn.commit()
    conn.close()

def seed_data():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Admin
    c.execute('''INSERT INTO users (full_name,username,email,password_hash,role,phone,registration_date,status)
                 VALUES (?,?,?,?,?,?,?,?)''',
              ('Administrator', 'admin', 'admin@library.com',
               generate_password_hash('admin123'), 'admin', '9999999999', today, 'Active'))

    # Demo student
    c.execute('''INSERT INTO users (full_name,username,email,password_hash,role,phone,registration_date,status)
                 VALUES (?,?,?,?,?,?,?,?)''',
              ('Demo Student', 'student', 'student@library.com',
               generate_password_hash('student123'), 'student', '8888888888', today, 'Active'))

    books = [
        ('Python Crash Course','Eric Matthes','Python','978-1-59327-928-8','No Starch Press',2023,5,5,'A-1','A fast-paced, hands-on introduction to programming with Python.','python.jpg'),
        ('Automate the Boring Stuff with Python','Al Sweigart','Python','978-1-59327-599-0','No Starch Press',2020,4,4,'A-2','Learn Python while automating real-world tasks.','python.jpg'),
        ('Hands-On Machine Learning','Aurélien Géron','Machine Learning','978-1-09-812555-6','O\'Reilly',2022,3,3,'B-1','Using Scikit-Learn, Keras and TensorFlow.','machine-learning.jpg'),
        ('Artificial Intelligence: A Modern Approach','Stuart Russell & Peter Norvig','Artificial Intelligence','978-0-13-468599-1','Pearson',2020,3,3,'B-2','The leading textbook in Artificial Intelligence.','ai.jpg'),
        ('Data Structures and Algorithms Made Easy','Narasimha Karumanchi','Data Structures','978-8-19-245734-9','CareerMonk',2020,6,6,'C-1','700+ algorithmic problems and data structure questions.','datastructures.jpg'),
        ('Database System Concepts','Abraham Silberschatz','DBMS','978-0-07-802215-9','McGraw-Hill',2020,4,4,'D-1','The standard text for database systems.','database.jpg'),
        ('Computer Networks','Andrew S. Tanenbaum','Computer Networks','978-0-13-212695-3','Pearson',2021,3,3,'E-1','A top-down approach to computer networking.','networking.jpg'),
        ('Operating System Concepts','Abraham Silberschatz','Operating Systems','978-1-11-906333-0','Wiley',2018,4,4,'F-1','The dinosaur book — the OS standard reference.','operating-system.jpg'),
        ('Clean Code','Robert C. Martin','Software Engineering','978-0-13-235088-4','Prentice Hall',2008,5,5,'G-1','A handbook of agile software craftsmanship.','software-engineering.jpg'),
        ('HTML and CSS','Jon Duckett','Web Development','978-1-11-899402-0','Wiley',2011,4,4,'H-1','Design and build websites the professional way.','web-development.jpg'),
        ('Introduction to Algorithms','Thomas H. Cormen','Data Structures','978-0-26-204630-5','MIT Press',2022,3,3,'C-2','CLRS — the definitive algorithms textbook.','datastructures.jpg'),
        ('The Pragmatic Programmer','David Thomas & Andrew Hunt','Software Engineering','978-0-13-595705-9','Addison-Wesley',2019,4,4,'G-2','Your journey to mastery — timeless programming wisdom.','software-engineering.jpg'),
        ('Deep Learning','Ian Goodfellow','Machine Learning','978-0-26-203561-3','MIT Press',2016,3,3,'B-3','The authoritative deep learning reference.','machine-learning.jpg'),
        ('Computer Organization and Architecture','William Stallings','Computer Networks','978-0-13-461026-5','Pearson',2021,3,3,'E-2','Designing for performance at every level.','networking.jpg'),
        ('Head First Java','Kathy Sierra & Bert Bates','Java','978-0-59-600712-6','O\'Reilly',2005,5,5,'A-3','A brain-friendly guide to Java programming.','ai.jpg'),
        ('Effective Java','Joshua Bloch','Java','978-0-13-468599-2','Addison-Wesley',2018,3,3,'A-4','Best practices for the Java platform.','ai.jpg'),
        ('C++ Primer','Stanley B. Lippman','C++','978-0-32-171411-4','Addison-Wesley',2012,4,4,'A-5','The definitive introduction to C++.','datastructures.jpg'),
        ('Discrete Mathematics','Kenneth H. Rosen','Mathematics','978-0-07-338309-5','McGraw-Hill',2018,5,5,'I-1','Foundations of computer science mathematics.','mathematics.jpg'),
        ('Software Engineering','Ian Sommerville','Software Engineering','978-0-13-703515-1','Pearson',2015,4,4,'G-3','A comprehensive guide to software engineering practice.','software-engineering.jpg'),
        ('JavaScript: The Good Parts','Douglas Crockford','Web Development','978-0-59-651774-8','O\'Reilly',2008,4,4,'H-2','Unearthing the excellence in JavaScript.','web-development.jpg'),
    ]
    for b in books:
        c.execute('''INSERT INTO books (title,author,category,isbn,publisher,publication_year,quantity,available_quantity,shelf,description,cover_image,added_date)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (b[0],b[1],b[2],b[3],b[4],b[5],b[6],b[7],b[8],b[9],b[10],today))

    conn.commit()
    conn.close()

# ── Book functions ─────────────────────────────────────────────────────────────

def get_all_books(search='', category='', availability='', sort='title'):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM books WHERE 1=1"
    params = []
    if search:
        q += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)"
        s = f'%{search}%'
        params += [s,s,s,s]
    if category:
        q += " AND category=?"
        params.append(category)
    if availability == 'available':
        q += " AND available_quantity>0"
    elif availability == 'unavailable':
        q += " AND available_quantity<=0"
    sort_map = {'title':'title ASC','author':'author ASC','newest':'publication_year DESC','availability':'available_quantity DESC'}
    q += f" ORDER BY {sort_map.get(sort,'title ASC')}"
    c.execute(q, params)
    books = c.fetchall()
    conn.close()
    return books

def get_book_by_id(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    conn.close()
    return book

def add_book(data):
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO books (title,author,category,isbn,publisher,publication_year,quantity,available_quantity,shelf,description,cover_image,added_date)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
              (data['title'],data['author'],data['category'],data.get('isbn',''),
               data.get('publisher',''),data.get('publication_year',0),
               int(data['quantity']),int(data['quantity']),
               data.get('shelf',''),data.get('description',''),
               data.get('cover_image','default.jpg'),today))
    conn.commit()
    conn.close()

def update_book(book_id, data):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT quantity, available_quantity FROM books WHERE id=?", (book_id,))
    old = c.fetchone()
    new_qty = int(data['quantity'])
    diff = new_qty - old['quantity']
    new_avail = max(0, old['available_quantity'] + diff)
    new_avail = min(new_avail, new_qty)
    c.execute('''UPDATE books SET title=?,author=?,category=?,isbn=?,publisher=?,publication_year=?,
                 quantity=?,available_quantity=?,shelf=?,description=?,cover_image=? WHERE id=?''',
              (data['title'],data['author'],data['category'],data.get('isbn',''),
               data.get('publisher',''),data.get('publication_year',0),
               new_qty,new_avail,data.get('shelf',''),data.get('description',''),
               data.get('cover_image','default.jpg'),book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM issued_books WHERE book_id=? AND status='Issued'", (book_id,))
    active = c.fetchone()[0]
    if active > 0:
        conn.close()
        return False
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return True

def get_categories():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM books ORDER BY category")
    cats = [r['category'] for r in c.fetchall()]
    conn.close()
    return cats

# ── User functions ─────────────────────────────────────────────────────────────

def create_user(full_name, username, email, password_hash, phone):
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO users (full_name,username,email,password_hash,role,phone,registration_date,status)
                 VALUES (?,?,?,?,?,?,?,?)''',
              (full_name,username,email,password_hash,'student',phone,today,'Active'))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    u = c.fetchone()
    conn.close()
    return u

def get_user_by_email(email):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    u = c.fetchone()
    conn.close()
    return u

def get_user_by_id(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    u = c.fetchone()
    conn.close()
    return u

def get_all_users(search=''):
    conn = get_db()
    c = conn.cursor()
    if search:
        c.execute("SELECT * FROM users WHERE role='student' AND (full_name LIKE ? OR username LIKE ? OR email LIKE ?) ORDER BY id DESC",
                  (f'%{search}%',f'%{search}%',f'%{search}%'))
    else:
        c.execute("SELECT * FROM users WHERE role='student' ORDER BY id DESC")
    users = c.fetchall()
    conn.close()
    return users

def update_user(user_id, data):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET full_name=?,email=?,phone=? WHERE id=?",
              (data['full_name'],data['email'],data.get('phone',''),user_id))
    conn.commit()
    conn.close()

def update_user_password(user_id, new_hash):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
    conn.commit()
    conn.close()

def toggle_user_status(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE id=?", (user_id,))
    cur = c.fetchone()['status']
    new_status = 'Inactive' if cur == 'Active' else 'Active'
    c.execute("UPDATE users SET status=? WHERE id=?", (new_status, user_id))
    conn.commit()
    conn.close()

# ── Issue / Return functions ───────────────────────────────────────────────────

def calculate_fine(due_date_str, return_date_str=None):
    due = datetime.strptime(due_date_str, '%Y-%m-%d')
    ref = datetime.strptime(return_date_str, '%Y-%m-%d') if return_date_str else datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
    days_late = (ref - due).days
    return max(0, days_late * 5)

def issue_book(user_id, book_id):
    conn = get_db()
    c = conn.cursor()

    # Check active borrows
    c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND status='Issued'", (user_id,))
    if c.fetchone()[0] >= 3:
        conn.close()
        return False, "You have reached the maximum limit of 3 active borrowed books."

    # Check duplicate
    c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND book_id=? AND status='Issued'", (user_id,book_id))
    if c.fetchone()[0] > 0:
        conn.close()
        return False, "You have already borrowed this book."

    # Check availability
    c.execute("SELECT available_quantity FROM books WHERE id=?", (book_id,))
    book = c.fetchone()
    if not book or book['available_quantity'] <= 0:
        conn.close()
        return False, "This book is currently unavailable."

    today = datetime.now()
    due = today + timedelta(days=14)
    c.execute('''INSERT INTO issued_books (user_id,book_id,issue_date,due_date,status,fine)
                 VALUES (?,?,?,?,?,?)''',
              (user_id, book_id, today.strftime('%Y-%m-%d'), due.strftime('%Y-%m-%d'), 'Issued', 0))
    c.execute("UPDATE books SET available_quantity=available_quantity-1 WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return True, due.strftime('%d %B %Y')

def return_book(issue_id, user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM issued_books WHERE id=? AND user_id=? AND status='Issued'", (issue_id, user_id))
    issue = c.fetchone()
    if not issue:
        conn.close()
        return False, 0
    today = datetime.now().strftime('%Y-%m-%d')
    fine = calculate_fine(issue['due_date'], today)
    c.execute("UPDATE issued_books SET return_date=?,status='Returned',fine=? WHERE id=?",
              (today, fine, issue_id))
    c.execute("UPDATE books SET available_quantity=available_quantity+1 WHERE id=?", (issue['book_id'],))
    conn.commit()
    conn.close()
    return True, fine

def get_user_issued_books(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT ib.*,b.title,b.author,b.cover_image,b.category
                 FROM issued_books ib JOIN books b ON ib.book_id=b.id
                 WHERE ib.user_id=? AND ib.status='Issued' ORDER BY ib.issue_date DESC''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_returned_books(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT ib.*,b.title,b.author,b.cover_image,b.category
                 FROM issued_books ib JOIN books b ON ib.book_id=b.id
                 WHERE ib.user_id=? AND ib.status='Returned' ORDER BY ib.return_date DESC''', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_stats(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND status='Issued'", (user_id,))
    active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND status='Returned'", (user_id,))
    returned = c.fetchone()[0]
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM issued_books WHERE user_id=? AND status='Issued' AND due_date<?", (user_id,today))
    overdue = c.fetchone()[0]
    c.execute('''SELECT COALESCE(SUM(CASE WHEN status='Issued' THEN
                 MAX(0,(julianday('now') - julianday(due_date))*5)
                 ELSE fine END),0) FROM issued_books WHERE user_id=?''', (user_id,))
    fine = c.fetchone()[0]
    conn.close()
    return {'active':active,'returned':returned,'overdue':overdue,'fine':round(fine,2)}

# ── Admin functions ────────────────────────────────────────────────────────────

def get_library_stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM books")
    total_books = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(quantity),0) FROM books")
    total_copies = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(available_quantity),0) FROM books")
    available = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM issued_books WHERE status='Issued'")
    active_issues = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM issued_books WHERE status='Returned'")
    returned = c.fetchone()[0]
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT COUNT(*) FROM issued_books WHERE status='Issued' AND due_date<?", (today,))
    overdue = c.fetchone()[0]
    c.execute('''SELECT COALESCE(SUM(CASE WHEN status='Issued' THEN
                 MAX(0,(julianday('now')-julianday(due_date))*5) ELSE fine END),0)
                 FROM issued_books''')
    total_fines = round(c.fetchone()[0], 2)
    conn.close()
    return {'total_books':total_books,'total_copies':total_copies,'available':available,
            'users':users,'active_issues':active_issues,'returned':returned,
            'overdue':overdue,'total_fines':total_fines}

def get_books_by_category():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT category, COUNT(*) as cnt FROM books GROUP BY category ORDER BY cnt DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def get_monthly_issues():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT strftime('%Y-%m', issue_date) as month, COUNT(*) as cnt
                 FROM issued_books GROUP BY month ORDER BY month DESC LIMIT 12''')
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))

def get_monthly_returns():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT strftime('%Y-%m', return_date) as month, COUNT(*) as cnt
                 FROM issued_books WHERE status='Returned' GROUP BY month ORDER BY month DESC LIMIT 12''')
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))

def get_most_borrowed_books():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT b.title, COUNT(ib.id) as cnt
                 FROM issued_books ib JOIN books b ON ib.book_id=b.id
                 GROUP BY ib.book_id ORDER BY cnt DESC LIMIT 10''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_issued_books(status_filter=''):
    conn = get_db()
    c = conn.cursor()
    q = '''SELECT ib.*,u.full_name,u.username,b.title as book_title
           FROM issued_books ib
           JOIN users u ON ib.user_id=u.id
           JOIN books b ON ib.book_id=b.id'''
    params = []
    if status_filter:
        q += " WHERE ib.status=?"
        params.append(status_filter)
    q += " ORDER BY ib.issue_date DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_overdue_books():
    conn = get_db()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''SELECT ib.*,u.full_name,u.username,b.title as book_title
                 FROM issued_books ib
                 JOIN users u ON ib.user_id=u.id
                 JOIN books b ON ib.book_id=b.id
                 WHERE ib.status='Issued' AND ib.due_date<? ORDER BY ib.due_date ASC''', (today,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_active_borrowers():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT u.full_name,u.username,COUNT(ib.id) as cnt
                 FROM issued_books ib JOIN users u ON ib.user_id=u.id
                 GROUP BY ib.user_id ORDER BY cnt DESC LIMIT 10''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_registrations_monthly():
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT strftime('%Y-%m', registration_date) as month, COUNT(*) as cnt
                 FROM users WHERE role='student' GROUP BY month ORDER BY month DESC LIMIT 12''')
    rows = c.fetchall()
    conn.close()
    return list(reversed(rows))
