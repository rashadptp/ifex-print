

from django.http import HttpResponse, HttpResponseForbidden
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
import os
from django.conf import settings
from num2words import num2words
from django.db.models import Sum
from django.utils import timezone
from .models import Quotation, QuotationItem, Customer, Invoice, InvoiceItem


def quotation_pdf(request, quotation_id):
    quotation = Quotation.objects.get(id=quotation_id)
    items = quotation.items.all()
    customer = quotation.customer

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Quotation_{quotation.quotation_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # IFEX Color Palette - matching the design exactly
    light_blue = colors.Color(0.53, 0.81, 0.92)  # #87CEEB - Light blue
    navy_blue = colors.Color(0.039, 0.164, 0.321)   # #4A5F7A - Navy blue
    silver_gray = colors.Color(0.96, 0.96, 0.97) # #F5F5F7 - Light gray
    gold_accent = colors.Color(0.83, 0.69, 0.22) # #D4AF37 - Gold
    dark_gray = colors.Color(0.3, 0.3, 0.3)
    white = colors.Color(1, 1, 1)
    black = colors.Color(0, 0, 0)   
    light_gray = colors.Color(0.95, 0.95, 0.95)  # #F2F2F2 - Light gray
    
    # LOGO HANDLING - Try multiple possible paths
    logo_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
        os.path.join(settings.STATIC_ROOT, 'images', 'logo.png') if settings.STATIC_ROOT else None,
        os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'logo.png'),
        os.path.join(settings.BASE_DIR, 'media', 'images', 'logo.png'),
        os.path.join(settings.BASE_DIR, 'assets', 'images', 'logo.png'),
    ]
    
    logo_paths = [path for path in logo_paths if path is not None]
    logo_found = False
    logo_path = None
    
    for path in logo_paths:
        if os.path.exists(path):
            logo_path = path
            logo_found = True
            break

    # HEADER SECTION - IFEX Design (Optimized positioning)
    # Left side: Logo area with circles and text
    logo_x = 30
    logo_y = height - 140
    
    if logo_found and logo_path:
        try:
            # Draw actual logo with better positioning
            p.drawImage(
                logo_path, 
                logo_x, logo_y, 
                width=220, 
                height=130, 
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            logo_found = False
    
    if not logo_found:
        # Draw stylized IFEX logo with circles (better aligned)
        circle_y = height - 80
        
        # Draw three circles with better spacing
        p.setFillColor(colors.Color(0, 0.5, 0.78))  # Dark blue circle
        p.circle(70, circle_y, 12, fill=1, stroke=0)
        
        p.setFillColor(light_blue)  # Light blue circle
        p.circle(88, circle_y-3, 10, fill=1, stroke=0)
        
        p.setFillColor(colors.Color(0.25, 0.41, 0.88))  # Medium blue circle
        p.circle(103, circle_y+2, 8, fill=1, stroke=0)
        
        # IFEX text - better aligned
        p.setFillColor(light_blue)
        p.setFont("Helvetica-Bold", 36)
        p.drawString(120, circle_y-6, "ifex")
        
        # Tagline below - aligned with text
        p.setFillColor(colors.gray)
        p.setFont("Helvetica", 9)
        p.drawString(238, height-85, "PR AND")
        p.drawString(238, height-97, "ADVERTISING EST")

    # Right side: Geometric banner with company info (Better proportions)
    banner_x = width - 320
    banner_y = height - 130
    banner_width = 270
    banner_height = 100
    
    # Create the geometric banner shape (cleaner angles)
    banner_path = p.beginPath()
    banner_path.moveTo(banner_x + 40, banner_y)  # Start point with angle
    banner_path.lineTo(banner_x + banner_width, banner_y)
    banner_path.lineTo(banner_x + banner_width, banner_y + banner_height)
    banner_path.lineTo(banner_x, banner_y + banner_height)
    banner_path.close()
    
    p.setFillColor(navy_blue)
    p.drawPath(banner_path, fill=1, stroke=0)
    
    # Banner text - properly aligned and spaced
    text_x = banner_x + banner_width - 20
    
    # Arabic text
    p.setFillColor(colors.white)
    p.setFont("Helvetica", 9)
    # p.drawRightString(text_x, banner_y + banner_height - 15, "مؤسسة إيفكس للعلاقات العامة و الإعلان")
    
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(text_x, banner_y + banner_height - 30, "IFEX PR AND ADVERTISING EST")
    
    p.setFont("Helvetica", 9)
    p.drawRightString(text_x, banner_y + banner_height - 45, "Phone: 055 831 7409")
    p.drawRightString(text_x, banner_y + banner_height - 57, "Ind. Area 3, Al Qusais, Dubai")
    p.drawRightString(text_x, banner_y + banner_height - 69, "E mail: sales@ifexprint.com")
    
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(text_x, banner_y + banner_height - 85, "www.ifexprint.com")

    # QUOTATION TITLE AND DETAILS (Better alignment)
    # Left: QUOTATION title
    p.setFillColor(navy_blue)
    p.setFont("Helvetica-Bold", 32)
    p.drawString(50, height - 170, "QUOTATION")
    
    # Right: Quotation details (properly aligned)
    details_x = width - 50
    details_y = height - 150
    
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(details_x, details_y, f"QUOTATION NO.              {quotation.quotation_number}")
    p.drawRightString(details_x, details_y - 15, f"DATE              {quotation.created_at.strftime('%d/%m/%Y')}")
    p.drawRightString(details_x, details_y - 30, "TRN.104106033400003")

    # CUSTOMER AND BANK SECTION (Aligned at same level)
    section_y = height - 270  # Same Y position for both sections

    # Left: Customer info (adjusted to match bank section height)
    customer_x = 50
    customer_width = 250  # Match width with bank section for balance

    # Customer box border
    p.setStrokeColor(colors.gray)
    p.setLineWidth(1)
    p.rect(customer_x, section_y - 20, customer_width, 100, fill=0, stroke=1)

    # Customer content
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(customer_x + 5, section_y + 55, "TO")  # Positioned inside box

    p.setFont("Helvetica", 11)
    p.setFillColor(dark_gray)
    p.drawString(customer_x + 10, section_y + 40, f"{customer.name}")

    # Handle customer address with better formatting
    address_y = section_y + 28
    if hasattr(customer, 'address') and customer.address:
        address_lines = customer.address.split(',')
        for i, line in enumerate(address_lines[:3]):  # Max 3 lines
            p.drawString(customer_x + 10, address_y - (i * 12), line.strip())
    else:
        p.drawString(customer_x + 10, address_y, quotation.customer.address or "UAE")
        p.drawString(customer_x + 10, address_y - 12, quotation.customer.city or "United Arab Emirates")

    # Right: Bank details box (same Y position as customer)
    bank_x = width - 300
    bank_width = 250
    bank_height = 100

    # Bank details border
    p.setStrokeColor(colors.gray)
    p.setLineWidth(1)
    p.rect(bank_x, section_y - 20, bank_width, bank_height, fill=0, stroke=1)

    # Bank content
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 9)
    p.drawCentredString(bank_x + bank_width/2, section_y + 35, "IFEX PR AND ADVERTISING EST.")
    p.setFont("Helvetica", 8.5)
    p.drawCentredString(bank_x + bank_width/2, section_y + 20, "A/c DETAILS : ABU DHABI COMMERCIAL BANK(ADCB)")
    p.drawCentredString(bank_x + bank_width/2, section_y + 11, "AE0200300130588589200001")
    # EXECUTIVE BAR (Better alignment and spacing)
    exec_y = height - 330
    table_width = width - 100  # Total width for both sections

    # Header bar (dark navy)
    p.setFillColor(navy_blue)
    p.rect(50, exec_y, table_width, 22, fill=1, stroke=0)

    # Header text with better centering
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 9)
    col_width = table_width / 3
    p.drawCentredString(50 + col_width/2, exec_y + 7, "Business Development Executive")
    p.drawCentredString(50 + col_width + col_width/2, exec_y + 7, "DELIVERY DATE")
    p.drawCentredString(50 + 2*col_width + col_width/2, exec_y + 7, "PAYMENT TERMS")

    # Values bar (light blue)
    p.setFillColor(light_gray)
    p.rect(50, exec_y - 18, table_width, 18, fill=1, stroke=0)

    p.setFillColor(colors.black)
    p.setFont("Helvetica", 9)
    p.drawCentredString(50 + col_width/2, exec_y - 11, "Zubair")
    p.drawCentredString(50 + col_width + col_width/2, exec_y - 11, quotation.expected_delivery_date.strftime('%d/%m/%Y'))
    p.drawCentredString(50 + 2*col_width + col_width/2, exec_y - 11, quotation.payment_term or "COD")

    # ITEMS TABLE (Same width as executive bar)
    table_y = exec_y - 50

    # Calculate dynamic table height based on items
    item_count = max(items.count(), 6)  # Minimum 6 rows, but adapt to actual items
    row_height = 22  # Base row height (will expand for wrapped text)

    # Table header - Use same table_width as executive bar
    header_data = [["NO", "DESCRIPTION", "QTY", "UNIT PRICE", "LINE TOTAL"]]
    col_widths = [
        35,  # NO
        table_width - 265,  # DESCRIPTION (adjust this to match total width)
        50,  # QTY
        80,  # UNIT PRICE
        80   # LINE TOTAL
    ]

    # Verify total width matches
    total_col_width = sum(col_widths)
    if abs(total_col_width - table_width) > 1:  # Allow 1pt tolerance
        col_widths[1] += (table_width - total_col_width)

    # Create a style for wrapped text
    styles = getSampleStyleSheet()
    item_style = ParagraphStyle(
        'ItemStyle',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        leading=10,
        leftIndent=0,
        rightIndent=0,
        wordWrap='LTR',
        splitLongWords=True,
        spaceBefore=0,
        spaceAfter=0
    )

    header_table = Table(header_data, colWidths=col_widths)
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), navy_blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.gray),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    header_table.wrapOn(p, table_width, height)
    header_table.drawOn(p, 50, table_y)

    # Table data rows
    current_y = table_y - 25

    # Prepare table data with wrapped text for descriptions
    table_data = []
    if items.exists():
        for idx, item in enumerate(items, start=1):
            # Create wrapped text paragraph for description
            wrapped_desc = Paragraph(item.item_name, item_style)
            table_data.append([
                str(idx),
                wrapped_desc,  # Use Paragraph instead of plain string
                str(item.quantity),
                f"{item.price:.2f}",
                f"{(item.quantity * item.price):.2f}"
            ])

    # Add empty rows with proper formatting
    empty_rows_count = max(4, 8 - len(table_data))
    for i in range(empty_rows_count):
        table_data.append(["", Paragraph("", item_style), "", "", ""])  # Empty Paragraph for description

    # Draw data rows with dynamic row heights
    for i, row_data in enumerate(table_data):
        # Calculate required row height based on wrapped text
        desc_height = 0
        if isinstance(row_data[1], Paragraph):
            desc_height = row_data[1].wrap(col_widths[1], height)[1]
        
        current_row_height = max(row_height, desc_height + 6)  # Add padding
        
        row_table = Table([row_data], colWidths=col_widths, rowHeights=[current_row_height])
        
        # Alternate row colors
        bg_color = colors.Color(0.95, 0.98, 1.0) if i % 2 == 0 else colors.white
        
        row_style = [
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]
        
        # Special style for Paragraph cells
        if isinstance(row_data[1], Paragraph):
            row_style.append(('LEFTPADDING', (1, 0), (1, 0), 5))
            row_style.append(('RIGHTPADDING', (1, 0), (1, 0), 5))
        
        row_table.setStyle(TableStyle(row_style))
        row_table.wrapOn(p, table_width, height)
        row_table.drawOn(p, 50, current_y)
        current_y -= current_row_height  # Use dynamic row height

    # Amount in words (better positioned)
    amount_words_y = current_y - 15
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Oblique", 10)
    try:
        from num2words import num2words
        amount_in_words = num2words(float(quotation.grand_total), lang='en').title() + " Dirhams Only"
    except:
        amount_in_words = "Amount in words will be calculated"
    p.drawString(50, amount_words_y, f"Amount in Words: {amount_in_words}")

    # TOTALS SECTION (Right aligned)
    totals_y = amount_words_y - 45
    totals_x = width - 210  # Keep totals on the right
    box_width = 160
    box_height = 18

    # NET AMOUNT
    p.setStrokeColor(colors.gray)
    p.setLineWidth(0.5)
    p.setFillColor(silver_gray)
    p.rect(totals_x, totals_y, box_width, box_height, fill=1, stroke=1)
    p.setFillColor(navy_blue)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(totals_x + 5, totals_y + 5, "NET AMOUNT")
    p.setFillColor(colors.black)
    p.drawRightString(totals_x + box_width - 5, totals_y + 5, f" {quotation.total_price:.2f}")
    
    tax_amount = quotation.total_price * (quotation.tax / 100)
    # 5% VAT
    p.setFillColor(silver_gray)
    p.rect(totals_x, totals_y - box_height, box_width, box_height, fill=1, stroke=1)
    p.setFillColor(navy_blue)
    p.drawString(totals_x + 5, totals_y - box_height + 5, "VAT (5%)")
    p.setFillColor(colors.black)
    p.drawRightString(totals_x + box_width - 5, totals_y - box_height + 5, f" {tax_amount:.2f}")

 


    # TOTAL AMOUNT (highlighted)
    p.setFillColor(light_gray)  # Light grey 
    p.rect(totals_x, totals_y - 2*box_height, box_width, box_height, fill=1, stroke=1)
    p.setFillColor(black)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(totals_x + 5, totals_y - 2*box_height + 5, "TOTAL AMOUNT")
    p.drawRightString(totals_x + box_width - 5, totals_y - 2*box_height + 5, f" {quotation.grand_total:.2f}/-")

    # # SIGNATURE SECTION (Left aligned)
    # signature_x = 50  # Left margin
    # signature_y = totals_y  # Align vertically with totals

    # p.setFillColor(colors.black)
    # p.setFont("Helvetica-Bold", 10)
    # p.drawString(signature_x, signature_y, "Authorized Signature:")

    # # Signature line and details
    # p.setFont("Helvetica", 9)
    # p.drawString(signature_x, signature_y - 30, "_" * 35)  # Signature line
    # p.drawString(signature_x, signature_y - 55, "Name: ___________________")
    # p.drawString(signature_x, signature_y - 70, f"Date: {quotation.created_at.strftime('%d/%m/%Y')}")
    # LOGO SECTION (Replacing signature)
    logo_x = 50  # Left margin
    logo_y = totals_y + 20  # Adjusted vertical position

    # Try to find logo (same logic as your header logo)
    logo_path = None
    logo_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'images', 'footerlogo.png'),
        os.path.join(settings.STATIC_ROOT, 'images', 'footerlogo.png') if settings.STATIC_ROOT else None,
        os.path.join(settings.BASE_DIR, 'staticfiles', 'images', 'footerlogo.png'),
        os.path.join(settings.BASE_DIR, 'media', 'images', 'footerlogo.png'),
        os.path.join(settings.BASE_DIR, 'assets', 'images', 'footerlogo.png'),
    ]

    for path in [p for p in logo_paths if p is not None]:
        if os.path.exists(path):
            logo_path = path
            break

    if logo_path:
        try:
            # Draw logo (adjust width/height as needed)
            logo_width = 120  # Adjust based on your logo aspect ratio
            logo_height = 60
            p.drawImage(
                logo_path,
                logo_x,
                logo_y - logo_height,  # Position above the bottom edge
                width=logo_width,
                height=logo_height,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Fallback to text if logo fails
            p.setFillColor(colors.black)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(logo_x, logo_y, "IFEX PR AND ADVERTISING")
    else:
        # Fallback text if no logo found
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(logo_x, logo_y, "IFEX PR AND ADVERTISING")

    # FOOTER SECTION (Optimized positioning)
    footer_y = 80
    
    # Footer background
    p.setFillColor(silver_gray)
    p.rect(0, 0, width, footer_y, fill=1, stroke=0)
    
    # Footer content - within margins with better alignment
    p.setFillColor(navy_blue)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, footer_y-18, "IFEX PR AND ADVERTISING EST")
    
    p.setFont("Helvetica", 8)
    p.drawString(50, footer_y-32, "Dubai UAE")
    p.drawString(50, footer_y-44, "For questions: Phone: 055 831 7409, 050 525 3616 | Email: info@ifexprint.com, sales@ifexprint.com")
    
    # Thank you message - positioned within right margin
    p.setFillColor(black)
    p.setFont("Helvetica-Bold", 10)
    p.drawRightString(width-50, footer_y-25, "Thank you for your business!")

    p.showPage()
    p.save()
    return response






########## WITH PAGINATION ##########

def quotation_pdf2(request, quotation_id):
    quotation = Quotation.objects.get(id=quotation_id)
    items = quotation.items.all()
    customer = quotation.customer

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Quotation_{quotation.quotation_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Color definitions
    light_blue = colors.Color(0.53, 0.81, 0.92)
    navy_blue = colors.Color(0.039, 0.164, 0.321)
    silver_gray = colors.Color(0.96, 0.96, 0.97)
    dark_gray = colors.Color(0.3, 0.3, 0.3)
    white = colors.Color(1, 1, 1)
    black = colors.Color(0, 0, 0)
    light_gray = colors.Color(0.95, 0.95, 0.95)

    # Constants for pagination
    ITEMS_PER_PAGE = 11
    current_page = 1
    total_pages = (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    item_counter = 1

    def draw_header():
        # Logo handling
        logo_path = None
        logo_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'logo.png') if settings.STATIC_ROOT else None,
        ]
        
        for path in [p for p in logo_paths if p is not None]:
            if os.path.exists(path):
                logo_path = path
                break

        if logo_path:
            try:
                p.drawImage(logo_path, 30, height - 140, width=220, height=130, preserveAspectRatio=True)
            except:
                # Fallback logo design
                circle_y = height - 80
                p.setFillColor(colors.Color(0, 0.5, 0.78))
                p.circle(70, circle_y, 12, fill=1, stroke=0)
                p.setFillColor(light_blue)
                p.circle(88, circle_y-3, 10, fill=1, stroke=0)
                p.setFillColor(colors.Color(0.25, 0.41, 0.88))
                p.circle(103, circle_y+2, 8, fill=1, stroke=0)
                p.setFillColor(light_blue)
                p.setFont("Helvetica-Bold", 36)
                p.drawString(120, circle_y-6, "ifex")

        # Company info banner
        banner_x = width - 320
        banner_y = height - 130
        banner_width = 270
        banner_height = 100
        
        banner_path = p.beginPath()
        banner_path.moveTo(banner_x + 40, banner_y)
        banner_path.lineTo(banner_x + banner_width, banner_y)
        banner_path.lineTo(banner_x + banner_width, banner_y + banner_height)
        banner_path.lineTo(banner_x, banner_y + banner_height)
        banner_path.close()
        
        p.setFillColor(navy_blue)
        p.drawPath(banner_path, fill=1, stroke=0)
        
        text_x = banner_x + banner_width - 20
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 11)
        p.drawRightString(text_x, banner_y + banner_height - 30, "IFEX PR AND ADVERTISING EST")
        p.setFont("Helvetica", 9)
        p.drawRightString(text_x, banner_y + banner_height - 45, "Phone: 055 831 7409")
        p.drawRightString(text_x, banner_y + banner_height - 57, "Ind. Area 3, Al Qusais, Dubai")
        p.drawRightString(text_x, banner_y + banner_height - 69, "E mail: sales@ifexprint.com")
        p.setFont("Helvetica-Bold", 10)
        p.drawRightString(text_x, banner_y + banner_height - 85, "www.ifexprint.com")

        # Quotation title and details
        p.setFillColor(navy_blue)
        p.setFont("Helvetica-Bold", 32)
        p.drawString(50, height - 170, "QUOTATION")
        
        details_x = width - 50
        details_y = height - 150
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        p.drawRightString(details_x, details_y, f"QUOTATION NO.              {quotation.quotation_number}")
        p.drawRightString(details_x, details_y - 15, f"DATE              {quotation.created_at.strftime('%d/%m/%Y')}")
        p.drawRightString(details_x, details_y - 30, "TRN.104106033400003")

        # Customer and Bank sections
        section_y = height - 270
        customer_x = 50
        customer_width = 250

        # Customer box
        p.setStrokeColor(colors.gray)
        p.setLineWidth(1)
        p.rect(customer_x, section_y - 20, customer_width, 100, fill=0, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(customer_x + 5, section_y + 55, "TO")
        p.setFont("Helvetica", 11)
        p.setFillColor(dark_gray)
        p.drawString(customer_x + 10, section_y + 40, f"{customer.name}")
        
        address_y = section_y + 28
        if customer.address:
            address_lines = customer.address.split(',')
            for i, line in enumerate(address_lines[:3]):
                p.drawString(customer_x + 10, address_y - (i * 12), line.strip())

        # Bank details box
        bank_x = width - 300
        bank_width = 250
        bank_height = 100
        p.rect(bank_x, section_y - 20, bank_width, bank_height, fill=0, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 9)
        p.drawCentredString(bank_x + bank_width/2, section_y + 35, "IFEX PR AND ADVERTISING EST.")
        p.setFont("Helvetica", 8.5)
        p.drawCentredString(bank_x + bank_width/2, section_y + 20, "A/c DETAILS : ABU DHABI COMMERCIAL BANK(ADCB)")
        p.drawCentredString(bank_x + bank_width/2, section_y + 11, "AE0200300130588589200001")

        # Executive bar
        exec_y = height - 330
        table_width = width - 100
        p.setFillColor(navy_blue)
        p.rect(50, exec_y, table_width, 22, fill=1, stroke=0)
        p.setFillColor(white)
        p.setFont("Helvetica-Bold", 9)
        col_width = table_width / 3
        p.drawCentredString(50 + col_width/2, exec_y + 7, "Business Development Executive")
        p.drawCentredString(50 + col_width + col_width/2, exec_y + 7, "DELIVERY DATE")
        p.drawCentredString(50 + 2*col_width + col_width/2, exec_y + 7, "PAYMENT TERMS")
        p.setFillColor(light_gray)
        p.rect(50, exec_y - 18, table_width, 18, fill=1, stroke=0)
        p.setFillColor(black)
        p.setFont("Helvetica", 9)
        p.drawCentredString(50 + col_width/2, exec_y - 11, "Zubair")
        p.drawCentredString(50 + col_width + col_width/2, exec_y - 11, quotation.expected_delivery_date.strftime('%d/%m/%Y'))
        p.drawCentredString(50 + 2*col_width + col_width/2, exec_y - 11, quotation.payment_term or "COD")

    def draw_footer():
        footer_y = 80
        p.setFillColor(silver_gray)
        p.rect(0, 0, width, footer_y, fill=1, stroke=0)
        p.setFillColor(navy_blue)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, footer_y-18, "IFEX PR AND ADVERTISING EST")
        p.setFont("Helvetica", 8)
        p.drawString(50, footer_y-32, "Dubai UAE")
        p.drawString(50, footer_y-44, "For questions: Phone: 055 831 7409, 050 525 3616 | Email: info@ifexprint.com, sales@ifexprint.com")
        p.setFillColor(black)
        p.setFont("Helvetica", 8)
        p.drawRightString(width-50, footer_y-25, f"Page {current_page} of {total_pages}")

    def draw_items(start_idx, end_idx, current_item_counter):
        table_y = height - 380
        col_widths = [20, width - 290, 30, 70, 70]
        
        # Table header
        header_data = [["NO", "DESCRIPTION", "QTY", "UNIT PRICE", "LINE TOTAL"]]
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), navy_blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        header_table.wrapOn(p, width - 100, height)
        header_table.drawOn(p, 50, table_y)

        # Table rows
        current_y = table_y - 25
        row_height = 22
        
        styles = getSampleStyleSheet()
        item_style = ParagraphStyle(
            'ItemStyle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            leading=10,
            leftIndent=0,
            rightIndent=0,
            wordWrap='LTR',
            splitLongWords=True,
            spaceBefore=0,
            spaceAfter=0
        )

        for idx in range(start_idx, end_idx):
            if idx >= len(items):
                break
                
            item = items[idx]
            wrapped_desc = Paragraph(item.item_name, item_style)
            row_data = [
                str(current_item_counter),
                wrapped_desc,
                str(item.quantity),
                f"{item.price:.2f}",
                f"{(item.quantity * item.price):.2f}"
            ]
            
            desc_height = row_data[1].wrap(col_widths[1], height)[1] if isinstance(row_data[1], Paragraph) else 0
            current_row_height = max(row_height, desc_height + 6)
            
            row_table = Table([row_data], colWidths=col_widths, rowHeights=[current_row_height])
            bg_color = white
            
            row_style = [
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (1, 0), (1, 0), 5),
                ('RIGHTPADDING', (1, 0), (1, 0), 5),
            ]
            
            row_table.setStyle(TableStyle(row_style))
            row_table.wrapOn(p, width - 100, height)
            row_table.drawOn(p, 50, current_y)
            current_y -= current_row_height
            current_item_counter += 1
        
        return current_item_counter  # Return the updated counter

    def draw_totals():
        totals_y = height - 650
        totals_x = width - 210
        box_width = 160
        box_height = 18

        # NET AMOUNT
        p.setStrokeColor(colors.gray)
        p.setLineWidth(0.5)
        p.setFillColor(silver_gray)
        p.rect(totals_x, totals_y, box_width, box_height, fill=1, stroke=1)
        p.setFillColor(navy_blue)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(totals_x + 5, totals_y + 5, "NET AMOUNT")
        p.setFillColor(black)
        p.drawRightString(totals_x + box_width - 5, totals_y + 5, f" {quotation.total_price:.2f}")
        
        tax_amount = quotation.total_price * (quotation.tax / 100)
        # 5% VAT
        p.setFillColor(silver_gray)
        p.rect(totals_x, totals_y - box_height, box_width, box_height, fill=1, stroke=1)
        p.setFillColor(navy_blue)
        p.drawString(totals_x + 5, totals_y - box_height + 5, "VAT (5%)")
        p.setFillColor(black)
        p.drawRightString(totals_x + box_width - 5, totals_y - box_height + 5, f" {tax_amount:.2f}")

        # TOTAL AMOUNT
        p.setFillColor(light_gray)
        p.rect(totals_x, totals_y - 2*box_height, box_width, box_height, fill=1, stroke=1)
        p.setFillColor(black)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(totals_x + 5, totals_y - 2*box_height + 5, "TOTAL AMOUNT")
        p.drawRightString(totals_x + box_width - 5, totals_y - 2*box_height + 5, f" {quotation.grand_total:.2f}/-")

        # Amount in words
        amount_words_y = totals_y - 3*box_height - 10
        p.setFillColor(black)
        p.setFont("Helvetica-Oblique", 10)
        try:
            amount_in_words = num2words(float(quotation.grand_total), lang='en').title() + " Dirhams Only"
        except:
            amount_in_words = "Amount in words will be calculated"
        p.drawString(50, amount_words_y, f"Amount in Words: {amount_in_words}")

        # Add logo on left side of totals (opposite the totals boxes)
        logo_x = 40
        logo_y = totals_y + 20  # Adjusted position to be opposite totals

        # Try to find footer logo
        logo_path = None
        logo_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'footerlogo.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'footerlogo.png') if settings.STATIC_ROOT else None,
        ]

        for path in [p for p in logo_paths if p is not None]:
            if os.path.exists(path):
                logo_path = path
                break

        if logo_path:
            try:
                # Draw logo (adjust width/height as needed)
                logo_width = 120
                logo_height = 60
                p.drawImage(
                    logo_path,
                    logo_x,
                    logo_y - logo_height,
                    width=logo_width,
                    height=logo_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
            except Exception as e:
                # Fallback to text if logo fails
                p.setFillColor(black)
                p.setFont("Helvetica-Bold", 10)
                p.drawString(logo_x, logo_y, "IFEX PR AND ADVERTISING")
        else:
            # Fallback text if no logo found
            p.setFillColor(black)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(logo_x, logo_y, "IFEX PR AND ADVERTISING")

    # Main PDF generation with pagination
    item_counter = 1
    for page in range(total_pages):
        if page > 0:
            p.showPage()
            current_page += 1
        
        draw_header()
        draw_footer()
        
        start_idx = page * ITEMS_PER_PAGE
        end_idx = (page + 1) * ITEMS_PER_PAGE
        item_counter = draw_items(start_idx, end_idx, item_counter)
        
        if page == total_pages - 1:
            draw_totals()

    p.save()
    return response


from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from num2words import num2words
import os
from django.conf import settings

def invoice_pdf(request, invoice_id):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from num2words import num2words
    import os
    from django.conf import settings
    from django.http import HttpResponse

    invoice = Invoice.objects.get(id=invoice_id)
    items = invoice.items.all()
    customer = invoice.customer

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # ===== Colors (from uploaded PDF: clean grayscale) =====
    black = colors.black
    white = colors.white
    gray = colors.Color(0.6, 0.6, 0.6)
    light_gray = colors.Color(0.95, 0.95, 0.95)

    # ===== Pagination settings =====
    ITEMS_PER_PAGE = 11
    current_page = 1
    total_pages = (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    item_counter = 1

    # ===== Header =====
    def draw_header():
        # Logo handling
        logo_path = None
        logo_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'logo.png') if settings.STATIC_ROOT else None,
        ]
        for path in [p for p in logo_paths if p]:
            if os.path.exists(path):
                logo_path = path
                break

        if logo_path:
            try:
                p.drawImage(logo_path, 30, height - 140, width=200, height=120, preserveAspectRatio=True)
            except:
                p.setFont("Helvetica-Bold", 20)
                p.drawString(50, height - 100, "Company Logo")

        # Title
        p.setFont("Helvetica-Bold", 26)
        p.setFillColor(black)
        p.drawCentredString(width / 2, height - 60, "INVOICE")

        # Invoice details
        details_x = width - 50
        details_y = height - 120
        p.setFont("Helvetica", 10)
        p.setFillColor(black)
        p.drawRightString(details_x, details_y, f"INVOICE NO {invoice.invoice_number}")
        p.drawRightString(details_x, details_y - 15, f"DATE {invoice.invoice_date.strftime('%d/%m/%Y')}")
        # if invoice.po_number:
        #     p.drawRightString(details_x, details_y - 30, f"PO NO. {invoice.po_number}")

        # Customer + Salesperson + LPO
        box_y = height - 200
        p.rect(50, box_y - 60, width - 100, 60, stroke=1, fill=0)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(60, box_y - 15, "TO")
        p.setFont("Helvetica", 10)
        p.drawString(100, box_y - 15, customer.name)
        p.drawString(60, box_y - 35, f"SALES PERSON: Zubair")
        if invoice.quotation:
            p.drawString(width / 2, box_y - 35, f"LPO DATE: {invoice.quotation.created_at.strftime('%d/%m/%Y')}")

    # ===== Footer =====
    def draw_footer():
        footer_y = 70
        p.setFont("Helvetica-Bold", 9)
        p.setFillColor(black)
        p.drawString(50, footer_y + 35, "Prepared by.")
        p.drawString(200, footer_y + 35, "Received by.")

        p.setFont("Helvetica-Bold", 9)
        p.drawString(50, footer_y + 20, "PAYMENT TERMS")
        p.drawString(200, footer_y + 20, "DELIVERY DATE")

        p.setFont("Helvetica", 9)
        p.drawString(50, footer_y + 8, "COD")
        if invoice.quotation:
            p.drawString(200, footer_y + 8, invoice.quotation.expected_delivery_date.strftime('%d-%b-%y'))

        # Bank details
        p.setFont("Helvetica-Bold", 9)
        p.drawString(50, footer_y - 5, "BANK DETAILS : IFEX PR AND ADVERTISING EST")
        p.setFont("Helvetica", 8)
        p.drawString(50, footer_y - 18, "ADCB : SHARJAH MAIN BRANCH, SWIFT CODE : ADCBAEAA060")
        p.drawString(50, footer_y - 30, "IBAN : AE02 0030 0130 5885 8920 001")

        # TRN
        p.setFont("Helvetica-Bold", 9)
        p.drawRightString(width - 50, footer_y - 18, "TRN. 104106033400003")
        p.drawRightString(width - 50, footer_y - 33, "TAX INVOICE")

        # Page number
        p.setFont("Helvetica", 8)
        p.setFillColor(gray)
        p.drawRightString(width - 50, footer_y - 50, f"Page {current_page} of {total_pages}")

    # ===== Items table =====
    def draw_items(start_idx, end_idx, current_item_counter):
        table_y = height - 300
        col_widths = [30, width - 330, 50, 70, 80]

        header_data = [["NO", "DESCRIPTION", "QTY", "RATE", "LINE TOTAL"]]
        header_table = Table(header_data, colWidths=col_widths)
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), gray),
            ('TEXTCOLOR', (0, 0), (-1, -1), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, gray),
        ]))
        header_table.wrapOn(p, width - 100, height)
        header_table.drawOn(p, 50, table_y)

        # Table rows
        current_y = table_y - 25
        row_height = 20
        styles = getSampleStyleSheet()
        item_style = ParagraphStyle(
            'ItemStyle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica',
            leading=10,
            wordWrap='LTR'
        )

        for idx in range(start_idx, end_idx):
            if idx >= len(items):
                break
            item = items[idx]
            desc = Paragraph(item.item_name, item_style)
            line_total = item.quantity * item.price
            row_data = [
                str(current_item_counter),
                desc,
                str(item.quantity),
                f"{item.price:.2f}",
                f"{line_total:.2f}",
            ]
            row_table = Table([row_data], colWidths=col_widths, rowHeights=[row_height])
            row_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.25, gray),
            ]))
            row_table.wrapOn(p, width - 100, height)
            row_table.drawOn(p, 50, current_y)
            current_y -= row_height
            current_item_counter += 1

        return current_item_counter

    # ===== Totals =====
    def draw_totals():
        totals_y = height - 600
        totals_x = width - 210
        box_width = 160
        box_height = 18

        net_amount = sum(item.quantity * item.price for item in items)
        tax_amount = net_amount * (invoice.tax / 100)
        grand_total = net_amount + tax_amount

        # Net
        p.setFont("Helvetica-Bold", 9)
        p.drawString(totals_x, totals_y, "NET AMOUNT")
        p.drawRightString(totals_x + box_width, totals_y, f"{net_amount:.2f}")

        # VAT
        p.setFont("Helvetica-Bold", 9)
        p.drawString(totals_x, totals_y - 15, "VAT (5%)")
        p.drawRightString(totals_x + box_width, totals_y - 15, f"{tax_amount:.2f}")

        # Total
        p.setFont("Helvetica-Bold", 10)
        p.drawString(totals_x, totals_y - 30, "TOTAL AMOUNT")
        p.drawRightString(totals_x + box_width, totals_y - 30, f"{grand_total:.2f}/-")

        # Amount in words
        amount_words_y = totals_y - 55
        try:
            amount_in_words = num2words(float(grand_total), lang='en').title() + " Dirhams Only"
        except:
            amount_in_words = "Amount in words not available"
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(50, amount_words_y, f"Amount in Words: {amount_in_words}")

        # Footer logo
        logo_path = None
        logo_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'images', 'footerlogo.png'),
            os.path.join(settings.STATIC_ROOT, 'images', 'footerlogo.png') if settings.STATIC_ROOT else None,
        ]
        for path in [p for p in logo_paths if p]:
            if os.path.exists(path):
                logo_path = path
                break
        if logo_path:
            try:
                p.drawImage(logo_path, 40, totals_y - 40, width=100, height=50, preserveAspectRatio=True, mask='auto')
            except:
                p.setFont("Helvetica-Bold", 10)
                p.drawString(40, totals_y - 20, "Company Footer Logo")

    # ===== Main loop =====
    item_counter = 1
    for page in range(total_pages):
        if page > 0:
            p.showPage()
            current_page += 1

        draw_header()
        draw_footer()

        start_idx = page * ITEMS_PER_PAGE
        end_idx = (page + 1) * ITEMS_PER_PAGE
        item_counter = draw_items(start_idx, end_idx, item_counter)

        if page == total_pages - 1:
            draw_totals()

    p.save()
    return response

def disabled_view(request, *args, **kwargs):
    return HttpResponseForbidden("This feature is temporarily disabled.")