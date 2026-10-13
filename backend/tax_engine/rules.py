"""
FinEasy AI - Tax Rules Configuration
========================================================================================
CRITICAL DISCLAIMER:
EDUCATIONAL DEMO RULES — NOT FOR ACTUAL TAX FILING
These rules are designed strictly for an engineering college prototype and educational
demonstrations. They do NOT represent official, current, or legally binding Indian tax law.
========================================================================================
"""

from typing import List, Tuple

RULES_VERSION: str = "demo-v1"
DISCLAIMER: str = "EDUCATIONAL DEMO RULES — NOT FOR ACTUAL TAX FILING"

# Demo Standard Deduction (Applied automatically in demo rules if deductions are 0 or lower)
DEMO_STANDARD_DEDUCTION: float = 50000.00

# Demo Health and Education Cess percentage (4%)
DEMO_CESS_RATE: float = 0.04

# Demo Tax Slabs: (Lower Bound, Upper Bound, Rate)
# Note: None indicates unbounded upper limit.
DEMO_TAX_SLABS: List[Tuple[float, float | None, float]] = [
    (0.0, 300000.0, 0.00),         # Up to 3,00,000 : Nil
    (300000.0, 600000.0, 0.05),     # 3,00,001 to 6,00,000 : 5%
    (600000.0, 900000.0, 0.10),     # 6,00,001 to 9,00,000 : 10%
    (900000.0, 1200000.0, 0.15),   # 9,00,001 to 12,00,000 : 15%
    (1200000.0, 1500000.0, 0.20),  # 12,00,001 to 15,00,000 : 20%
    (1500000.0, None, 0.30),       # Above 15,00,000 : 30%
]

# Demo Section 87A Rebate Threshold:
# Under demo rules, taxable income <= 7,00,000 receives rebate equal to tax payable
DEMO_REBATE_87A_THRESHOLD: float = 700000.0
