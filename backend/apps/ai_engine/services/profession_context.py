"""
CALDIM Profession-Aware Context & Intelligence Service.
Maps visitor job titles and professional designations to extensible professional categories,
and constructs tailored cognitive reasoning directives, diagnostic lenses, vocabulary,
and decision criteria for the real LLM consultation engine.
"""
import re
from typing import Dict, Any, Optional, Tuple


class ProfessionCategory:
    PRODUCTION_MANUFACTURING = "production_manufacturing"
    MAINTENANCE_RELIABILITY = "maintenance_reliability"
    QUALITY_ASSURANCE = "quality_assurance"
    INDUSTRIAL_PROCESS = "industrial_process"
    SOFTWARE_IT = "software_it"
    BUSINESS_LEADERSHIP = "business_leadership"
    FINANCE_ACCOUNTING = "finance_accounting"
    HR_WORKFORCE = "hr_workforce"
    SALES_MARKETING = "sales_marketing"
    SUPPLY_CHAIN_LOGISTICS = "supply_chain_logistics"
    CONSULTANT_RESEARCHER = "consultant_researcher"
    GENERAL_PROFESSIONAL = "general_professional"


# Mapping patterns (regex tuples) to resolve free-form job titles into categories
ROLE_PATTERNS = [
    (
        ProfessionCategory.PRODUCTION_MANUFACTURING,
        r"\b(production|manufacturing|plant\s*manager|factory|shopfloor|shift\s*supervisor|assembly|line\s*manager|mill\s*manager|works\s*manager|fabrication\s*manager|operations\s*manager)\b",
    ),
    (
        ProfessionCategory.MAINTENANCE_RELIABILITY,
        r"\b(maintenance|reliability|equipment|technician|tooling|preventive|pm\s*engineer|electrical\s*engineer|mechanical\s*engineer|instrumentation|millwright|breakdown)\b",
    ),
    (
        ProfessionCategory.QUALITY_ASSURANCE,
        r"\b(quality|qa|qc|inspection|compliance|six\s*sigma|iso|metrology|calibration|testing|audit|qms)\b",
    ),
    (
        ProfessionCategory.INDUSTRIAL_PROCESS,
        r"\b(industrial\s*engineer|process\s*engineer|continuous\s*improvement|kaizen|lean|value\s*stream|method\s*engineer|operational\s*excellence|op-ex)\b",
    ),
    (
        ProfessionCategory.SOFTWARE_IT,
        r"\b(software|developer|programmer|devops|architect|cto|tech\s*lead|systems\s*admin|cloud|database|it\s*manager|data\s*engineer|fullstack|backend|frontend)\b",
    ),
    (
        ProfessionCategory.SUPPLY_CHAIN_LOGISTICS,
        r"\b(supply\s*chain|logistics|warehouse|procurement|purchasing|inventory|dispatcher|fleet|freight|stores\s*manager|materials\s*manager)\b",
    ),
    (
        ProfessionCategory.FINANCE_ACCOUNTING,
        r"\b(finance|financial|cfo|controller|accountant|auditor|billing|bookkeeper|treasurer|costing|budget)\b",
    ),
    (
        ProfessionCategory.HR_WORKFORCE,
        r"\b(hr|human\s*resources|talent|recruiter|recruitment|payroll|people\s*ops|workforce|training|timekeeping)\b",
    ),
    (
        ProfessionCategory.SALES_MARKETING,
        r"\b(sales|marketing|commercial|business\s*development|bd|account\s*executive|customer\s*success|client\s*relations|revenue)\b",
    ),
    (
        ProfessionCategory.BUSINESS_LEADERSHIP,
        r"\b(owner|founder|ceo|managing\s*director|md|general\s*manager|gm|president|partner|executive|director|co-founder|proprietor)\b",
    ),
    (
        ProfessionCategory.CONSULTANT_RESEARCHER,
        r"\b(consultant|advisor|analyst|researcher|scientist|professor|student|intern|scholar|fellow)\b",
    ),
]


CATEGORY_DIRECTIVES: Dict[str, Dict[str, Any]] = {
    ProfessionCategory.PRODUCTION_MANUFACTURING: {
        "title": "Production & Manufacturing Management",
        "diagnostic_lens": (
            "Focus on Overall Equipment Effectiveness (OEE), throughput bottlenecks, shift handoff discrepancies, "
            "takt time vs cycle time variances, scrap and rework rates, and operational scheduling friction. "
            "Probe into how shopfloor machine logs and technician attendance feed into daily production targets."
        ),
        "vocabulary": [
            "OEE (Availability, Performance, Quality)",
            "Takt Time & Cycle Time",
            "WIP (Work-in-Progress)",
            "Bottleneck Stations",
            "Changeover Lag (SMED)",
            "Shift Handoff Protocols",
            "Shopfloor Run-Hours",
        ],
        "decision_criteria": (
            "Maximizing operational uptime, eliminating production schedule slippage, preventing manual spreadsheet "
            "reconciliation delays, and ensuring shift worker attendance accuracy."
        ),
        "preferred_artifacts": (
            "Shift Production Flowchart, Capacity Bottleneck Breakdown, Phased Shopfloor Deployment Plan."
        ),
    },
    ProfessionCategory.MAINTENANCE_RELIABILITY: {
        "title": "Maintenance & Reliability Engineering",
        "diagnostic_lens": (
            "Focus on Mean Time Between Failures (MTBF), Mean Time To Repair (MTTR), recurring breakdown patterns, "
            "vibration/thermal wear indicators, operating run-hour intervals, spare parts buffer stockouts, and "
            "unplanned versus planned maintenance ratios."
        ),
        "vocabulary": [
            "MTBF & MTTR",
            "Preventive Maintenance (PM) Schedules",
            "Operating Run-Hour Triggers",
            "Critical Spares Inventory",
            "Condition Monitoring (Vibration/Thermal)",
            "CMMS / Maintenance Ticketing",
            "Root-Cause Failure Analysis (RCFA)",
        ],
        "decision_criteria": (
            "Eliminating catastrophic line shutdowns, automating work order generation directly from machine run-hours, "
            "and ensuring synchronized spare parts availability before scheduled servicing."
        ),
        "preferred_artifacts": (
            "Preventive Maintenance Workflow, Equipment Servicing Trigger Matrix, Spare Parts Consumption Flow."
        ),
    },
    ProfessionCategory.QUALITY_ASSURANCE: {
        "title": "Quality Assurance & Control",
        "diagnostic_lens": (
            "Focus on Defect Parts Per Million (PPM), First Pass Yield (FPY), Non-Conformance Reports (NCR), "
            "statistical process control (SPC) out-of-spec triggers, calibration schedules, and end-to-end batch traceability."
        ),
        "vocabulary": [
            "Defect PPM",
            "First Pass Yield (FPY)",
            "NCR & CAPA Tracking",
            "SPC Control Limits",
            "ISO 9001 / IATF 16949 Auditability",
            "Metrology Calibration Logs",
            "Batch / Heat Number Traceability",
        ],
        "decision_criteria": (
            "Preventing defective material escapes, guaranteeing full component genealogy across operations, and "
            "automating quality gate sign-offs without paper checklist latency."
        ),
        "preferred_artifacts": (
            "Quality Gate Inspection Matrix, CAPA Root-Cause Pareto Diagram, Audit Traceability Workflow."
        ),
    },
    ProfessionCategory.INDUSTRIAL_PROCESS: {
        "title": "Industrial Engineering & Process Improvement",
        "diagnostic_lens": (
            "Focus on Value Stream Mapping (VSM), operator motion waste, transport distance, station cycle balancing, "
            "standard operating procedures (SOP), and process variation."
        ),
        "vocabulary": [
            "Value Stream Mapping (VSM)",
            "Station Line Balancing",
            "Standard Work Instructions (SWI)",
            "Muda / Operational Waste Elimination",
            "Poka-Yoke (Error Proofing)",
            "Material Flow Efficiency",
        ],
        "decision_criteria": (
            "Minimizing non-value-added motion, standardizing operator cycles across shifts, and systematically error-proofing handover points."
        ),
        "preferred_artifacts": (
            "Process Value Stream Diagram, Station Balance Comparison, Lean Implementation Roadmap."
        ),
    },
    ProfessionCategory.SOFTWARE_IT: {
        "title": "Software Engineering & Enterprise IT",
        "diagnostic_lens": (
            "Focus on API latency percentiles (p95/p99), database query efficiency (indexes, N+1 patterns), concurrency, "
            "error rates, message queue backlogs, authentication security, and bidirectional ERP/telemetry integration."
        ),
        "vocabulary": [
            "REST API & Webhooks",
            "Database Indexing & Query Plans",
            "Stateless Token Authentication",
            "Idempotency Keys",
            "System Availability SLAs",
            "Microservice Architecture",
            "Telemetry Ingestion Pipelines",
        ],
        "decision_criteria": (
            "High system reliability, strict data isolation, zero arbitrary code execution, clear API contracts, "
            "and scalable PostgreSQL performance."
        ),
        "preferred_artifacts": (
            "System Architecture Block Diagram, Data Pipeline Sequence, Integration Comparison Matrix."
        ),
    },
    ProfessionCategory.BUSINESS_LEADERSHIP: {
        "title": "Business Ownership & Executive Leadership",
        "diagnostic_lens": (
            "Focus on capital investment vs payback horizon (ROI), gross margin expansion, operational risk mitigation, "
            "workforce capacity scaling, customer SLA fulfillment, and measurable business outcomes."
        ),
        "vocabulary": [
            "Capital Payback Period (ROI)",
            "Operating Margin Expansion",
            "Risk Mitigation & Compliance",
            "Workforce Scalability",
            "Customer SLA Fulfillment",
            "Total Cost of Ownership (TCO)",
        ],
        "decision_criteria": (
            "Rapid time-to-value (sub-12 month payback), minimal operational disruption to active revenue lines, "
            "and demonstrable competitive advantage."
        ),
        "preferred_artifacts": (
            "Executive Business Case Summary, Before-and-After Operational Comparison, Investment Milestone Roadmap."
        ),
    },
    ProfessionCategory.FINANCE_ACCOUNTING: {
        "title": "Finance & Accounting Management",
        "diagnostic_lens": (
            "Focus on payroll and overtime reconciliation accuracy, statutory tax deductions (PF/ESI/TDS), "
            "cost center allocation, 3-way purchase order matching, and immutable audit trails."
        ),
        "vocabulary": [
            "Statutory Deductions & Filings",
            "Cost Center Attribution",
            "Overtime Calculation Audit Trails",
            "3-Way Matching (PO/GRN/Invoice)",
            "Payroll Run Reconciliation",
            "Operating Expense Variance",
        ],
        "decision_criteria": (
            "Eliminating manual calculation errors in payroll, zero statutory non-compliance penalties, "
            "and automated financial ledger synchronization."
        ),
        "preferred_artifacts": (
            "Financial Reconciliation Flow, Statutory Compliance Audit Breakdown, Cost-Benefit Comparison."
        ),
    },
    ProfessionCategory.HR_WORKFORCE: {
        "title": "Human Resources & Workforce Management",
        "diagnostic_lens": (
            "Focus on workforce timesheet collection friction, biometric punch reconciliation, multi-shift rotation rules, "
            "overtime rate calculations, and technical recruitment pipeline velocity."
        ),
        "vocabulary": [
            "Biometric Attendance Sync",
            "Shift Rotation Schedules",
            "Overtime Multipliers & Approvals",
            "Statutory Employee Benefits",
            "Skill Matrix & Candidate Parsing",
            "Employee Master Record Sync",
        ],
        "decision_criteria": (
            "Compressing payroll processing cycles from days to minutes, resolving shift attendance disputes, "
            "and automating technical skill evaluation."
        ),
        "preferred_artifacts": (
            "Timesheet-to-Payroll Automation Flow, Skill Scoring Matrix, Workforce Deployment Roadmap."
        ),
    },
    ProfessionCategory.SALES_MARKETING: {
        "title": "Commercial, Sales & Marketing",
        "diagnostic_lens": (
            "Focus on engineering quote turnaround time (TAT), tender takeoff accuracy, bill of materials (BOM) estimation, "
            "and customer proposal personalization."
        ),
        "vocabulary": [
            "Quote Turnaround Time (TAT)",
            "Tender Takeoff Accuracy",
            "Commercial Proposal Generation",
            "Bill of Quantities (BOQ)",
            "Customer Conversion Velocity",
        ],
        "decision_criteria": (
            "Accelerating tender submission speed, avoiding under-quoted estimation errors, and winning high-margin enterprise bids."
        ),
        "preferred_artifacts": (
            "Tender Takeoff Workflow, Proposal Automation Pipeline, Commercial Milestone Plan."
        ),
    },
    ProfessionCategory.SUPPLY_CHAIN_LOGISTICS: {
        "title": "Supply Chain, Logistics & Inventory",
        "diagnostic_lens": (
            "Focus on purchase requisition approval bottlenecks, supplier lead time variance, inventory buffer stockouts, "
            "warehouse pick-and-pack latency, and field technician dispatch routing."
        ),
        "vocabulary": [
            "Purchase Requisition Routing",
            "Safety Stock & Reorder Levels",
            "Multi-Tier Approval Limits",
            "Field Dispatch Ticketing",
            "Material Transfer Slips",
            "Supplier Lead Time Variance",
        ],
        "decision_criteria": (
            "Preventing plant assembly stoppages caused by missing parts, eliminating email-based approval delays, "
            "and maintaining real-time logistics tracking."
        ),
        "preferred_artifacts": (
            "Procurement Approval Hierarchy, Field Dispatch Flowchart, Inventory Buffer Matrix."
        ),
    },
    ProfessionCategory.CONSULTANT_RESEARCHER: {
        "title": "Industrial Consultant & Researcher",
        "diagnostic_lens": (
            "Focus on architectural trade-off comparisons, system maturity models, industry reference architectures, "
            "and empirical benchmark validation."
        ),
        "vocabulary": [
            "Architectural Trade-Off Analysis",
            "Operational Maturity Benchmarking",
            "Technology Readiness Levels (TRL)",
            "System Modularization",
            "Evidence-Based Evaluation",
        ],
        "decision_criteria": (
            "Rigorous technical justification, source-verified evidence, transparent boundary conditions, "
            "and clear alternative comparison."
        ),
        "preferred_artifacts": (
            "Comparative Architecture Matrix, Technology Maturity Evaluation, Phased Scoping Framework."
        ),
    },
    ProfessionCategory.GENERAL_PROFESSIONAL: {
        "title": "Enterprise & Industrial Professional",
        "diagnostic_lens": (
            "Adapt dynamically to the visitor's stated operational goals and industry sector with high consultative clarity, "
            "probing into root causes, process friction, and system integration needs."
        ),
        "vocabulary": [
            "Operational Efficiency",
            "Process Automation",
            "Data Reconciliation",
            "System Architecture",
            "Enterprise Scalability",
        ],
        "decision_criteria": (
            "Measurable process acceleration, elimination of repetitive manual work, and dependable software architecture."
        ),
        "preferred_artifacts": (
            "Solution Architecture Overview, Phased Implementation Roadmap, Trade-Off Comparison."
        ),
    },
}


class ProfessionContextService:
    """
    Categorizes visitor professions and produces tailored cognitive directives for LLM orchestration.
    """

    @classmethod
    def resolve_category(cls, profession: str) -> str:
        """
        Maps free-text profession/job title into an extensible professional category.
        Preserves original user job title for reporting while using category for cognitive tailoring.
        """
        clean = (profession or "").strip().lower()
        if not clean:
            return ProfessionCategory.GENERAL_PROFESSIONAL

        for category, pattern in ROLE_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                return category

        return ProfessionCategory.GENERAL_PROFESSIONAL

    @classmethod
    def get_category_directives(cls, category: str) -> Dict[str, Any]:
        """Retrieve cognitive directives for a category, falling back to general."""
        return CATEGORY_DIRECTIVES.get(category, CATEGORY_DIRECTIVES[ProfessionCategory.GENERAL_PROFESSIONAL])

    @classmethod
    def build_profession_prompt_directives(
        cls,
        profession: str,
        industry: str = "",
        department: str = "",
        responsibilities: str = "",
        company_name: str = "",
    ) -> str:
        """
        Constructs tailored cognitive instructions for the Senior Industrial Solution Architect LLM persona.
        """
        category = cls.resolve_category(profession)
        directives = cls.get_category_directives(category)

        category_title = directives["title"]
        diagnostic_lens = directives["diagnostic_lens"]
        vocab_list = "\n".join(f"  - {v}" for v in directives["vocabulary"])
        decision_criteria = directives["decision_criteria"]
        preferred_artifacts = directives["preferred_artifacts"]

        industry_context = industry.strip() if industry else "Industrial / Commercial Enterprise"
        dept_resp = responsibilities.strip() or department.strip() or "General Operational Oversight"
        company_ctx = company_name.strip() if company_name else "Independent / Enterprise Client"

        prompt_section = f"""### Profession-Aware Cognitive Directives:
You are consulting for a professional in the **{category_title}** domain.
- Visitor Job Title: {profession or "Operational Leader"}
- Mapped Role Category: {category_title}
- Industry / Sector: {industry_context}
- Company: {company_ctx}
- Operational Scope & Responsibilities: {dept_resp}

### Required Cognitive Demeanor & Reasoning Approach:
1. **Diagnostic Lens**:
   {diagnostic_lens}

2. **Native Vocabulary & Technical Depth**:
   Speak as an expert peer in their domain. Naturally utilize appropriate terminology such as:
{vocab_list}

3. **Core Decision Criteria & Priorities**:
   {decision_criteria}

4. **Targeted Artifacts & Outputs**:
   Where relevant to the query, structure your response to provide: {preferred_artifacts}

5. **Dynamic Follow-Up Inquiries**:
   Formulate your dynamic clarifying questions to probe the specific operational parameters, constraints, and metrics that matter most to a {profession or category_title} in {industry_context}.
"""
        return prompt_section
