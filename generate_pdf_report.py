import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(
                54,
                750,
                "EcoGen-AI — Layer 1 Ingestion & Monitoring Finalization Report",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        self.drawString(
            54,
            33,
            "Confidential & Internal — EcoGen-AI Architecture Verification",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 33, page_str)
        self.restoreState()


def build_pdf(filename="EcoGen_AI_Layer1_Finalization_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary = colors.HexColor("#0F766E")  # Teal / Emerald
    dark = colors.HexColor("#0F172A")  # Slate 900
    text_color = colors.HexColor("#334155")  # Slate 700

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=dark,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=16,
        textColor=primary,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=dark,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=text_color,
        spaceAfter=4,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=text_color,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
        textColor=dark,
    )

    badge_pass_style = ParagraphStyle(
        "BadgePass",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#065F46"),
    )

    story = []

    # Title block
    story.append(Paragraph("EcoGen-AI — Technical Milestone Report", title_style))
    story.append(
        Paragraph(
            "Layer 1 (Ingestion & Monitoring) Finalization, Metrics Expansion & Hardening",
            subtitle_style,
        )
    )

    # Metadata card table
    meta_data = [
        [
            Paragraph("<b>Target System:</b> EcoGen-AI Ingestion Layer", table_cell_style),
            Paragraph("<b>Database:</b> SQLite (<code>ecogen.db</code>)", table_cell_style),
        ],
        [
            Paragraph("<b>Stack:</b> FastAPI, SQLAlchemy, Pydantic, SQLite", table_cell_style),
            Paragraph("<b>Migration Status:</b> Completed & Non-Destructive", table_cell_style),
        ],
        [
            Paragraph("<b>Verification Result:</b> 6 / 6 Test Suites Passed", table_cell_style),
            Paragraph("<b>Deployment Readiness:</b> Layer 2 Ready", table_cell_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(
        Paragraph(
            "This document confirms the completion and end-to-end verification of <b>Layer 1 (Ingestion & Monitoring)</b> "
            "for the <b>EcoGen-AI</b> platform. EcoGen-AI operates across three integrated layers: "
            "(1) Ingestion & Monitoring, (2) Analytical Engine (Energy & Carbon computation), and (3) Strategy & Optimization. "
            "To enable Layer 2 to calculate accurate kilowatt-hours, embodied carbon, and marginal emissions, Layer 1 was hardened "
            "with missing operational metadata (datacenter PUE, GPU specifications, MoE active parameters, idle baseline power, and hardware lifespans). "
            "All modifications were executed non-destructively, preserving existing database rows and maintaining backward compatibility.",
            body_style,
        )
    )

    # 3-Layer System Overview
    story.append(Paragraph("2. System Architecture & Metric Flow", h1_style))
    arch_data = [
        [
            Paragraph("Layer", table_header_style),
            Paragraph("Role", table_header_style),
            Paragraph("Inputs from Layer 1", table_header_style),
        ],
        [
            Paragraph("<b>Layer 1<br/>Ingestion</b>", table_cell_bold),
            Paragraph("Intercepts LLM inference calls and hardware states; logs runtime, tokens, power draw, and datacenter parameters.", table_cell_style),
            Paragraph("Ingests: <code>InferenceEvent</code> & <code>HardwareSnapshot</code>", table_cell_style),
        ],
        [
            Paragraph("<b>Layer 2<br/>Analytics</b>", table_cell_bold),
            Paragraph("Computes dynamic energy (kWh), marginal carbon footprint (gCO2eq), incremental power over baseline, and embodied emissions amortization.", table_cell_style),
            Paragraph("Requires: <code>pue</code>, <code>num_gpus_used</code>, <code>gpu_model</code>, <code>active_param_count_b</code>, <code>idle_power_baseline_w</code>", table_cell_style),
        ],
        [
            Paragraph("<b>Layer 3<br/>Strategy</b>", table_cell_bold),
            Paragraph("Recommends model routing, batch size tuning, region carbon-intensity shifting, and MoE vs dense optimizations.", table_cell_style),
            Paragraph("Requires: <code>provider</code>, <code>batch_size</code>, <code>department</code>, <code>cost_usd</code>, <code>use_case</code>", table_cell_style),
        ],
    ]
    arch_table = Table(arch_data, colWidths=[80, 240, 184])
    arch_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("ALIGN", (0, 0), (-1, 0), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # Schema Additions
    story.append(Paragraph("3. Schema & Metric Additions", h1_style))
    story.append(Paragraph("3.1 InferenceEvent Table Extensions", h2_style))

    fields_data = [
        [
            Paragraph("Field Name", table_header_style),
            Paragraph("SQL Type", table_header_style),
            Paragraph("Default / Null", table_header_style),
            Paragraph("Purpose & Role in Layer 2 / 3", table_header_style),
        ],
        [
            Paragraph("<code>provider</code>", table_cell_bold),
            Paragraph("VARCHAR", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Origin provider (e.g., 'gemini', 'ollama') for cross-provider comparative analytics.", table_cell_style),
        ],
        [
            Paragraph("<code>pue</code>", table_cell_bold),
            Paragraph("FLOAT", table_cell_style),
            Paragraph("1.2", table_cell_style),
            Paragraph("Power Usage Effectiveness for cooling/datacenter multiplier in total energy calculation.", table_cell_style),
        ],
        [
            Paragraph("<code>gpu_model</code>", table_cell_bold),
            Paragraph("VARCHAR", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Accelerator hardware spec (e.g., 'H100', 'A100-SXM4-80GB', 'none') for TDP lookups.", table_cell_style),
        ],
        [
            Paragraph("<code>num_gpus_used</code>", table_cell_bold),
            Paragraph("INTEGER", table_cell_style),
            Paragraph("1", table_cell_style),
            Paragraph("Scale multiplier for multi-GPU distributed model parallelism.", table_cell_style),
        ],
        [
            Paragraph("<code>batch_size</code>", table_cell_bold),
            Paragraph("INTEGER", table_cell_style),
            Paragraph("1", table_cell_style),
            Paragraph("Batch throughput optimization tracking for Layer 3 recommendation engine.", table_cell_style),
        ],
        [
            Paragraph("<code>cost_usd</code>", table_cell_bold),
            Paragraph("FLOAT", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Financial cost per request for carbon-cost pareto efficiency frontier analysis.", table_cell_style),
        ],
        [
            Paragraph("<code>department</code>", table_cell_bold),
            Paragraph("VARCHAR", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Internal cost center / departmental ESG attribution reporting.", table_cell_style),
        ],
        [
            Paragraph("<code>use_case</code>", table_cell_bold),
            Paragraph("VARCHAR", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Workload categorization (e.g., 'code-refactoring', 'customer-chat', 'summarization').", table_cell_style),
        ],
        [
            Paragraph("<code>param_count_b</code>", table_cell_bold),
            Paragraph("FLOAT", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Total model parameter count (Billions). Basis for Tier 2 FLOP/token energy estimation.", table_cell_style),
        ],
        [
            Paragraph("<code>active_param_count_b</code>", table_cell_bold),
            Paragraph("FLOAT", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Active parameter count for MoE models (e.g. 12.9B for Mixtral 8x7B) vs total parameters.", table_cell_style),
        ],
    ]
    fields_table = Table(fields_data, colWidths=[90, 60, 70, 284])
    fields_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(fields_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.2 HardwareSnapshot Table Extensions", h2_style))
    hw_data = [
        [
            Paragraph("Field Name", table_header_style),
            Paragraph("SQL Type", table_header_style),
            Paragraph("Default / Null", table_header_style),
            Paragraph("Purpose & Role in Layer 2 / 3", table_header_style),
        ],
        [
            Paragraph("<code>idle_power_baseline_w</code>", table_cell_bold),
            Paragraph("FLOAT", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Resting baseline power. Enables Layer 2 to isolate incremental workload energy: P_incremental = P_active - P_idle.", table_cell_style),
        ],
        [
            Paragraph("<code>hardware_install_date</code>", table_cell_bold),
            Paragraph("DATETIME", table_cell_style),
            Paragraph("NULL", table_cell_style),
            Paragraph("Deployment timestamp for hardware manufacturing embodied carbon amortization over expected lifespan (GHG Scope 3).", table_cell_style),
        ],
    ]
    hw_table = Table(hw_data, colWidths=[110, 60, 70, 264])
    hw_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(hw_table)
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # Implementation & Hardening Details
    story.append(Paragraph("4. Hardening & Collector Upgrades", h1_style))
    story.append(
        Paragraph(
            "<b>4.1 LLM Metadata Collector (<code>collectors/gen_ai_data.py</code> & <code>genai_metadata.py</code>)</b><br/>"
            "• <b>Static Parameter Mapping (<code>MODEL_PARAM_MAP</code>):</b> Best-effort static table pre-populates parameter counts "
            "for Gemma (270m to 27b), LLaMA (1b to 405b), Mistral/Mixtral (7b, 8x7b, 8x22b), Gemini (1.5/2.0/2.5/3.5 Flash & Pro), Qwen 2.5, and Phi.<br/>"
            "• <b>MoE Active Parameter Resolution (<code>MOE_ACTIVE_PARAM_MAP</code>):</b> Differentiates between total and active routed parameters "
            "(e.g., Mixtral 8x7B has 46.7B total but only 12.9B active per token). Dense models automatically default active = total.<br/>"
            "• <b>Provider Persistence:</b> <code>provider</code> parameter in <code>@track_inference</code> is now posted into <code>/ingest/event</code> and stored in SQLite.<br/>"
            "• <b>Token Extraction Resilience:</b> Extended <code>_extract_tokens</code> to handle both object attributes (<code>usage_metadata</code>) and dictionary responses.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "<b>4.2 Hardware Power Collector (<code>collectors/hardware_data.py</code> & <code>hardware_power.py</code>)</b><br/>"
            "• <b>Baseline Power Sampling:</b> Added <code>get_idle_power_baseline(samples=4, interval_sec=0.5)</code> to measure resting load.<br/>"
            "• <b>API Integration:</b> Exposed optional automatic sampling via <code>POST /ingest/hardware?sample_idle=true</code>.<br/>"
            "• <b>Helper Function:</b> Added <code>post_hardware_snapshot(...)</code> to sample and transmit hardware metrics in a single call.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "<b>4.3 Schema Drift Correction</b><br/>"
            "During testing, we identified that <code>power_draw_watts</code> and <code>carbon_intensity</code> were present in the database model and output schema, "
            "but omitted from the input <code>EventCreate</code> schema. This caused incoming power draw values sent to <code>/ingest/event</code> to be ignored. "
            "We added both fields to <code>EventCreate</code> as optional attributes, allowing explicit power values and carbon intensity readings to persist.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "<b>4.4 Safe Database Migration (<code>database/migrate.py</code>)</b><br/>"
            "• Implemented non-destructive <code>run_migrations('ecogen.db')</code>.<br/>"
            "• Queries <code>PRAGMA table_info</code> and applies individual <code>ALTER TABLE ADD COLUMN</code> statements only when missing.<br/>"
            "• Preserves 100% of existing rows without table dropping or recreation.<br/>"
            "• Triggered automatically on FastAPI application startup (<code>@app.on_event('startup')</code>).",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    # Verification & Test Matrix
    story.append(Paragraph("5. Verification & Test Matrix", h1_style))

    test_data = [
        [
            Paragraph("Check", table_header_style),
            Paragraph("Test Description", table_header_style),
            Paragraph("Expected Behavior", table_header_style),
            Paragraph("Result", table_header_style),
        ],
        [
            Paragraph("<b>Check 1</b>", table_cell_bold),
            Paragraph("SQLite schema inspection (<code>sqlite3 ecogen.db '.schema'</code>)", table_cell_style),
            Paragraph("All 10 new columns in <code>inference_events</code>, 2 in <code>hardware_snapshots</code>.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
        [
            Paragraph("<b>Check 2</b>", table_cell_bold),
            Paragraph("Full-payload ingestion via <code>POST /ingest/event</code>", table_cell_style),
            Paragraph("HTTP 200; all 10 new fields (provider, pue, cost, MoE active params) populated.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
        [
            Paragraph("<b>Check 3</b>", table_cell_bold),
            Paragraph("Minimal required fields only via <code>POST /ingest/event</code>", table_cell_style),
            Paragraph("HTTP 200; defaults applied (pue=1.2, gpus=1, batch=1); nullable fields return null.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
        [
            Paragraph("<b>Check 4</b>", table_cell_bold),
            Paragraph("Query events (<code>GET /events?limit=5</code> and <code>GET /events/1</code>)", table_cell_style),
            Paragraph("Pre-migration rows deserialize cleanly with nulls; new rows show populated fields.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
        [
            Paragraph("<b>Check 5</b>", table_cell_bold),
            Paragraph("Unmodified decorator test (Gemini & Ollama <code>@track_inference</code>)", table_cell_style),
            Paragraph("Function returns original response; <code>last_event</code> captures provider and tokens; auto-posted to DB.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
        [
            Paragraph("<b>Check 6</b>", table_cell_bold),
            Paragraph("Hardware snapshot ingestion (<code>POST /ingest/hardware</code>)", table_cell_style),
            Paragraph("Explicit and <code>?sample_idle=true</code> baseline captures succeed and persist.", table_cell_style),
            Paragraph("<b>PASSED</b><br/>Verified", badge_pass_style),
        ],
    ]
    test_table = Table(test_data, colWidths=[55, 175, 194, 80])
    test_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), primary),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(test_table)
    story.append(Spacer(1, 6))

    # Readiness & Next Steps
    story.append(Paragraph("6. Hand-off to Layer 2 & Layer 3", h1_style))
    story.append(
        Paragraph(
            "With Layer 1 finalized and hardened, the data contract between layers is locked:<br/>"
            "• <b>Layer 2 Readiness:</b> Can compute dynamic inference energy: <i>E_inf = (P_active - P_idle) × runtime × PUE</i>. "
            "Can amortize embodied impact using <code>hardware_install_date</code>, and apply Tier 2 FLOPs fallbacks using <code>active_param_count_b</code>.<br/>"
            "• <b>Layer 3 Readiness:</b> Can segment carbon intensity and operational cost by <code>provider</code>, <code>department</code>, "
            "and <code>use_case</code> to recommend greener model architectures and batching schedules.<br/>"
            "• <b>Repository Status:</b> Ready for staging/production commit with zero schema breaking changes.",
            body_style,
        )
    )

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "EcoGen_AI_Layer1_Finalization_Report.pdf"
    build_pdf(out_file)
