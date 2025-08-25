# quotation/models.py

from django.db import models

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    
    phone = models.CharField(max_length=20, blank=True, null=True)
    def __str__(self):
        return self.name

class Quotation(models.Model):
    quotation_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    expected_delivery_date = models.DateField()
    payment_term = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    tax = models.FloatField(default=0.0)  # % for whole quotation
    total_price = models.FloatField(editable=False)  # sum of all item totals
    grand_total = models.FloatField(editable=False)  # total + tax

    def save(self, *args, **kwargs):
        # Generate order number if not exists
        if not self.quotation_number:
            last_order = Quotation.objects.order_by('-id').first()
            if last_order and last_order.quotation_number:
                last_number = int(last_order.quotation_number[2:])
                new_number = last_number + 1
            else:
                new_number = 2001
            self.quotation_number = f"IF{new_number}"
        super().save(*args, **kwargs)  # ← VERY IMPORTANT


    def __str__(self):
        return f"Quotation #{self.id} - {self.customer.name}"


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.FloatField(default=0.0)


    def total(self):
        return self.quantity * self.price



class Invoice(models.Model):
    quotation = models.ForeignKey(
        Quotation, 
        on_delete=models.CASCADE, 
        related_name='invoices', 
        null=True,      # Allow NULL in DB
        blank=True      # Allow empty in forms
    )
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, null=True, blank=True)   # Add this line if missing
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField(null=True, blank=True)
    total_amount = models.FloatField()
    tax = models.FloatField(default=5.0)  # % for whole invoice
    grand_total = models.FloatField(editable=False)  # total + tax

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-id').first()
            if last_invoice and last_invoice.invoice_number:
                last_number = int(last_invoice.invoice_number[3:])
                new_number = last_number + 1
            else:
                new_number = 2001
            self.invoice_number = f"INV{new_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        if self.quotation:
            return f"Invoice #{self.invoice_number} for {self.quotation.customer.name}"
        return f"Invoice #{self.invoice_number} (No Quotation)"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.FloatField(default=0.0)

    def total(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.item_name} - {self.quantity} @ {self.price}"
