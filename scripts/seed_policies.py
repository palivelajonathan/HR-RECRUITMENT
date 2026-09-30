"""
Seeds realistic corporate policy documents into data/sample/policies/
and indexes them into the Chroma vector store via DEFAULT_WORKFLOW_SERVICE.
"""

import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fpdf import FPDF
from capabl_core.workflow import DEFAULT_WORKFLOW_SERVICE


def create_pdf(file_path: Path, title: str, paragraphs: list[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, text=title, new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    for p in paragraphs:
        pdf.multi_cell(0, 6, text=p)
        pdf.ln(3)

    pdf.output(str(file_path))
    print(f"Generated PDF: {file_path}")


def main():
    base_dir = REPO_ROOT / "data" / "sample" / "policies"
    base_dir.mkdir(parents=True, exist_ok=True)

    policies = [
        {
            "id": "policy_leave_2026",
            "filename": "policy_leave_and_attendance.pdf",
            "title": "Corporate Employee Handbook - Annual Leave & Attendance Policy",
            "paragraphs": [
                "Policy Title: Corporate Employee Handbook - Annual Leave & Attendance Policy | Document ID: policy_leave_2026",
                "Effective Date: January 1, 2026 | Version: 3.2 | Department: Human Resources | Status: Active",
                "1. Annual Paid Time Off (PTO):",
                "All full-time employees are entitled to 24 business days of paid annual leave per calendar year. Leave requests exceeding 3 consecutive days must be submitted at least 2 weeks in advance through the HR portal.",
                "2. Sick and Medical Leave:",
                "Employees receive 12 days of paid sick leave annually for personal illness or caring for immediate family members. Medical certificates are required for sick leave exceeding 2 consecutive business days.",
                "3. Remote Work & Core Hours:",
                "The company maintains a hybrid work schedule. Employees may work remotely up to 3 days per week. Core collaboration hours during which all team members must be reachable on messaging channels are 10:00 AM to 4:00 PM local time.",
                "4. Sabbatical & Extended Unpaid Leave:",
                "Employees with more than 3 years of continuous service are eligible to apply for an unpaid professional sabbatical of up to 3 months, subject to department head approval.",
            ],
        },
        {
            "id": "policy_infosec_2026",
            "filename": "policy_infosec_and_compliance.pdf",
            "title": "Information Security, Access Control & Data Protection Policy",
            "paragraphs": [
                "Policy Title: Information Security, Access Control & Data Protection Policy | Document ID: policy_infosec_2026",
                "Effective Date: February 15, 2026 | Version: 4.1 | Department: Information Security & Compliance | Status: Active",
                "1. Access Control & Multi-Factor Authentication (MFA):",
                "Multi-factor authentication is mandatory on all corporate systems and SSO gateways. Passwords must be at least 14 characters in length and expire every 90 days. Shared accounts are strictly prohibited.",
                "2. Data Classification & Candidate Privacy:",
                "All company data is categorized into Public, Internal, Confidential, or Restricted tiers. Candidate resumes and personal identifying information (PII) are classified as Confidential and must never be exported to unapproved third-party cloud stores.",
                "3. Device Security & Clean Desk Policy:",
                "All corporate laptops must maintain full-disk encryption (BitLocker/FileVault). Screens must lock automatically after 5 minutes of inactivity. Physical documents containing recruitment data must be stored in locked file cabinets.",
                "4. Security Incident Reporting:",
                "Any suspected security breach, compromised credential, or unauthorized access to candidate records must be reported immediately to security@capabl.internal within 60 minutes of discovery.",
            ],
        },
        {
            "id": "policy_conduct_dei_2026",
            "filename": "policy_code_of_conduct.pdf",
            "title": "Workplace Ethics, Anti-Harassment & Equal Opportunity Guidelines",
            "paragraphs": [
                "Policy Title: Workplace Ethics, Anti-Harassment & Equal Opportunity Guidelines | Document ID: policy_conduct_dei_2026",
                "Effective Date: January 15, 2026 | Version: 2.4 | Department: Legal & People Experience | Status: Active",
                "1. Equal Employment Opportunity (EEO) & Anti-Discrimination:",
                "The organization provides equal employment opportunities to all applicants and employees regardless of race, color, religion, gender, sexual orientation, national origin, age, disability, or genetic information.",
                "2. Anti-Harassment & Zero Tolerance Standards:",
                "Harassment, intimidation, bullying, and hostile conduct are strictly prohibited in physical and remote workplace channels. Violations result in disciplinary action up to immediate termination of employment.",
                "3. Conflicts of Interest & External Advisory Roles:",
                "Employees must avoid outside commitments that conflict with company business. Any secondary employment, paid advisory board role, or consulting engagement requires prior written approval from the Head of People.",
                "4. Whistleblower Protection & Non-Retaliation:",
                "Employees who report suspected compliance violations in good faith are protected from retaliation. Reports may be filed confidentially via the compliance ethics hotline at ethics@capabl.internal.",
            ],
        },
        {
            "id": "policy_compensation_travel_2026",
            "filename": "policy_travel_and_expenses.pdf",
            "title": "Business Travel, Expense Reimbursement & Learning Stipend Policy",
            "paragraphs": [
                "Policy Title: Business Travel, Expense Reimbursement & Learning Stipend Policy | Document ID: policy_compensation_travel_2026",
                "Effective Date: March 1, 2026 | Version: 1.8 | Department: Finance & Operations | Status: Active",
                "1. Corporate Travel & Lodging Guidelines:",
                "All flights under 6 hours flight time must be booked in standard economy class. Hotel accommodations are reimbursed up to $220/night in standard metropolitan areas and $300/night in high-cost tier-1 cities.",
                "2. Per Diem Meal & Incidental Allowances:",
                "Business travel meal expenses are capped at a daily per diem rate of $85. Itemized receipts are required for all individual expenses exceeding $25. Alcoholic beverages are not eligible for reimbursement.",
                "3. Professional Development & Learning Allowance:",
                "Full-time employees receive an annual budget of $1,500 for job-related conferences, professional certifications, books, and courses. Approvals are processed through the Manager Expense Portal.",
                "4. Remote Workspace & Wellness Stipend:",
                "Remote-eligible employees receive a one-time $600 ergonomic equipment grant upon hire, plus a recurring $75 monthly wellness and connectivity stipend.",
            ],
        },
        {
            "id": "policy_hiring_recruitment_2026",
            "filename": "policy_recruitment_standards.pdf",
            "title": "Structured Hiring, Recruiter Ethics & Interview Standards",
            "paragraphs": [
                "Policy Title: Structured Hiring, Recruiter Ethics & Interview Standards | Document ID: policy_hiring_recruitment_2026",
                "Effective Date: February 1, 2026 | Version: 3.0 | Department: Talent Acquisition & HR | Status: Active",
                "1. Deterministic Requirement Verification:",
                "Recruiters and interviewers must evaluate candidates strictly against deterministic job requirements extracted from approved job descriptions. Subjective scoring formulas or arbitrary percentages are barred.",
                "2. Calibrated Interview Panels:",
                "All interview panels must consist of at least two calibrated interviewers. Independent written notes and structured feedback must be submitted within 24 hours of interview completion.",
                "3. Candidate Data Retention & Privacy:",
                "Candidate resumes, interview feedback, and evaluation records are retained for 12 months for compliance auditing, after which they are automatically archived or purged upon candidate request.",
                "4. Consequential Action Authorization Gatekeeper:",
                "Interview invitations and calendar bookings strictly require explicit human confirmation. State mutations must never be dispatched automatically without human recruiter authorization.",
            ],
        },
    ]

    for p in policies:
        pdf_path = base_dir / p["filename"]
        create_pdf(pdf_path, p["title"], p["paragraphs"])
        try:
            chunks_count = DEFAULT_WORKFLOW_SERVICE.ingest_document(
                file_path_or_bytes=pdf_path,
                document_type="policy",
                document_id=p["id"],
                filename=p["filename"],
                replace=True,
            )
            print(f"Indexed policy '{p['id']}' ({chunks_count} chunks) into Chroma.")
        except Exception as e:
            print(f"Failed to index '{p['id']}': {e}")


if __name__ == "__main__":
    main()
