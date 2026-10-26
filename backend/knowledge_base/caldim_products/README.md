# CALDIM Product Knowledge Base & Catalogue

This directory contains the authoritative product reference catalogue, specification documents, and media assets powering the CALDIM IntelliSolve AI platform.

---

## 1. Directory Structure

```
backend/knowledge_base/caldim_products/
├── products.json           # Master product catalogue (10 candidate/showcase products)
├── README.md               # This operating guide
├── documents/              # Approved specification documents & manuals
│   ├── README.md
│   └── caltims_spec.md     # CalTIMS reference specification document [DRAFT]
└── media/                  # Screenshots, diagrams, and video walkthroughs
    └── README.md
```

---

## 2. Master Catalogue Format (`products.json`)

The catalogue uses a structured JSON format with strict governance fields:

| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | string | Official product name |
| `slug` | string | Unique URL-safe identifier (e.g. `caltims`, `calbuy`) |
| `category` | string | Product domain / category classification |
| `tagline` | string | Short marketing summary (1 sentence) |
| `overview` | string | Comprehensive detailed technical description |
| `readiness_status` | enum | `production_ready`, `preview_ready`, `in_development`, `concept` |
| `publication_status`| enum | `published` (visible to visitors) or `draft` (internal review only) |
| `is_verified` | boolean | `true` only when verified against official CALDIM documentation |
| `verifier_name` | string/null | Name / designation of verifier |
| `verification_date` | string/null | ISO date of latest verification |
| `official_product_page`| url/null | Official CALDIM website URL |
| `documentation_url`| url/null | Approved documentation URL |
| `demo_url` | url/null | Working interactive demo URL |
| `customization_scope`| string | Scope for customer-specific tailoring |
| `integrations` | array | List of supported enterprise connectors/ERPs |
| `deployment_options`| array | `Cloud SaaS`, `Dedicated Cloud VPC`, `On-Premises Air-Gapped` |
| `pricing_status` | string | Pricing policy description |
| `pricing_evidence` | string/null | Verified pricing references or null if unverified |
| `case_studies` | array | Verified case studies (empty array if none) |
| `customer_references`| array | Verified references (empty array if confidential/unverified) |
| `capabilities` | array | Verified capabilities with titles, descriptions, and metrics |
| `limitations` | array | Known operational boundaries and alternatives |
| `business_problems`| array | Mappings to industry verticals, problems, and buyer roles |
| `media` | array | Screenshots, architecture diagrams, and video links |
| `notes` | string | Audit notes or illustrative sample warnings |

---

## 3. Strict Verification & AI Retrieval Governance

To ensure 100% truthfulness and prevent AI hallucination:

1. **Authoritative AI Consultation**:
   - The AI consultation engine and search service strictly filter by:
     `is_verified = True` AND `publication_status = "published"` AND `is_active = True`.
   - Any product marked `is_verified = False` or `publication_status = "draft"` is **never cited** as an authoritative solution in customer consultation or automated proposal generation.

2. **No Invented Capabilities**:
   - If a capability or metric is not backed by documented evidence, set `is_verified: false` and clearly prefix the title with `[ILLUSTRATIVE]`.
   - Unknown values for pricing, case studies, or demo URLs must be `null` or `[]`.

---

## 4. How to Replace a Sample Product with Real Information

Follow these steps to convert an unverified sample record into an authoritative production product:

### Step 1: Open `products.json`
Locate the product by its `slug` (for example, `calbuy`).

### Step 2: Replace Sample Text with Real Specifications
Update the fields with verified content:
- Set `is_verified: true`
- Set `publication_status: "published"`
- Set `verifier_name: "Your Name / Department"`
- Set `verification_date: "YYYY-MM-DD"`
- Set `official_product_page: "https://caldimproducts.com/products/calbuy"`
- Replace illustrative capabilities with real, verified capabilities, setting `is_verified: true` on each capability.
- Document real architectural limitations and alternatives in `limitations`.
- Add approved industry pain-point mappings in `business_problems`.

### Step 3: Add Documentation (Optional but Recommended)
Place the full markdown specification in `backend/knowledge_base/caldim_products/documents/calbuy_spec.md`.

### Step 4: Validate with Dry-Run
Run the validation command to verify schema integrity without writing to the database:
```bash
python manage.py import_caldim_catalogue --dry-run
```

### Step 5: Execute Import
Once the dry-run passes, import the updated catalogue:
```bash
python manage.py import_caldim_catalogue
```
The command is **idempotent**: it will match by `slug` and update existing records instead of creating duplicates.

---

## 5. Concrete Before & After Example

### Before (Sample / Draft Record)
```json
{
  "name": "CALBUY",
  "slug": "calbuy",
  "category": "Procurement & Vendor Lifecycle Pipeline",
  "tagline": "Streamlined purchase requisitions, RFQs, vendor comparisons, and PO issuance",
  "overview": "Corporate purchasing workflow system supporting requisitions, quotation requests, supplier comparison, and purchase order tracking.",
  "readiness_status": "preview_ready",
  "publication_status": "draft",
  "is_verified": false,
  "verifier_name": null,
  "verification_date": null,
  "official_product_page": "https://caldimproducts.com/products",
  "documentation_url": null,
  "demo_url": null,
  "pricing_status": "Unverified / Contact Sales",
  "pricing_evidence": null,
  "capabilities": [
    {
      "title": "Requisition to Purchase Order Workflow [ILLUSTRATIVE]",
      "description": "Multi-tier approval routing based on order value.",
      "metric_highlight": "Preview feature observed in showcase",
      "feature_order": 1,
      "is_verified": false
    }
  ],
  "limitations": [],
  "notes": "ILLUSTRATIVE SAMPLE RECORD: Sourced from CALDIM-DAS showcase."
}
```

### After (Verified Production Record)
```json
{
  "name": "CALBUY",
  "slug": "calbuy",
  "category": "Procurement & Vendor Lifecycle Pipeline",
  "tagline": "Automated Enterprise Requisition, RFQ Matching, and PO Issuance",
  "overview": "CALBUY is CALDIM's enterprise procurement platform that automates multi-department purchase requisitions, comparative RFQ analysis across approved vendors, and three-way invoice matching.",
  "readiness_status": "production_ready",
  "publication_status": "published",
  "is_verified": true,
  "verifier_name": "Chief Procurement Systems Architect",
  "verification_date": "2026-11-01",
  "official_product_page": "https://caldimproducts.com/products/calbuy",
  "documentation_url": "https://docs.caldim.com/calbuy",
  "demo_url": "https://caldimproducts.com/products/calbuy#demo",
  "pricing_status": "Enterprise Tiered",
  "pricing_evidence": "Annual subscription starting at $12,000/year for up to 50 purchasing agents; verified against Q4 2026 rate card.",
  "capabilities": [
    {
      "title": "Automated Three-Way Invoice Matching",
      "description": "Cross-verifies purchase orders, warehouse goods receipt notes (GRN), and vendor invoices before payment release.",
      "metric_highlight": "99.8% match accuracy across 50,000 invoices",
      "feature_order": 1,
      "is_verified": true
    }
  ],
  "limitations": [
    {
      "title": "SAP S/4HANA Bidirectional Connector",
      "description": "Direct bidirectional ledger sync requires the CALDIM SAP Gateway connector module.",
      "mitigation_or_alternative": "Standard automated SFTP CSV batch exchange is included out of the box."
    }
  ],
  "notes": "Verified against production v3.2 release notes."
}
```
