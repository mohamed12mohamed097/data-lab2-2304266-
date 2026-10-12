# Lab 2: Login & To-Do Application

## 1. Team
- Mohamed [your last name], ID 2304266: did everything (database, back end, front end, README). Worked alone.

## 2. Technology
- Back end: Python 3, Flask, PyMySQL, bcrypt
- Front end: HTML, CSS, JavaScript (no framework)
- Database: MySQL 8

## 3. How to run
1. Install Python 3.9+, MySQL 8 and Git.
2. Clone the repository and open the folder.
3. Create and activate a virtual environment:
```
   python -m venv venv
   venv\Scripts\activate.bat
```
4. Install the libraries: `pip install -r requirements.txt`
5. Create the database: `mysql -u root -p < database/schema.sql`
6. Copy `.env.example` to `.env` and put your real MySQL password and a random `SECRET_KEY`.
7. Start the server: `python app.py`
8. Open http://127.0.0.1:5000/login

## 4. Features
R1 Register, R2 Login and Logout, R3 Private list, R4 Add, R5 Edit, R6 Mark done, R7 Delete with confirmation, R8 Validation in the browser and on the server, R9 bcrypt hashes and parameterized queries, R10 Responsive UI. No bonus features.

## 5. Screenshots
https://drive.google.com/drive/folders/1gg0H2XRQ8JO5_ttqpqFhGIIbWzK8aRf8?usp=sharing

## 6. Answers

**(a)** The id of a to-do comes from the browser, so anyone can send another user's number. `AND user_id = ?` uses the id of the logged-in user (taken from the session), so if the to-do belongs to someone else the statement changes zero rows. If I remove it, any logged-in user could edit, mark or delete other users' to-dos just by changing the id in the request.

**(b)** MySQL refuses the insert and shows error 1452 (a foreign key constraint fails), because there is no row in `users` with that `user_id`. This is the foreign key constraint, also called referential integrity: every to-do must belong to a user that really exists.

**(c)** If the database is stolen or leaked, plain passwords can be read and used directly, and many people reuse the same password on other sites. A bcrypt hash cannot be reversed. It is salted, so equal passwords give different hashes, and it is slow on purpose, which makes guessing passwords very expensive. To log in, the app compares the typed password with the stored hash.

**(d)** `NOT NULL` only refuses a missing value (NULL). An empty text `''` is a real value, so MySQL accepts it. Because of this, the server (and the browser) must check for an empty or spaces-only name themselves and show "Name is required".
