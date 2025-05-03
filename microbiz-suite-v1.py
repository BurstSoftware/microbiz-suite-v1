import streamlit as st
import pandas as pd
import pytesseract
from PIL import Image
import pdfkit
import os
from datetime import datetime

# Set page config for mobile-friendly layout
st.set_page_config(page_title="MicroBiz Suite", layout="wide")

# App title and description
st.title("MicroBiz Suite")
st.markdown("A simple invoice generator and receipt tracker for small businesses and contractors.")

# Sidebar for navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.selectbox("Choose a tool", ["Invoice Generator", "Receipt Scanner", "Expense Log"])

# Sample templates for invoices
INVOICE_TEMPLATES = {
    "Professional": {"header_color": "#2c3e50", "font": "Arial"},
    "Modern": {"header_color": "#2980b9", "font": "Helvetica"},
    "Minimal": {"header_color": "#7f8c8d", "font": "Times New Roman"}
}

# Session state for storing invoices and receipts
if "invoices" not in st.session_state:
    st.session_state.invoices = []
if "receipts" not in st.session_state:
    st.session_state.receipts = []

# Invoice Generator
if app_mode == "Invoice Generator":
    st.header("Create an Invoice")
    
    # Invoice form
    with st.form("invoice_form"):
        template = st.selectbox("Select Invoice Template", list(INVOICE_TEMPLATES.keys()))
        business_name = st.text_input("Your Business Name", "Your Company")
        business_email = st.text_input("Your Business Email", "email@example.com")
        client_name = st.text_input("Client Name")
        client_email = st.text_input("Client Email")
        
        # Line items
        st.subheader("Line Items")
        num_items = st.number_input("Number of Items", min_value=1, max_value=10, value=1)
        items = []
        for i in range(num_items):
            cols = st.columns([3, 2, 2])
            description = cols[0].text_input(f"Item {i+1} Description", f"Service {i+1}", key=f"desc_{i}")
            quantity = cols[1].number_input(f"Quantity {i+1}", min_value=1, value=1, key=f"qty_{i}")
            price = cols[2].number_input(f"Price {i+1}", min_value=0.0, value=100.0, key=f"price_{i}")
            items.append({"description": description, "quantity": quantity, "price": price})
        
        # Notes and submit
        notes = st.text_area("Additional Notes (Optional)")
        submitted = st.form_submit_button("Generate Invoice")
        
        if submitted:
            # Calculate total
            total = sum(item["quantity"] * item["price"] for item in items)
            
            # Store invoice data
            invoice_data = {
                "id": len(st.session_state.invoices) + 1,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "business_name": business_name,
                "business_email": business_email,
                "client_name": client_name,
                "client_email": client_email,
                "items": items,
                "total": total,
                "notes": notes,
                "template": template
            }
            st.session_state.invoices.append(invoice_data)
            
            # Generate HTML for PDF
            html_content = f"""
            <html>
            <head><style>
            body {{ font-family: {INVOICE_TEMPLATES[template]["font"]}; }}
            .header {{ background-color: {INVOICE_TEMPLATES[template]["header_color"]}; color: white; padding: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            </style></head>
            <body>
            <div class="header"><h1>Invoice #{invoice_data["id"]}</h1></div>
            <p><b>From:</b> {business_name} ({business_email})</p>
            <p><b>To:</b> {client_name} ({client_email})</p>
            <p><b>Date:</b> {invoice_data["date"]}</p>
            <table>
            <tr><th>Description</th><th>Quantity</th><th>Price</th><th>Total</th></tr>
            """
            for item in items:
                html_content += f"<tr><td>{item['description']}</td><td>{item['quantity']}</td><td>${item['price']:.2f}</td><td>${item['quantity'] * item['price']:.2f}</td></tr>"
            html_content += f"""
            </table>
            <p><b>Total:</b> ${total:.2f}</p>
            <p><b>Notes:</b> {notes}</p>
            <p>Payment via Stripe/Square (Premium Feature)</p>
            <p>E-Signature (Premium Feature)</p>
            </body></html>
            """
            
            # Save HTML and convert to PDF
            with open("invoice.html", "w") as f:
                f.write(html_content)
            pdfkit.from_file("invoice.html", "invoice.pdf")
            
            # Display download button
            with open("invoice.pdf", "rb") as f:
                st.download_button("Download Invoice PDF", f, file_name=f"invoice_{invoice_data['id']}.pdf")
            st.success("Invoice generated successfully!")

# Receipt Scanner
elif app_mode == "Receipt Scanner":
    st.header("Scan a Receipt")
    
    uploaded_file = st.file_uploader("Upload Receipt Image", type=["jpg", "png"])
    if uploaded_file:
        # Save and process image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Receipt", use_column_width=True)
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image)
        st.text_area("Extracted Text", text, height=200)
        
        # Form to log receipt
        with st.form("receipt_form"):
            vendor = st.text_input("Vendor Name", value=text[:20] if text else "")
            amount = st.number_input("Amount", min_value=0.0, value=0.0)
            date = st.date_input("Date", value=datetime.now())
            category = st.selectbox("Category", ["Travel", "Meals", "Supplies", "Other"])
            submitted = st.form_submit_button("Log Receipt")
            
            if submitted:
                receipt_data = {
                    "id": len(st.session_state.receipts) + 1,
                    "vendor": vendor,
                    "amount": amount,
                    "date": date.strftime("%Y-%m-%d"),
                    "category": category
                }
                st.session_state.receipts.append(receipt_data)
                st.success("Receipt logged successfully!")

# Expense Log
elif app_mode == "Expense Log":
    st.header("Expense Log")
    
    if st.session_state.receipts:
        df = pd.DataFrame(st.session_state.receipts)
        st.dataframe(df)
        
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button("Download Expense Log as CSV", csv, file_name="expense_log.csv", mime="text/csv")
    else:
        st.info("No receipts logged yet.")
    
    if st.session_state.invoices:
        st.subheader("Invoices")
        invoice_df = pd.DataFrame([
            {"ID": inv["id"], "Client": inv["client_name"], "Total": inv["total"], "Date": inv["date"]}
            for inv in st.session_state.invoices
        ])
        st.dataframe(invoice_df)
        
        # Export to CSV
        csv = invoice_df.to_csv(index=False)
        st.download_button("Download Invoices as CSV", csv, file_name="invoices.csv", mime="text/csv")
