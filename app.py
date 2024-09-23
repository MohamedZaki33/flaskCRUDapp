from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, flash
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
    address = db.Column(db.String(120), nullable=False)
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

    @staticmethod
    def calculate_total(amount, price):
        return amount * price


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    money_owed = db.Column(db.Float, nullable=False, default=0.0)  # الفلوس اللي ليه
    money_paid = db.Column(db.Float, nullable=False, default=0.0)  # الفلوس اللي خدها

    def __repr__(self):
        return f'<Supplier {self.name}>'


class Return(db.Model):
    __tablename__ = 'return'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    item_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    amount_returned = db.Column(db.Float, nullable=False)

    # relationships
    invoice = db.relationship('Invoice', backref=db.backref('returns', lazy=True))

    def __repr__(self):
        return f'<Return {self.item_name}>'


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    client = db.relationship('Client', backref='payments')
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    from_supplier = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    to_client = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    price_from_supplier = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='products', lazy=True)
    client = db.relationship('Client', backref='products', lazy=True)


with app.app_context():
    db.create_all()


@app.route('/suppliers')
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)


@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']

    new_supplier = Supplier(name=name, address=address, phone=phone)
    db.session.add(new_supplier)
    db.session.commit()

    return redirect(url_for('suppliers'))


@app.route('/edit_supplier/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    supplier = Supplier.query.get_or_404(id)

    if request.method == 'POST':
        supplier.name = request.form['name']
        supplier.address = request.form['address']
        supplier.phone = request.form['phone']
        db.session.commit()
        return redirect(url_for('suppliers'))


@app.route('/delete_supplier/<int:id>', methods=['POST'])
def delete_supplier(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    return redirect(url_for('suppliers'))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/employees')
def index():
    employees = Employee.query.all()
    return render_template('index.html', employees=employees)


@app.route('/add_employee', methods=['POST'])
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

        new_invoice = Invoice(client_id=client_id)
        db.session.add(new_invoice)
        db.session.commit()

        amounts = request.form.getlist('amount[]')
        prices = request.form.getlist('price[]')
        item_names = request.form.getlist('item_name[]')

        if len(amounts) != len(prices) or len(amounts) != len(item_names):
            return "Error: The number of amounts, prices, and item names do not match", 400

        total_amount = 0.0
        for amount, price, item_name in zip(amounts, prices, item_names):
            amount = int(amount)
            price = float(price)
            total = InvoiceItem.calculate_total(amount, price)
            total_amount += total

            new_item = InvoiceItem(invoice_id=new_invoice.id, amount=amount, price=price, item_name=item_name,
                                   total=total)
            db.session.add(new_item)

        new_invoice.total_amount = total_amount
        db.session.commit()

        return redirect(url_for('view_invoice', id=new_invoice.id))

    clients = Client.query.all()
    return render_template('add_invoice.html', clients=clients)


@app.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    employee = Employee.query.get(id)

    if request.method == 'POST':
        employee.name = request.form.get('name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/delete_employee/<int:id>')
def delete_employee(id):
    employee = Employee.query.get(id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/clients/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    client = Client.query.get_or_404(id)

    if request.method == 'POST':
        client.name = request.form['name']
        client.address = request.form['address']
        client.phone = request.form['phone']

        db.session.commit()
        return redirect(url_for('list_clients'))


@app.route('/clients/delete/<int:id>', methods=['POST'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('list_clients'))


@app.route('/client_statement/<int:id>')
def client_statement(id):
    client = Client.query.get_or_404(id)
    invoices = Invoice.query.filter_by(client_id=id).all()
    payments = Payment.query.filter_by(client_id=id).all()
    returns = Return.query.filter_by(invoice_id=id).all()  # تحديث الاستعلام للمرتجعات

    invoice_items = []
    for invoice in invoices:
        for item in invoice.items:
            invoice_items.append({
                'invoice_id': invoice.id,
                'item_name': item.item_name,
                'amount': item.amount,
                'price': item.price,
                'total': item.total,
                'date': invoice.date_created  # إضافة تاريخ الفاتورة
            })

    total_amount_owed = sum(invoice.total_amount for invoice in invoices)
    total_amount_paid = sum(payment.amount for payment in payments)
    total_returns = sum(ret.amount_returned for ret in returns)  # إجمالي المرتجعات
    # total_discounts = sum(invoice.discounts for invoice in invoices)  # إجمالي الخصومات

    return render_template('client_statement.html', client=client, invoices=invoices,
                           total_amount_owed=total_amount_owed, total_amount_paid=total_amount_paid,
                           total_returns=total_returns,
                           invoice_items=invoice_items, current_year=datetime.utcnow().year)


@app.route('/payments')
def list_payments():
    # Fetch all payments from the database
    payments = Payment.query.all()
    return render_template('list_payments.html', payments=payments)


@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        amount = request.form.get('amount')

        # Validate input
        if not client_id or not amount:
            return "Error: Client ID and amount are required", 400

        try:
            amount = float(amount)
        except ValueError:
            return "Error: Amount must be a valid number", 400

        # Create a new Payment object
        new_payment = Payment(client_id=client_id, amount=amount)
        db.session.add(new_payment)
        db.session.commit()

        return redirect(url_for('list_clients'))  # Redirect to a page where you can view all clients or payments

    clients = Client.query.all()
    return render_template('add_payment.html', clients=clients)


@app.route('/returns')
def list_returns():
    returns = Return.query.all()
    return render_template('list_returns.html', returns=returns)


@app.route('/add_return', methods=['GET', 'POST'])
def add_return():
    if request.method == 'POST':
        # Extract data from the form
        invoice_id = request.form['invoice_id']
        item_name = request.form['item_name']
        amount = request.form['amount']
        amount_returned = request.form['amount_returned']

        # Create a new Return object
        new_return = Return(
            invoice_id=invoice_id,
            item_name=item_name,
            amount=amount,
            amount_returned=amount_returned
        )

        # Add to the database
        db.session.add(new_return)
        db.session.commit()

        return redirect(url_for('list_returns'))

    # Fetch invoices for the form
    invoices = Invoice.query.all()
    return render_template('add_return.html', invoices=invoices)


@app.route('/client/<int:client_id>/payments', methods=['GET'])
def client_payments(client_id):
    client = Client.query.get_or_404(client_id)
    payments = Payment.query.filter_by(client_id=client_id).all()

    payments_data = [
        {
            'id': payment.id,
            'amount': payment.amount,
            'date': payment.date.strftime('%Y-%m-%d'),
            'status': payment.status,
        } for payment in payments
    ]

    return jsonify(payments_data)


@app.route('/products')
def product_list():
    products = Product.query.all()
    suppliers = Supplier.query.all()  # Fetch suppliers
    clients = Client.query.all()  # Fetch clients
    return render_template('product_list.html', products=products, suppliers=suppliers, clients=clients)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = request.form.get('amount')
        supplier = request.form.get('from_supplier')
        client = request.form.get('to_client')
        price_from_supplier = request.form.get('price_from_supplier')

        new_product = Product(
            name=name,
            amount=amount,
            from_supplier=supplier,
            to_client=client,
            price_from_supplier=price_from_supplier
        )
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('product_list'))

    suppliers = Supplier.query.all()
    clients = Client.query.all()
    return render_template('add_product.html', suppliers=suppliers, clients=clients)


@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)

    product.name = request.form.get('name')
    product.amount = request.form.get('amount')
    product.from_supplier = request.form.get('from_supplier')
    product.to_client = request.form.get('to_client')
    product.price_from_supplier = request.form.get('price_from_supplier')

    db.session.commit()
    return redirect(url_for('product_list'))


@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('product_list'))


if __name__ == '__main__':
    app.run(debug=True)
