# quotation/urls.py

from stats import views
from django.urls import path
from .views import *
from stats import utils
from stats import invoice_pdf

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', create_quotation, name='create_quotation'),
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('<int:quotation_id>/', views.quotation_detail, name='quotation_detail'),
    path('<int:quotation_id>/edit/', edit_quotation, name='quotation_edit'),

    path('customers/', customer_list, name='customer_list'),
    path('customers/create/', customer_create, name='customer_create'),
    path('customers/<int:customer_id>/edit/', customer_edit, name='customer_edit'),
    path('customers/<int:customer_id>/delete/', customer_delete, name='customer_delete'),

    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', invoice_detail, name='invoice_detail'),
    path('invoices/create/', create_invoice, name='create_invoice_no_quotation'),  # without quotation_id
    path('invoices/<int:quotation_id>/create/', create_invoice, name='create_invoice'),  # with quotation_id
    path('invoices/create/dropdown', create_invoice_from_dropdown, name='create_invoice_dropdown'),
    path('invoices/<int:invoice_id>/edit/', edit_invoice, name='edit_invoice'),


    path('quotation/<int:quotation_id>/pdf/', utils.quotation_pdf2, name='quotation_pdf'),
    path('invoice/<int:invoice_id>/pdf/', invoice_pdf.generate_invoice_pdf, name='invoice_pdf'),
    path('do/<int:invoice_id>/pdf/', utils.disabled_view, name='do_pdf'),


]

