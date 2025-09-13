* * * * *

📘 Frappe HRMS Assignment -- Girman Technologies
===============================================

📌 Overview
-----------

This repository contains my submission for the **Frappe Developer Assignment** (Girman Technologies).\
It demonstrates customizations in ERPNext HRMS module covering **Recruitment, Employee Lifecycle, Payroll, Taxation, and Custom Doctypes**, along with **Git best practices**.

* * * * *

⚙️ Setup Instructions
---------------------

### Prerequisites

-   Python 3.10+

-   Node.js & Yarn

-   Redis, MariaDB, wkhtmltopdf

-   Bench CLI

### Steps to Install

```bash
# Clone repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Setup bench environment
bench init frappe-bench
cd frappe-bench

# Get apps
bench get-app erpnext
bench get-app hrms
bench get-app <this-repo>

# Create site
bench new-site hrms.local
bench --site hrms.local install-app erpnext hrms <this-repo>

# Start server
bench start

```

🚀 Features Implemented
-----------------------

### Part 1 -- HRMS & Recruitment

-   Custom Recruitment Workflow: `Job Opening → Application → Screening → Interview → Offer → Hired`

-   Role-based permissions for HR Manager, Interviewer, Hiring Manager

-   Custom field in *Job Applicant*: `Source of Application`

-   Report/Dashboard: Applicants per source

* * * * *

### Part 2 -- Employee Lifecycle

-   Employee lifecycle states: `Joining → Probation → Confirmation → Exit`

-   Automation:

    -   Auto-update status on confirmation

    -   Generate **Experience Letter PDF** on exit

* * * * *

### Part 3 -- Salary Structure & Payroll

-   Salary Structure with: Basic, HRA, Special Allowance, PF, Professional Tax

-   Payroll Entry for multiple employees

-   Custom Payslip Print Format with branding

* * * * *

### Part 4 -- Tax Regime Implementation

-   Two Salary Structures: Old Regime & New Regime

-   Custom field in Employee: `Tax Regime Preference`

-   Payroll auto-selects salary structure based on preference

-   Report: Old vs New tax deduction comparison

* * * * *

### Part 5 -- Customization

-   Custom Doctype: **Employee Investment Declaration**

    -   Section 80C (LIC, PPF, ELSS, etc.)

    -   Section 80D (Medical Insurance)

    -   Other Exemptions

-   Integrated into Payroll for tax calculations

* * * * *


📂 [View All Screenshots](https://drive.google.com/drive/folders/1X2Rgqzm986Oshv_xfeWKOnvRfvaA_tOk?usp=sharing)
