from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from num2words import num2words
import os
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
# AttributeError at /invoice/12/pdf/
# 'Canvas' object has no attribute 'moveTo' what to do?
# This error occurs when using an older version of reportlab. Ensure you have the latest version
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from django.conf import settings
from django.http import HttpResponse
import os
from django.shortcuts import get_object_or_404
from num2words import num2words
from .models import Quotation, Customer
from .models import QuotationItem
from .models import Invoice, InvoiceItem, Customer



class IFEXInvoice:
    def __init__(self, filename):
        self.filename = filename
        self.width, self.height = A4
        
        # Colors
        self.blue_color = colors.HexColor('#2f3e5b')
        self.light_blue = colors.HexColor('#75cef5')
        self.dark_blue = colors.HexColor('#2f3e5b')
        self.light_gray = colors.HexColor('#F0F0F0')
        self.white = colors.Color(1, 1, 1)
        self.black = colors.Color(0, 0, 0)
        
    def create_invoice(self, invoice_data):
        c = canvas.Canvas(self.filename, pagesize=A4)
        
        # Draw all components
        self._draw_header(c, invoice_data)
        self._draw_invoice_info(c, invoice_data)
        self._draw_customer_section(c, invoice_data)
        self._draw_items_table(c, invoice_data)
        self._draw_totals(c, invoice_data)
        self._draw_signatures(c)
        self._draw_footer(c, invoice_data)
        
        c.save()
    
    def _draw_header(self, c, data):
    # Header banner image that contains both logo and company details
        banner_path = None
        banner_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'header_banner.png'),
            os.path.join(settings.BASE_DIR, 'static', 'images', 'banner.png'),
            os.path.join(settings.BASE_DIR, 'static', 'images', 'ifex_header.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'header_banner.png') if settings.STATIC_ROOT else None,
            os.path.join(settings.STATIC_ROOT, 'images', 'banner.png') if settings.STATIC_ROOT else None,
            os.path.join(settings.STATIC_ROOT, 'images', 'ifex_header.png') if settings.STATIC_ROOT else None,
        ]
        
        for path in [p for p in banner_paths if p is not None]:
            if os.path.exists(path):
                banner_path = path
                break

        if banner_path:
            # Draw the complete header banner
            # Adjust width and height based on your banner image dimensions
            c.drawImage(banner_path, 10, self.height - 100, width=555, height=80)
        else:
            # Fallback - recreate the header design if banner image is not found
            self._draw_fallback_header(c, data)

    def _draw_fallback_header(self, c, data):
        """Fallback header design if banner image is not available"""
        # Logo on the left
        circle_y = self.height - 80
        c.setFillColor(colors.Color(0, 0.5, 0.78))
        c.circle(70, circle_y, 12, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#4B7BA7'))
        c.circle(88, circle_y-3, 10, fill=1, stroke=0)
        c.setFillColor(colors.Color(0.25, 0.41, 0.88))
        c.circle(103, circle_y+2, 8, fill=1, stroke=0)
        c.setFillColor(colors.HexColor('#4B7BA7'))
        c.setFont("Helvetica-Bold", 36)
        c.drawString(120, circle_y-6, "ifex")
        
        # Dark blue header box with arrow shape
        c.setFillColor(self.dark_blue)
        # Main rectangle
        c.rect(280, self.height - 100, 280, 65, fill=1, stroke=0)
        
        # Arrow shape on left side of blue box
        c.setFillColor(self.blue_color)
        points = [
            (260, self.height - 100),
            (280, self.height - 100),
            (280, self.height - 35),
            (260, self.height - 35),
            (240, self.height - 67.5)
        ]
        p = c.beginPath()
        p.moveTo(points[0][0], points[0][1])
        for point in points[1:]:
            p.lineTo(point[0], point[1])
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        
        # White text in header
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        
        # Header text - right aligned
        header_lines = [
            ("IFEX PR AND ADVERTISING EST", self.height - 57),
            ("C.R.No. 4030434660", self.height - 69),
            ("Ind. Area 3, Al Qusais, Dubai", self.height - 81),
            ("E mail: info@ifexprint.com", self.height - 93),
            ("www.ifexprint.com", self.height - 105)
        ]
        
        for text, y_pos in header_lines:
            text_width = c.stringWidth(text, "Helvetica", 9)
            c.drawString(550 - text_width, y_pos, text)
        
    def _draw_invoice_info(self, c, data):
        # TAX INVOICE title
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(self.blue_color)
        c.drawString(50, self.height - 140, "TAX INVOICE")
        
        # Invoice details on the right
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        # Labels
        labels_x = 380
        c.drawString(labels_x, self.height - 130, "INVOICE NO")
        c.drawString(labels_x, self.height - 145, "DATE")
        c.drawString(labels_x, self.height - 160, "PO NO.")
        
        # Values
        values_x = 480
        c.drawString(values_x, self.height - 130, str(data.get('invoice_number', '')))
        c.drawString(values_x, self.height - 145, data.get('invoice_date', ''))
        c.drawString(values_x, self.height - 160, data.get('po_number', ''))
        
        # TRN line
        c.drawString(50, self.height - 180, f"TRN. {data.get('trn', '104106033400003')}")
        
        # Horizontal line
        c.setStrokeColor(colors.black)
        c.line(50, self.height - 190, 560, self.height - 190)
    
    def _draw_customer_section(self, c, data):
        # TO label
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        c.drawString(50, self.height - 210, "TO")
        
        # Customer details
        customer = data.get('customer', {})
        c.drawString(80, self.height - 210, customer.get('name', ''))
        c.drawString(80, self.height - 225, customer.get('address', ''))
        c.drawString(80, self.height - 240, customer.get('address_line1', ''))
        c.drawString(80, self.height - 255, customer.get('address_line2', ''))
                
        # # Amount box on the right
        # c.setStrokeColor(colors.black)
        # c.rect(420, self.height - 265, 120, 25, fill=0, stroke=1)
        # c.drawString(430, self.height - 255, f"{data.get('grand_total', 0):.2f}")
    
    def _draw_items_table(self, c, data):
        # Table data
        table_data = []
        
        # Header row with blue background
        headers = [
            ['SALES PERSON', 'LPO DATE', 'DELIVERY DATE', 'PAYMENT TERMS'],
            [data.get('sales_person', ''), 
             data.get('lpo_date', ''), 
             data.get('delivery_date', ''), 
             data.get('payment_terms', '')]
        ]
        
        # Items header
        items_header = ['NO', 'DESCRIPTION', 'QTY', 'RATE', 'TAX\nAMOUNT', '%', 'LINE TOTAL']
        
        # Get items from data
        items = data.get('invoice_items', [])
        
        # Create table starting position
        table_y = self.height - 320
        
        # Draw sales info table
        sales_table = Table(headers, colWidths=[127.5, 127.5, 127.5, 127.5])
        sales_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.blue_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, 1), [colors.white]),
        ]))
        
        sales_table.wrapOn(c, self.width, self.height)
        sales_table.drawOn(c, 50, table_y)
        
        # Draw items table
        items_data = [items_header]
        
        # Add item rows
        for item in items:
            row = [
                str(item.get('no', '')),
                item.get('item_name', ''),
                str(item.get('quantity', '')),
                f"{item.get('price', 0):.2f}" if item.get('price') else '',
                f"{item.get('tax_amount', 0):.2f}" if item.get('tax_amount') else '',
                f"{item.get('tax_percent', 0):.2f}" if item.get('tax_percent') else '',
                f"{item.get('line_total', 0):.2f}" if item.get('line_total') else ''
            ]
            items_data.append(row)
        
        # Add empty rows to match the invoice layout
        for i in range(15 - len(items)):
            items_data.append(['', '', '', '', '', '', ''])
        
        # Add total row
        items_data.append(['', 'TOTAL', '', '', 
                          f"{data.get('total_tax_amount', 0):.2f}", 
                          f"{data.get('tax', 0):.2f}", 
                          f"{data.get('grand_total', 0):.2f}"])
        
        # Create items table
        col_widths = [30, 200, 50, 50, 60, 40, 80]
        items_table = Table(items_data, colWidths=col_widths)
        
        # Table styling
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.blue_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            
            # All cells
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # NO column
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),  # All numeric columns
            
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), self.light_gray),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            
            # Row heights
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.white]),
            ('LEFTPADDING', (1, 0), (1, -1), 5),

            


        ]))
        
        # Draw the items table
        items_table.wrapOn(c, self.width, self.height)
        items_table.drawOn(c, 50, 200)
    
    def _draw_totals(self, c, data):
        # Amount in words
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, 180, data.get('amount_in_words', ''))
    
    def _draw_signatures(self, c):
        # Signature section
        c.setFont("Helvetica", 10)
        c.drawString(50, 160, "Prepared by:")
        c.drawString(400, 160, "Received by:")
        
        # # Signature lines
        # c.line(50, 145, 150, 145)
        # c.line(300, 145, 400, 145)
            
        # Footer logo
        footer_logo_path = None
        footer_logo_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'footerlogo.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'footerlogo.png') if settings.STATIC_ROOT else None,
        ]
        
        for path in [p for p in footer_logo_paths if p is not None]:
            if os.path.exists(path):
                footer_logo_path = path
                break

        if footer_logo_path:
            c.drawImage(footer_logo_path, 45, 80, width=130, height=70, preserveAspectRatio=True)
        
        # # Arabic text below logo
        # c.setFont("Helvetica", 9)
        # c.drawString(60, 65, "Ù…Ø¤Ø³Ø³Ø© Ø¥ÙÙŠÙƒØ³ Ù„Ù„Ø¹Ù„Ø§Ù‚Ø§Øª Ø§Ù„Ø¹Ø§Ù…Ø© ÙˆØ§Ù„Ø¥Ø¹Ù„Ø§Ù†")
        
        # # Company name
        # c.setFont("Helvetica-Bold", 12)
        # c.drawString(200, 90, "IFEX")
        # c.setFont("Helvetica", 9)
        # c.drawString(230, 90, "PR &")
        
        # # ADVERTISING EST.
        # c.setFont("Helvetica", 8)
        # c.drawString(190, 75, "ADVERTISING EST.")
        
        # # Location
        # c.drawString(210, 60, "Dubai - UAE")
    
    def _draw_footer(self, c, data):
        # Blue footer bar
        c.setFillColor("#3b5e91")
        c.rect(40, 10, self.width - 80, 50, fill=1, stroke=0)
        
        # Footer text in white
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 8)
        
        # Bank details line 1
        footer_text1 = "BANK DETAILS : IFEX PR AND ADVERTISING EST"
        c.drawString(200, 38, footer_text1)
        
        # Bank details line 2
        footer_text2 = "ADCB : SHARJAH MAIN BRANCH, SWIFT CODE : ADCBAEAA050"
        c.drawString(170, 28, footer_text2)
        
        # Bank details line 3
        footer_text3 = "IBAN : AE02 0030 0130 3885 8920 001"
        c.drawString(230, 18, footer_text3)


# Main view function for generating invoice PDF
def generate_invoice_pdf(request, invoice_id):
    """
    Generate invoice PDF with data from Django models
    
    Args:
        request: Django request object
        invoice_id: ID of the invoice to generate
    """
    from .models import Invoice, InvoiceItem, Customer  # Import your models
    
    # Get invoice or return 404
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice_items = invoice.items.all()
    
    # Get customer - either from invoice directly or from quotation
    customer = None
    if invoice.customer:
        customer = invoice.customer
    elif invoice.quotation and invoice.quotation.customer:
        customer = invoice.quotation.customer

    # Setup HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'

    # Calculate totals
    total_amount = sum(item.total() for item in invoice_items)
    tax_amount = (total_amount * invoice.tax) / 100
    grand_total = total_amount + tax_amount

    # Prepare invoice data
    invoice_data = {
        'invoice_number': invoice.invoice_number,
        'invoice_date': invoice.invoice_date.strftime('%d/%m/%Y') if invoice.invoice_date else '',
        'po_number': '',  # Add po_number field to model if needed
        'trn': '104106033400003',  # Add trn field to model if needed
        'customer': {
            'name': customer.name if customer else 'N/A',
            'company': customer.company if customer and hasattr(customer, 'company') else '',
            'address_line1': customer.address.split(',')[0].strip() if customer and hasattr(customer, 'address') and customer.address else '',
            'address_line2': ', '.join(customer.address.split(',')[1:]).strip() if customer and hasattr(customer, 'address') and customer.address and len(customer.address.split(',')) > 1 else ''
        },
        'sales_person': 'Zubair',  # Add sales_person field to model if needed
        'lpo_date': '',  # Add lpo_date field to model if needed
        'delivery_date': invoice.quotation.expected_delivery_date if invoice.quotation else '',  # Add delivery_date field to model if needed
        'payment_terms': 'COD',  # Add payment_terms field to model if needed
        'invoice_items': [],
        'total_amount': total_amount,
        'tax': invoice.tax,
        'total_tax_amount': tax_amount,
        'grand_total': grand_total,
        'amount_in_words': num2words(float(grand_total), lang='en').title() + " Dirhams Only" if grand_total else ""
    }
    
    # Add items
    for i, item in enumerate(invoice_items, 1):
        item_tax_amount = (item.total() * invoice.tax) / 100
        invoice_data['invoice_items'].append({
            'no': i,
            'item_name': item.item_name,
            'quantity': item.quantity,
            'price': item.price,
            'tax_amount': item_tax_amount,
            'tax_percent': invoice.tax,
            'line_total': item.total() + item_tax_amount
        })
    
    # Generate the invoice
    invoice_pdf = IFEXInvoice(response)
    invoice_pdf.create_invoice(invoice_data)
    
    return response


# Example usage for standalone testing
if __name__ == "__main__":
    # Sample data for testing - replace with your actual data
    sample_data = {
        'invoice_number': 'INV2001',
        'invoice_date': '26/05/2025',
        'po_number': '',
        'trn': '104106033400003',
        'customer': {
            'name': 'Arif Ahmed',
            'company': 'Alfan Emirates LLC',
            'address_line1': 'Address line 1',
            'address_line2': 'Address line 2'
        },
        'sales_person': 'Zubair',
        'lpo_date': '13-Jun-25',
        'delivery_date': '',
        'payment_terms': 'COD',
        'invoice_items': [
            {
                'no': 1,
                'item_name': 'Business Card Printing',
                'quantity': 500,
                'price': 0.24,
                'tax_amount': 6.00,
                'tax_percent': 5.00,
                'line_total': 126.00
            }
        ],
        'total_amount': 120.00,
        'tax': 5.00,
        'total_tax_amount': 6.00,
        'grand_total': 126.00,
        'amount_in_words': 'One Hundred and Twenty Six Dirhams Only'
    }
    
    # Generate the invoice
    invoice_pdf = IFEXInvoice('test_invoice.pdf')
    invoice_pdf.create_invoice(sample_data)
    print("Invoice generated successfully!")