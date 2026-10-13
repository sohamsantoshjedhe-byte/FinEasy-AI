"""
FinEasy AI - Sample Form 16 PDF Generator
Creates a synthetic Form 16 PDF with realistic text layer for testing and demonstration.
Can run standalone with zero external dependencies (pure Python PDF generator).
"""

import os

FORM_16_TEXT = """FORM NO. 16
[See rule 31(1)(a)]
Certificate under section 203 of the Income-tax Act, 1961 for tax deducted at source on salary

Certificate No: CERT-2025-0098471
Last updated on: 15-May-2025

PART A
Name and address of the Employer:
Infosys Technologies Global Ltd
Electronic City, Hosur Road, Bangalore, Karnataka - 560100
PAN of Deductor: BLRT09876K
TAN of Deductor: BLRT12345C

Name and address of the Employee:
Rajesh Kumar Sharma
Flat 402, Green Meadows, Indiranagar, Bangalore - 560038
PAN of Employee: ABCDE1234F

Assessment Year: 2025-26
Financial Year: 2024-25
Period with the Employer: 01-Apr-2024 to 31-Mar-2025

PART B (Details of Salary Paid and Tax Deducted)
1. Gross Salary:
   (a) Salary as per provisions contained in section 17(1): Rs. 950000.00
   (b) Value of perquisites under section 17(2): Rs. 0.00
   (c) Profits in lieu of salary under section 17(3): Rs. 0.00
   (d) Total Gross Salary: Rs. 950000.00

2. Deductions under section 16:
   (a) Standard deduction under section 16(ia): Rs. 50000.00
   (b) Tax on Employment: Rs. 2400.00

3. Total Deductions under Chapter VI-A:
   (a) Section 80C (Life Insurance, PF, PPF): Rs. 150000.00
   (b) Section 80D (Health Insurance): Rs. 25000.00
   Total Deductible Amount: Rs. 175000.00

4. Total Taxable Income: Rs. 722600.00

5. Tax on Total Income:
   Tax calculated: Rs. 56250.00
   Health and Education Cess (4%): Rs. 2250.00
   Total Tax Payable: Rs. 58500.00

6. Tax Deducted at Source (TDS):
   Total Tax Deducted and Deposited to Central Government: Rs. 52000.00
   Net Tax Payable / Refundable: Rs. 6500.00

Verification:
I, Rajesh Kumar Sharma, do hereby certify that the information given above is true,
complete and correct based on the books of account, documents and Form 26AS.
Place: Bangalore
Date: 20-May-2025
"""


def generate_pure_python_pdf(output_path: str, text: str):
    """Generates a valid PDF file with selectable text using raw PDF-1.4 primitives."""
    lines = text.strip().split("\n")
    
    # Format text for PDF stream
    stream_lines = ["BT", "/F1 10 Tf", "50 780 Td", "14 TL"]
    for line in lines:
        escaped_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"({escaped_line}) '")
    stream_lines.append("ET")
    
    stream_content = "\n".join(stream_lines).encode("latin-1")
    stream_len = len(stream_content)

    pdf_parts = [
        b"%PDF-1.4\n",
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("latin-1") + stream_content + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    # Calculate xref offsets
    xref_offsets = []
    current_offset = 0
    for part in pdf_parts:
        xref_offsets.append(current_offset)
        current_offset += len(part)

    xref = (
        f"xref\n0 6\n0000000000 65535 f \n"
        f"{xref_offsets[1]:010d} 00000 n \n"
        f"{xref_offsets[2]:010d} 00000 n \n"
        f"{xref_offsets[3]:010d} 00000 n \n"
        f"{xref_offsets[4]:010d} 00000 n \n"
        f"{xref_offsets[5]:010d} 00000 n \n"
    ).encode("latin-1")

    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        f"startxref\n{current_offset}\n%%EOF\n"
    ).encode("latin-1")

    full_pdf_data = b"".join(pdf_parts) + xref + trailer

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(full_pdf_data)

    print(f"Generated demo Form 16 PDF at: {output_path} ({len(full_pdf_data)} bytes)")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_pdf = os.path.join(current_dir, "demo_form16.pdf")
    generate_pure_python_pdf(target_pdf, FORM_16_TEXT)
