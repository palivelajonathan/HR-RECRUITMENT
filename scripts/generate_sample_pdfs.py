"""
Generates synthetic, safe sample PDF documents for Milestone 1 testing.

Outputs:
- data/sample/resumes/resume_alex_chen.pdf
- data/sample/resumes/resume_priya_sharma.pdf
- data/sample/job_descriptions/jd_senior_backend_lead.pdf
- data/sample/policies/policy_leave_and_attendance.pdf

No real candidate PII is included.
"""

from pathlib import Path
from fpdf import FPDF


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
    print(f"Generated: {file_path}")


def main():
    base_dir = Path("./data/sample")

    # 1. Resume: Alex Chen (Backend & Distributed Systems)
    alex_paragraphs = [
        "Candidate Name: Alex Chen | Candidate ID: cand_alex_chen",
        "Role: Senior Backend & Distributed Systems Engineer | Experience: 6.5 Years",
        "Summary: Highly experienced software engineer specializing in distributed systems, asynchronous event architectures, microservices, and high-volume data pipelines.",
        "Core Technical Skills: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, Apache Kafka, Distributed Transactions, Microservices, CI/CD, Linux.",
        "Professional Experience:",
        "- Staff Platform Engineer at CloudTech Systems (2022 - Present): Architected microservices with Python and FastAPI handling 45,000 requests/sec. Orchestrated container workloads using Kubernetes and Helm.",
        "- Senior Backend Engineer at FinStream Corp (2019 - 2022): Designed robust database schemas in PostgreSQL, implemented distributed caching using Redis clusters, and optimized slow SQL queries.",
        "Education: Bachelor of Science in Computer Science, State University.",
    ]
    create_pdf(
        base_dir / "resumes" / "resume_alex_chen.pdf",
        "Curriculum Vitae - Alex Chen",
        alex_paragraphs,
    )

    # 2. Resume: Priya Sharma (Frontend & UI Engineering)
    priya_paragraphs = [
        "Candidate Name: Priya Sharma | Candidate ID: cand_priya_sharma",
        "Role: Frontend Lead & Design Systems Engineer | Experience: 5.0 Years",
        "Summary: Passionate frontend architect experienced in building enterprise web dashboards, component libraries, and interactive applications.",
        "Core Technical Skills: TypeScript, React, Next.js, GraphQL, Tailwind CSS, Jest, State Management, Web Performance, HTML5/CSS3.",
        "Professional Experience:",
        "- Frontend Lead at DesignHub Interactive (2021 - Present): Led migration to Next.js App Router, built accessible Design System components used by 12 squads.",
        "- UI Engineer at WebCraft Labs (2019 - 2021): Developed responsive dashboards in React, integrating REST and GraphQL endpoints with client-side caching.",
        "Education: Bachelor of Engineering in Information Technology.",
    ]
    create_pdf(
        base_dir / "resumes" / "resume_priya_sharma.pdf",
        "Curriculum Vitae - Priya Sharma",
        priya_paragraphs,
    )

    # 3. Job Description: Senior Backend Infrastructure Lead
    jd_paragraphs = [
        "Position Title: Senior Backend Infrastructure Lead | Document ID: jd_backend_lead_2026",
        "Department: Engineering Platform Team | Location: Hybrid / Remote",
        "Job Summary: We are seeking an accomplished Senior Backend Infrastructure Lead to spearhead our distributed microservices platform, cloud containerization, and data infrastructure.",
        "Key Responsibilities:",
        "- Architect and scale high-performance REST APIs and background services using Python and FastAPI.",
        "- Deploy, manage, and scale microservices running on Kubernetes clusters and Docker containers.",
        "- Oversee relational database architecture in PostgreSQL, ensuring optimal indexing, replication, and query performance.",
        "Required Qualifications:",
        "- 4+ years of professional backend engineering experience with Python.",
        "- Hands-on proficiency with Docker, Kubernetes, and cloud orchestration.",
        "- Strong experience with relational databases (PostgreSQL) and caching systems (Redis).",
        "Preferred Skills: Experience with Kafka event streaming and LangChain agentic systems.",
    ]
    create_pdf(
        base_dir / "job_descriptions" / "jd_senior_backend_lead.pdf",
        "Job Description - Senior Backend Infrastructure Lead",
        jd_paragraphs,
    )

    # 4. Policy Document: Employee Handbook - Leave & Attendance Policy
    policy_paragraphs = [
        "Policy Title: Corporate Employee Handbook - Annual Leave & Attendance Policy | Document ID: policy_leave_2026",
        "Effective Date: January 1, 2026 | Version: 3.2 | Department: Human Resources",
        "1. Annual Paid Time Off (PTO):",
        "All full-time employees are entitled to 24 business days of paid annual leave per calendar year. Leave requests exceeding 3 consecutive days must be submitted at least 2 weeks in advance through the HR portal.",
        "2. Sick and Medical Leave:",
        "Employees receive 12 days of paid sick leave annually for personal illness or caring for immediate family members. Medical certificates are required for sick leave exceeding 2 consecutive business days.",
        "3. Remote Work & Core Hours:",
        "The company maintains a hybrid work schedule. Employees may work remotely up to 3 days per week. Core collaboration hours during which all team members must be reachable on messaging channels are 10:00 AM to 4:00 PM local time.",
        "4. Sabbatical & Extended Unpaid Leave:",
        "Employees with more than 3 years of continuous service are eligible to apply for an unpaid professional sabbatical of up to 3 months, subject to department head approval.",
    ]
    create_pdf(
        base_dir / "policies" / "policy_leave_and_attendance.pdf",
        "Corporate Policy - Leave, Attendance, and Remote Work Guidelines",
        policy_paragraphs,
    )


if __name__ == "__main__":
    main()
