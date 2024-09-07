from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    def __repr__(self):
        return f'<Employee {self.name}>'


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(120), unique=False, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

    def __repr__(self):
        return f'<Client {self.name}>'


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref='invoices')
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'<Invoice {self.id}>'


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    invoice = db.relationship('Invoice', backref='items')
    amount = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    item_name = db.Column(db.String(100), nullable=True)
    total = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<InvoiceItem {self.id} - {self.total}>'

    # Automatically calculate the total based on amount and price
    @staticmethod
    def calculate_total(amount, price):
        return amount * price


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/employees')
def index():
    employees = Employee.query.all()
    return render_template('index.html', employees=employees)


@app.route('/add', methods=['POST'])
def add_employee():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    new_employee = Employee(name=name, email=email, phone=phone)
    db.session.add(new_employee)
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/clients')
def list_clients():
    clients = Client.query.all()
    return render_template('clients.html', clients=clients)


@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    address = request.form.get('address')
    phone = request.form.get('phone')

    new_client = Client(name=name, address=address, phone=phone)
    db.session.add(new_client)
    db.session.commit()

    return redirect(url_for('list_clients'))


@app.route('/invoice/<int:id>')
def view_invoice(id):
    invoice = Invoice.query.get(id)
    if invoice is None:
        abort(404)
    return render_template('view_invoice.html', invoice=invoice)


@app.route('/invoices')
def list_invoices():
    invoices = Invoice.query.all()
    return render_template('invoices.html', invoices=invoices)


@app.route('/add_invoice', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        client_id = request.form.get('client_id')

        # Create the invoice
        new_invoice = Invoice(client_id=client_id)
        db.session.add(new_invoice)
        db.session.commit()

        # Retrieve item data from the form
        amounts = request.form.getlist('amount[]')
        prices = request.form.getlist('price[]')
        item_names = request.form.getlist('item_name[]')  # Note the [] here

        # Ensure the lengths match
        if len(amounts) != len(prices) or len(amounts) != len(item_names):
            return "Error: The number of amounts, prices, and item names do not match", 400

        total_amount = 0.0  # Initialize total amount
ssss
        # Create invoice items
        for amount, price, item_name in zip(amounts, prices, item_names):
            amount = int(amount)
            price = float(price)
            total = InvoiceItem.calculate_total(amount, price)
            total_amount += total  # Update total amount

            new_item = InvoiceItem(invoice_id=new_invoice.id, amount=amount, price=price, item_name=item_name,
                                   total=total)
            db.session.add(new_item)

        # Update the invoice with the total amount
        new_invoice.total_amount = total_amount
        db.session.commit()

        # Redirect to the invoice details page after creation
        return redirect(url_for('view_invoice', id=new_invoice.id))

    # If it's a GET request, render the form to add an invoice
    clients = Client.query.all()
    return render_template('add_invoice.html', clients=clients)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get(id)

    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/delete/<int:id>')
def delete_employee(id):
    employee = Employee.query.get(id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('index'))


# Edit client (Update)
@app.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)

    if request.method == 'POST':
        client.name = request.form['name']
        client.address = request.form['address']
        client.phone = request.form['phone']

        db.session.commit()
        return redirect(url_for('list_clients'))

    return render_template('edit_client.html', client=client)


# Delete client (Delete)
@app.route('/clients/delete/<int:id>', methods=['POST'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('list_clients'))


if __name__ == '__main__':
    app.run(debug=True)
