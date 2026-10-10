# Training Bills Level 2 Evidence & Quality Review

Reviewing answers for IESCO_0004, KESC_0004, LESCO_0005, and LESCO_0006 against Level 1 ground truth.

## Bill: IESCO_0004

### Level 1 Ground Truth Reference:
- Provider: IESCO
- Tariff: A-1A(01)
- Bill Month: 2026-09
- Units Consumed: 158
- Total Charges: PKR 6102
- Total Taxes: PKR 498
- Current Bill: PKR 3267
- Arrears: PKR 0
- Payable within due date: PKR 3535
- Payable after due date: PKR 3812

### Level 2 Q&A Evaluations:

**Q1: How much of my bill is taxes?**

> Taxes on your bill amount to PKR 498, which is computed as 15.24% of your current bill (PKR 498 out of PKR 3267).

**Q2: How many months in my history went above 200 units?**

> Based on your 12 months of recorded history, 0 months went above 200 units.

**Q3: How many units did I consume this month compared to my historical average?**

> You consumed 158 units this month. This is 39.58 units higher than your average (33.42% above average, based on 12 months of recorded history).

**Q4: What is the single largest charge on my bill?**

> The single largest charge on your bill is the FPA (Fuel Price Adjustment) amount of PKR 267.

**Q5: When is the due date for this bill and how much should I pay?**

> The due date for this bill is 2026-10-08, and you should pay PKR 3535 within the due date.

**Q6: How much will I have to pay if I pay after the due date?**

> If you pay after the due date, you will have to pay PKR 3812.

**Q7: What is the Fuel Price Adjustment (FPA) charge on this bill?**

> The Fuel Price Adjustment (FPA) charge on this bill is PKR 267.

**Q8: Do I have any previous dues or arrears carry-forward on this bill?**

> You do not have any previous dues or arrears carry-forward on this bill; your arrears are PKR 0.

**Q9: What was my highest monthly consumption recorded in the history table?**

> Your highest monthly consumption recorded in the history table was 197 units in Jun 26.

**Q10: What is my sanctioned load and tariff category?**

> Your sanctioned load is 3 kW and your tariff category is A-1A(01) (Domestic).

**Q11: What are the meter reading dates and readings for this billing cycle?**

> The reading date for this billing cycle is 2026-09-25. The previous reading was 9301 and the current reading is 9459.

**Q12: Can you provide a breakdown of all the taxes and duties charged?**

> This could not be determined from the bill, as individual tax lines are not detailed on the bill summary.

---

## Bill: KESC_0004

### Level 1 Ground Truth Reference:
- Provider: KE
- Tariff: A1-R
- Bill Month: 2026-06
- Units Consumed: 901
- Total Charges: PKR 38098.01
- Total Taxes: PKR 7472.24
- Current Bill: PKR 45570.25
- Arrears: PKR -91877.02
- Payable within due date: PKR 0.0
- Payable after due date: PKR 0.0

### Level 2 Q&A Evaluations:

**Q1: How much of my bill is taxes?**

> Taxes make up 16.4% of your current bill, which is PKR 7472.24 out of PKR 45570.25 (computed from the bill's tax and total charges breakdown).

**Q2: How many months in my history went above 200 units?**

> 0 months in your history went above 200 units (computed from 0 recorded months of history).

**Q3: How many units did I consume this month compared to my historical average?**

> You consumed 901 units this month. Your historical average monthly consumption could not be determined from the bill because the historical usage table does not record units.

**Q4: What is the single largest charge on my bill?**

> The single largest charge on your bill is energy at PKR 26257.99.

**Q5: When is the due date for this bill and how much should I pay?**

> The due date for this bill is 13th Jul 2026, and you should pay PKR 0.0.

**Q6: How much will I have to pay if I pay after the due date?**

> If you pay after the due date, you will have to pay PKR 0.0 (late_payment_difference_pkr: computed as PKR 0.0).

**Q7: What is the Fuel Price Adjustment (FPA) charge on this bill?**

> The Fuel Price Adjustment (FPA) charge on this bill is PKR 354.19.

**Q8: Do I have any previous dues or arrears carry-forward on this bill?**

> Yes, you have a credit carry-forward of PKR -91877.02 in previous dues or arrears.

**Q9: What was my highest monthly consumption recorded in the history table?**

> Your highest monthly consumption recorded in the history table could not be determined from the bill because unit counts are not listed in the billing history.

**Q10: What is my sanctioned load and tariff category?**

> Your sanctioned load is 10 kW and your tariff category is A1-R.

**Q11: What are the meter reading dates and readings for this billing cycle?**

> The reading date is 2026-06-25. For off-peak energy, the previous reading is 1163.29 and the current reading is 1923.73. For peak energy, the previous reading is 402.35 and the current reading is 542.85.

**Q12: Can you provide a breakdown of all the taxes and duties charged?**

> The breakdown of all taxes and duties charged is: electricity_duty (PKR 520.85) and gst (PKR 6951.39).

---

## Bill: LESCO_0005

### Level 1 Ground Truth Reference:
- Provider: LESCO
- Tariff: A-1b(03)
- Bill Month: 2026-07
- Units Consumed: 1017
- Total Charges: PKR 17367.77
- Total Taxes: PKR 3358.23
- Current Bill: PKR 54770
- Arrears: PKR -75496
- Payable within due date: PKR -54770
- Payable after due date: PKR None

### Level 2 Q&A Evaluations:

**Q1: How much of my bill is taxes?**

> Taxes on your bill total PKR 3358.23, which is 6.13% of your current bill (PKR 3358.23 out of PKR 54770), computed based on the current bill details.

**Q2: How many months in my history went above 200 units?**

> Based on 12 months of recorded history, there are 3 months in your history that went above 200 units (specifically JUL 25 with 781 units, AUG 25 with 225 units, and JAN 26 with 359 units). If you include the current month, the total is 4 months.

**Q3: How many units did I consume this month compared to my historical average?**

> You consumed 1017 units this month, which is 1324.58 units higher than your historical average (0.0% above average), computed across 12 months of recorded history.

**Q4: What is the single largest charge on my bill?**

> This could not be determined from the bill as individual charges are not listed.

**Q5: When is the due date for this bill and how much should I pay?**

> The due date for this bill is 2026-07-30. You have a credit balance/credit carried forward, with a payable amount of PKR -54770 (or 54770CR).

**Q6: How much will I have to pay if I pay after the due date?**

> This could not be determined from the bill since the payable after the due date is listed as null.

**Q7: What is the Fuel Price Adjustment (FPA) charge on this bill?**

> This could not be determined from the bill as specific FPA charges are not listed.

**Q8: Do I have any previous dues or arrears carry-forward on this bill?**

> Yes, you have a previous dues or arrears carry-forward of PKR -75496, representing a credit carried forward.

**Q9: What was my highest monthly consumption recorded in the history table?**

> Your highest monthly consumption recorded in the history table was 781 units in JUL 25.

**Q10: What is my sanctioned load and tariff category?**

> Your sanctioned load is 10 kW and your tariff category is A-1b(03).

**Q11: What are the meter reading dates and readings for this billing cycle?**

> The reading date for this billing cycle is 2026-07-17, with a previous reading of 11561 and a current reading of 12578.

**Q12: Can you provide a breakdown of all the taxes and duties charged?**

> This could not be determined from the bill as a detailed breakdown of individual taxes and duties is not provided.

---

## Bill: LESCO_0006

### Level 1 Ground Truth Reference:
- Provider: LESCO
- Tariff: A-2a(04)
- Bill Month: 2026-08
- Units Consumed: 65
- Total Charges: PKR 3777.49
- Total Taxes: PKR 1723.51
- Current Bill: PKR 5501
- Arrears: PKR 39411.5
- Payable within due date: PKR 44912
- Payable after due date: PKR 45263

### Level 2 Q&A Evaluations:

**Q1: How much of my bill is taxes?**

> Taxes make up PKR 1723.51 of your current bill, which is 31.33% of your current bill (computed based on the current bill of PKR 5501).

**Q2: How many months in my history went above 200 units?**

> Based on the 12 months of recorded history provided in the bill, 9 months went above 200 units: AUG 25 (440 units), SEP 25 (407 units), OCT 25 (243 units), DEC 25 (206 units), MAR 26 (257 units), APR 26 (264 units), MAY 26 (434 units), JUN 26 (350 units), and JUL 26 (225 units).

**Q3: How many units did I consume this month compared to my historical average?**

> You consumed 65 units this month. Based on your 12 months of recorded history, your average monthly consumption is 275.25 units. This month is 210.25 units lower than your average (76.39% below average, computed from your historical records).

**Q4: What is the single largest charge on my bill?**

> This could not be determined from the bill.

**Q5: When is the due date for this bill and how much should I pay?**

> The due date for this bill is 2026-09-09, and you should pay PKR 44912 within the due date.

**Q6: How much will I have to pay if I pay after the due date?**

> If you pay after the due date, you will have to pay PKR 45263, which includes a late payment difference of PKR 351.

**Q7: What is the Fuel Price Adjustment (FPA) charge on this bill?**

> This could not be determined from the bill.

**Q8: Do I have any previous dues or arrears carry-forward on this bill?**

> Yes, you have unpaid past dues/arrears amounting to PKR 39411.5 carried forward on this bill.

**Q9: What was my highest monthly consumption recorded in the history table?**

> Your highest monthly consumption recorded in the history table was 440 units in AUG 25.

**Q10: What is my sanctioned load and tariff category?**

> Your sanctioned load is 1 kW and your tariff category is A-2a(04).

**Q11: What are the meter reading dates and readings for this billing cycle?**

> The reading date for this billing cycle is 2026-08-26. The previous reading is 22238 and the current reading is 22303.

**Q12: Can you provide a breakdown of all the taxes and duties charged?**

> This could not be determined from the bill.

---
