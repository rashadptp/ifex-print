from django.shortcuts import render, redirect
from .models import *
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
def create_quotation(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        payment_term = request.POST.get('payment_term', '')
        expected_delivery_date = request.POST.get('expected_delivery_date')
        tax = 5.0  # Default tax percentage

        customer = Customer.objects.get(id=customer_id)

        item_names = request.POST.getlist('item_name')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')

        # Validate we have matching counts for all item fields
        if len(item_names) != len(quantities) or len(item_names) != len(prices):
            messages.error(request, "Invalid item data submitted")
            return redirect('create_quotation')

        total_price = 0
        item_data = []

        for name, qty_str, price_str in zip(item_names, quantities, prices):
            try:
                qty = int(qty_str)
                price = float(price_str)
                item_total = qty * price
                total_price += item_total
                item_data.append({
                    'item_name': name,
                    'quantity': qty,
                    'price': price
                })
            except (ValueError, TypeError):
                messages.error(request, "Invalid quantity or price format")
                return redirect('create_quotation')

        # Calculate tax and grand total (this will work for any number of items)
        tax_amount = total_price * tax / 100
        grand_total = total_price + tax_amount

        quotation = Quotation.objects.create(
            customer=customer,
            expected_delivery_date=expected_delivery_date,
            payment_term=payment_term,
            tax=tax,
            total_price=total_price,
            grand_total=grand_total
        )

        for item in item_data:
            QuotationItem.objects.create(
                quotation=quotation,
                item_name=item['item_name'],
                quantity=item['quantity'],
                price=item['price']
            )

        return redirect('quotation_list')
    
    else:
        # GET request - show form
        last_quotation = Quotation.objects.order_by('-id').first()
        if last_quotation and last_quotation.quotation_number:
            last_number = int(last_quotation.quotation_number[2:])
            next_quotation_number = f"IF{last_number + 1}"
        else:
            next_quotation_number = "IF2001"

        customers = Customer.objects.all()
        return render(request, 'stats/create_quotation.html', {
            'customers': customers,
            'next_quotation_number': next_quotation_number
        })



def quotation_list(request):
    quotations = Quotation.objects.select_related('customer').order_by('-created_at')
    return render(request, 'stats/quotation_list.html', {'quotations': quotations})

from django.shortcuts import get_object_or_404


def quotation_detail(request, quotation_id):
    quotation = get_object_or_404(Quotation, id=quotation_id)
    items = quotation.items.all()
    for item in items:
        item.line_total = item.quantity * item.price

    return render(request, 'stats/quotation_detail.html', {
        'quotation': quotation,
        'items': items,
    })

def edit_quotation(request, quotation_id):
    quotation = get_object_or_404(Quotation, id=quotation_id)
    customers = Customer.objects.all()
    items = quotation.items.all()

    if request.method == 'POST':
        try:
            # Validate and update basic quotation info
            quotation.customer = get_object_or_404(Customer, id=request.POST.get('customer'))
            quotation.expected_delivery_date = request.POST.get('expected_delivery_date')
            quotation.payment_term = request.POST.get('payment_term', '')
            
            # Validate tax percentage
            tax = float(request.POST.get('tax', 5.0))
            if not (0 <= tax <= 100):
                raise ValueError("Tax percentage must be between 0 and 100")
            quotation.tax = tax

            # Process items
            item_names = request.POST.getlist('item_name')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('price')

            # Validate equal number of items
            if len(item_names) != len(quantities) or len(item_names) != len(prices):
                raise ValueError("Mismatched item data count")

            total_price = 0
            quotation.items.all().delete()  # Clear existing items

            for name, qty_str, price_str in zip(item_names, quantities, prices):
                try:
                    qty = int(qty_str)
                    price = float(price_str)
                    if qty <= 0 or price < 0:
                        raise ValueError("Quantity must be positive and price cannot be negative")
                        
                    item_total = qty * price
                    total_price += item_total

                    QuotationItem.objects.create(
                        quotation=quotation,
                        item_name=name.strip(),
                        quantity=qty,
                        price=price,
                    )
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid item data: {str(e)}")

            # Calculate totals
            tax_amount = total_price * quotation.tax / 100
            quotation.total_price = total_price
            quotation.grand_total = total_price + tax_amount
            
            quotation.save()
            messages.success(request, "Quotation updated successfully")
            return redirect('quotation_detail', quotation_id=quotation.id)

        except Exception as e:
            messages.error(request, f"Error updating quotation: {str(e)}")
            # Return to form with existing data
            return render(request, 'stats/create_quotation.html', {
                'quotation': quotation,
                'customers': customers,
                'items': items,
                'error': str(e)
            })

    # GET request - show form
    return render(request, 'stats/create_quotation.html', {
        'quotation': quotation,
        'customers': customers,
        'items': items,
    })

############ CUSTOMER VIEWS ############
from django.shortcuts import render, redirect, get_object_or_404
from .models import Customer

# List all customers
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customer/customer_list.html', {'customers': customers})


# Create a new customer
def customer_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        Customer.objects.create(name=name, phone=phone, address=address, city=city)
        return redirect('customer_list')
    return render(request, 'customer/customer_form.html', {'action': 'Create'})


# Edit an existing customer
def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address', '')
        customer.city = request.POST.get('city', '')
        customer.save()
        return redirect('customer_list')
    return render(request, 'customer/customer_form.html', {'customer': customer, 'action': 'Edit'})


# Delete a customer immediately (no confirmation)
def customer_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    customer.delete()
    return redirect('customer_list')


#########  INVOICE VIEWS ############
def create_invoice(request, quotation_id=None):
    quotation = None
    if quotation_id:
        quotation = get_object_or_404(Quotation, id=quotation_id)

    if request.method == 'POST':
        tax = 5.0  # Default VAT rate
        item_names = request.POST.getlist('item_name')
        invoice_date = request.POST.get('invoice_date', timezone.now().date())
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')

        # Determine customer
        customer = None
        if quotation:
            customer = quotation.customer
        else:
            customer_id = request.POST.get('customer')
            if not customer_id:
                messages.error(request, "Please select a customer")
                return redirect('create_invoice')
            customer = get_object_or_404(Customer, id=customer_id)

        # Validate items
        if not item_names or not all(item_names):
            messages.error(request, "Please add at least one item")
            return redirect('create_invoice')

        # Calculate totals
        total_amount = 0
        items = []
        for name, qty, price in zip(item_names, quantities, prices):
            if name and qty and price:
                try:
                    qty = int(qty)
                    price = float(price)
                    total_amount += qty * price
                    items.append({
                        'name': name,
                        'qty': qty,
                        'price': price,
                        'total': qty * price
                    })
                except (ValueError, TypeError):
                    continue

        if total_amount <= 0:
            messages.error(request, "Please enter valid item quantities and prices")
            return redirect('create_invoice')

        grand_total = total_amount + (total_amount * tax / 100)

        # Generate invoice number
        last_invoice = Invoice.objects.order_by('-id').first()
        new_number = 1
        if last_invoice:
            try:
                new_number = int(last_invoice.invoice_number.split('-')[-1]) + 1
            except:
                new_number = last_invoice.id + 1
        invoice_number = f"INV-{timezone.now().year}-{new_number:05d}"

        # Create invoice
        invoice = Invoice.objects.create(
            invoice_number=invoice_number,
            quotation=quotation,
            customer=customer,
            invoice_date=invoice_date,
            total_amount=total_amount,
            tax=tax,
            grand_total=grand_total
        )

        # Create invoice items
        for item in items:
            InvoiceItem.objects.create(
                invoice=invoice,
                item_name=item['name'],
                quantity=item['qty'],
                price=item['price']
            )

        return redirect('invoice_detail', invoice_id=invoice.id)

    # GET request: Render the form
    context = {
        'quotation': quotation,
        'customers': Customer.objects.all(),
        'show_customer_select': not bool(quotation),
        'items': [],
        'quotation_items': quotation.items.all() if quotation else [],
    }
    return render(request, 'invoices/create_invoice.html', context)

    # For GET requests
    customers = Customer.objects.all()
    context = {
        'quotation': quotation,
        'quotation_items': quotation.items.all() if quotation else None,
        'customers': customers,
        'show_customer_select': not quotation
    }
    return render(request, 'invoice/create_invoice.html', context)

def invoice_list(request):
    invoices = Invoice.objects.select_related('quotation').all()
    now = timezone.now()
    invoices = invoices.filter(invoice_date__year=now.year, invoice_date__month=now.month)
    total_revenue = invoices.aggregate(total=Sum('grand_total'))['total'] or 0
    return render(request, 'invoice/invoice_list.html', {'invoices': invoices, 'total_revenue': total_revenue})

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = invoice.items.all()
    for item in items:
        item.line_total = item.quantity * item.price

    return render(request, 'invoice/invoice_detail.html', {
        'invoice': invoice,
        'items': items
    })

def create_invoice_from_dropdown(request):
    quotations = Quotation.objects.all()

    if request.method == 'POST':
        quotation_id = request.POST.get('quotation_id')
        if quotation_id == 'none':  # user selected no quotation
            return redirect('create_invoice_no_quotation')
        elif quotation_id:
            quotation = Quotation.objects.get(id=quotation_id)

            existing_invoice = quotation.invoices.first()
            if existing_invoice:
                return redirect('edit_invoice', invoice_id=existing_invoice.id)
            else:
                return redirect('create_invoice', quotation_id=quotation.id)

    return render(request, 'invoice/create_invoice_select.html', {
        'quotations': quotations
    })


def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    quotation = invoice.quotation
    items = invoice.items.all()
    customer = invoice.customer or (quotation.customer if quotation else None)

    if request.method == 'POST':
        tax = float(request.POST.get('tax', 5.0))  # Default to 5.0% VAT
        item_names = request.POST.getlist('item_name')
        invoice_date = request.POST.get('invoice_date', timezone.now().date())
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')

        # Determine customer
        if quotation:
            customer = quotation.customer  # Use quotation's customer
        else:
            customer_id = request.POST.get('customer')
            if not customer_id:
                messages.error(request, "Please select a customer")
                return redirect('edit_invoice', invoice_id=invoice.id)
            customer = get_object_or_404(Customer, id=customer_id)

        # Validate items
        if not item_names or not all(item_names):
            messages.error(request, "Please add at least one item")
            return redirect('edit_invoice', invoice_id=invoice.id)

        # Calculate totals
        total_amount = 0
        items_data = []
        for name, qty, price in zip(item_names, quantities, prices):
            if name and qty and price:
                try:
                    qty = int(qty)
                    price = float(price)
                    total_amount += qty * price
                    items_data.append({
                        'name': name,
                        'qty': qty,
                        'price': price,
                        'total': qty * price
                    })
                except (ValueError, TypeError):
                    continue

        if total_amount <= 0:
            messages.error(request, "Please enter valid item quantities and prices")
            return redirect('edit_invoice', invoice_id=invoice.id)

        grand_total = total_amount + (total_amount * tax / 100)

        # Update invoice
        invoice.customer = customer
        invoice.invoice_date = invoice_date
        invoice.total_amount = total_amount
        invoice.tax = tax
        invoice.grand_total = grand_total
        invoice.save()

        # Delete existing items and create new ones
        invoice.items.all().delete()
        for item in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                item_name=item['name'],
                quantity=item['qty'],
                price=item['price']
            )

        messages.success(request, "Invoice updated successfully")
        return redirect('invoice_detail', invoice_id=invoice.id)

    # GET request: Render the form
    context = {
        'invoice': invoice,
        'quotation': quotation,
        'customer': customer,  # Explicitly include the customer
        'customers': Customer.objects.all(),
        'show_customer_select': not bool(quotation),
        'items': items,
        'quotation_items': quotation.items.all() if quotation else [],
    }
    return render(request, 'invoice/create_invoice.html', context)

#######################   PDF EXPORT   #######################

from django.template.loader import render_to_string
from django.http import HttpResponse

from django.shortcuts import get_object_or_404
from num2words import num2words

def quotation_pdf_html(request, quotation_id):
    quotation = get_object_or_404(Quotation, id=quotation_id)
    items = quotation.items.all()
    customer = quotation.customer
    amount_in_words = num2words(quotation.grand_total, lang='en').title() + " Dirhams Only"
    

    html_string = render_to_string('stats/quotation_pdf.html', {
        'quotation': quotation,
        'items': items,
        'customer': customer
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Quotation_{quotation.quotation_number}.pdf"'
    return response


    
def do_pdf(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)
    items = invoice.items.all()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="DO_{invoice.invoice_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"Delivery Order")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Invoice #: {invoice.invoice_number}")
    y -= 20
    p.drawString(50, y, f"Customer: {invoice.quotation.customer.name}")
    y -= 20
    p.drawString(50, y, f"Issued Date: {invoice.issued_date}")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Items (No Pricing):")
    y -= 20

    p.setFont("Helvetica", 11)
    for item in items:
        p.drawString(60, y, f"{item.item_name} — Qty: {item.quantity}")
        y -= 18
        if y < 100:  # page break if needed
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 11)

    p.showPage()
    p.save()
    return response


def home(request):
    return render(request, 'stats/home.html')