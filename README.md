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

### Demo Credentials

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `administrator` | `admin` |
| HR Manager | `hr.manager` | `password123` |
| Interviewer | `interviewer` | `password123` |
| Hiring Manager | `hiring.manager` | `password123` |

* * * * *