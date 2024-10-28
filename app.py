from flask import  Flask, render_template, request, redirect, url_for,session
import mysql.connector
app=Flask(__name__)
app.secret_key = '0123'

app.config['MYSQL_HOST'] = 'sql12.freesqldatabase.com'
app.config['MYSQL_USER'] = 'sql12741263'
app.config['MYSQL_PASSWORD'] = 'MRKeSWPczK'
app.config['MYSQL_DB'] = 'sql12741263'

def get_mysql_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        port=app.config.get('MYSQL_PORT', 3306)
    )


def add_amount(dictionary,description):
    
    email = session['email']
    description=description
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT NAME FROM USERS WHERE email = %s", (email,))
    user = cursor.fetchone()


    for key, value in dictionary.items():
        cursor.execute("INSERT INTO EXPENSES (PHONE,AMOUNT,DESCRIPTION,ADDED_BY) VALUES (%s,%s,%s,%s)", (str(key),value,str(description),str(user[0])))
        conn.commit()
        
    conn.close()
        

@app.route('/')
def index():
    if 'email' in session:
        # User is logged in, fetch the username
        email = session['email']
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT NAME,NUMBER FROM USERS WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            # Fetch the first element from the tuple (name)
            name = user[0]
            phone=user[1]
        else:
            name = "Guest"  # Fallback if the user is not found

        return render_template("index.html", name=name,phone=phone)
    else:
        # User is not logged in, redirect to login page
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM USERS WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            # Store user in session
            session['email'] = email 
            return redirect(url_for('index'))
        else:
            return "Username or password is incorrect"
        
    return render_template('login.html')
    

@app.route('/signup',methods=("GET","POST"))
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        number=request.form.get("number")
        password = request.form.get("password")

        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Check if the username is already taken
        cursor.execute('SELECT * FROM USERS WHERE NUMBER = %s OR email = %s ', (number,email))
        existing_user = cursor.fetchone()

        if existing_user:
            # Phone already exists, handle accordingly (e.g., display an error message)
            return "Phone number/email already exists. Please choose a different phone number/email."


        cursor.execute('INSERT INTO USERS (name,NUMBER,email,password) VALUES (%s,%s,%s, %s)', (name,number,email, password))
        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for('index'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Remove user from session
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/split-expenses")
def split_expenses():
    return render_template("split-expenses.html")

@app.route("/equal",methods=["GET","POST"])
def equal():
    if request.method== "POST":
        # Get phone numbers from form
        phone_numbers = request.form.getlist('phones[]')

        
        # Get total expense from form
        total_expense = float(request.form.get('total_expense'))

        description=str(request.form.get('Description'))

        number_of_people = len(phone_numbers)

        # If no people are entered, return an error
        if number_of_people == 0:
            return "No phone numbers entered. Please enter at least one."

        # Split expense equally
        equal_share = total_expense / number_of_people

        # Prepare data for rendering result
        result = {
            'phone_numbers': phone_numbers,
            'total_expense': total_expense,
            'equal_share': equal_share,
            'number_of_people': number_of_people
        }

        dictionary = dict.fromkeys(phone_numbers, equal_share)

        print(description)
        add_amount(dictionary,description)     

        return render_template('added.html', phone_numbers=result["phone_numbers"],total_expense=result["total_expense"],number_of_people=result["number_of_people"],share=result["equal_share"])
    
    return render_template("equal.html")


@app.route("/amount", methods=['GET', 'POST'])
def amount():
    if request.method == "POST":
        expenses = request.form.getlist('expenses[]')
        
        dictionary = {}
        total_expense = 0
        
        description=str(request.form.get('Description'))

        # expenses[] will be a list of phone and amount pairs, so parse them correctly
        phone_numbers = request.form.getlist('expenses[][phone]')
        amounts = request.form.getlist('expenses[][amount]')
        
        # Build the dictionary and calculate the total expense
        for phone, amount in zip(phone_numbers, amounts):
            dictionary[phone] = float(amount)
            total_expense += float(amount)

        Share_per_person = dictionary

        add_amount(dictionary,str(description))

        return render_template('added.html',
                               total_expense=total_expense,
                               phone_numbers=list(dictionary.keys()),
                               share=Share_per_person,
                               number_of_people=len(dictionary),
                               dictionary=dictionary)

    return render_template("amount.html")


@app.route("/percentage",methods=['GET','POST'])
def percentage():
    if request.method == "POST":
        total_amount = float(request.form['total_amount'])  # Get the total amount
        phone_numbers = request.form.getlist('expenses[][phone]')
        percentages = request.form.getlist('expenses[][percentage]')
        
        dictionary = {}
        total_percentage = 0
        
        description=str(request.form.get('Description'))
        
        # Build the dictionary and calculate the individual shares
        for phone, percentage in zip(phone_numbers, percentages):
            percentage = float(percentage)
            amount_share = (percentage / 100) * total_amount  # Calculate share from percentage
            dictionary[phone] = round(amount_share, 2)  # Round to 2 decimal places
            total_percentage += percentage

        if total_percentage > 100:
            return "Error: added percentages goes more then 100."

        Share_per_person = dictionary
        total_expense = total_amount  # The total amount remains the same

        add_amount(dictionary,str(description))

        return render_template('added.html',
                               total_expense=total_expense,
                               phone_numbers=list(dictionary.keys()),
                               share=Share_per_person,
                               number_of_people=len(dictionary),
                               dictionary=dictionary)

    return render_template("percentage.html")

@app.route("/balance-sheet")
def balance_sheet():
    email=session["email"]
    #Reading Phone number of currently logged in user
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT NUMBER FROM USERS WHERE email = %s ", (email,))
    user = cursor.fetchone()
    phone=user[0]
    cursor.close()
    conn.close()

    # Reading transaction history of currently loggedin user
    
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT AMOUNT,DESCRIPTION,ADDED_BY FROM EXPENSES WHERE PHONE = %s ", (phone,))
    transactions = cursor.fetchall()
    print(transactions)



    return render_template("balance-sheet.html",Transactions=transactions)

app.run(debug=False,host='0.0.0.0')
