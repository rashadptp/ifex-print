from django.contrib import admin
from .models import Quotation, QuotationItem, Customer, Invoice, InvoiceItem
# Register your models here.
admin.site.register(Quotation)
admin.site.register(QuotationItem)
admin.site.register(Customer)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)