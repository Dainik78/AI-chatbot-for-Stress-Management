from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import cx_Oracle
import os
import json

app = Flask(__name__)
CORS(app)

# Oracle database configuration
os.environ['TNS_ADMIN'] = '/path/to/your/wallet'  # Set the path to your Oracle wallet if using one
dsn = "localhost:1521/xe"

# Secret key for session
app.secret_key = 'your_secret_key'

# Routes
@app.route('/')
def landpage():
    return render_template('landpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Admin login check
        if email == 'admin@gmail.com' and password == 'admin123':
            session['loggedin'] = True
            session['id'] = 'admin'
            session['email'] = email
            return redirect(url_for('home'))
        
        # User login check
        try:
            with cx_Oracle.connect(user="system", password="dainik", dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE email = :email AND password = :password", 
                                   {"email": email, "password": password})
                    user = cursor.fetchone()
            
            if user:
                session['loggedin'] = True
                session['id'] = user[0]  # Assuming the first column is the user ID
                session['email'] = user[1]  # Assuming the second column is the email
                return redirect(url_for('home'))
            else:
                return render_template('login.html', error='Invalid credentials')

        except cx_Oracle.DatabaseError as e:
            return render_template('login.html', error=str(e))
    
    return render_template('login.html')

@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['email'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        gender = request.form['gender']
        age = request.form['age']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        try:
            with cx_Oracle.connect(user="system", password="dainik", dsn=dsn) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (name, email, password, gender, age) 
                        VALUES (:name, :email, :password, :gender, :age)
                    """, {"name": name, "email": email, "password": password, "gender": gender, "age": age})
                connection.commit()

            return redirect(url_for('login'))

        except cx_Oracle.DatabaseError as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    try:
        # Extract data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        feedback_text = request.form.get('feedback')
        rating = request.form.get('rating')

        # Check if required fields are missing
        if not name or not email or not feedback_text or not rating:
            return jsonify({"error": "All fields are required"}), 400  # Return 400 Bad Request

        # Ensure rating is a valid number
        try:
            rating = int(rating)  # Convert to integer
            if rating < 1 or rating > 5:
                return jsonify({"error": "Rating must be between 1 and 5"}), 400
        except ValueError:
            return jsonify({"error": "Invalid rating format"}), 400

        # Database connection
        with cx_Oracle.connect(user="system", password="dainik", dsn="localhost:1521/xe") as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO feedback (name, email, feedback_text, rating) 
                    VALUES (:name, :email, :feedback_text, :rating)
                """, {"name": name, "email": email, "feedback_text": feedback_text, "rating": rating})
            connection.commit()

        return jsonify({"message": "Feedback submitted successfully", "name": name, "rating": rating})

    except cx_Oracle.DatabaseError as e:
        error_msg = str(e)
        print("Database Error:", error_msg)  # Log error in console
        return jsonify({"error": "Database error occurred", "details": error_msg}), 500

    except Exception as e:
        error_msg = str(e)
        print("General Error:", error_msg)  # Log error in console
        return jsonify({"error": "An unexpected error occurred", "details": error_msg}), 500

@app.route('/feedback-data')
def feedback_data():
    try:
        with cx_Oracle.connect(user="system", password="dainik", dsn=dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating ORDER BY rating")
                ratings = cursor.fetchall()

        rating_counts = {str(row[0]): row[1] for row in ratings}
        return jsonify(rating_counts)

    except cx_Oracle.DatabaseError as e:
        return jsonify({"error": str(e)}), 500

with open('intents.json', 'r') as file:
    intents = json.load(file)

# Function to get a response from intents.json based on user input
def get_chatbot_response(user_message):
    for intent in intents['intents']:
        if user_message.lower() in map(str.lower, intent['patterns']):
            return intent['responses'][0]  # Return the first response for simplicity
    return "Sorry, I didn't understand that. Could you rephrase?"

# Load intents from a JSON file
with open('intents.json', 'r') as file:
    intents = json.load(file)

# Function to get a response from intents.json based on user input
def get_chatbot_response(user_message):
    for intent in intents['intents']:
        if user_message.lower() in map(str.lower, intent['patterns']):
            return intent['responses'][0]  # Return the first response for simplicity
    return "Sorry, I didn't understand that. Could you rephrase?"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message')
    if not user_message:
        return jsonify({"response": "Message is empty. Please type something."})
    
    bot_response = get_chatbot_response(user_message)
    return jsonify({"response": bot_response})

@app.route('/psychiatrist')
def psychiatrist():
    return render_template('pysc.html')

@app.route('/yournotalone')
def yournotalone():
    return render_template('youarenotalone.html')

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/motivation')
def motivation():
    return render_template('motivational.html')

if __name__ == '__main__':
    app.run(debug=True)
