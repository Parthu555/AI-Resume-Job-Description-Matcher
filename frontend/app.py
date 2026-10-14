import os
import time
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="AI Resume & Job Description Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Backend URL configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# Custom CSS for modern SaaS aesthetic
CUSTOM_CSS = """
<style>
    /* Global styles */
    .main {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header typography */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.25rem;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }

    /* Metric Card */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1e3a8a;
    }
    .metric-subtext {
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Skill tags */
    .skill-badge {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .skill-match {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }
    .skill-missing-req {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
    .skill-missing-pref {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .skill-additional {
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    /* Recommendation card */
    .rec-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
    }
    .rec-issue {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.35rem;
    }
    .rec-why {
        font-size: 0.88rem;
        color: #475569;
        margin-bottom: 0.5rem;
    }
    .rec-action {
        font-size: 0.88rem;
        color: #0f172a;
        background: #f1f5f9;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
    .rec-example {
        font-size: 0.85rem;
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        font-family: monospace;
        color: #334155;
    }

    /* Disclaimer box */
    .disclaimer-banner {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.82rem;
        color: #64748b;
        margin-top: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=3)
def check_backend_health():
    """Checks FastAPI backend availability and model status, returning (result_dict, error_message)."""
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=2.5)
        if resp.status_code == 200:
            return resp.json(), None
        return None, f"Server returned HTTP {resp.status_code}: {resp.text[:80]}"
    except requests.exceptions.ConnectionError:
        return None, f"Connection refused at `{BACKEND_URL}`. Ensure FastAPI backend is running."
    except requests.exceptions.Timeout:
        return None, f"Connection timed out at `{BACKEND_URL}`."
    except Exception as e:
        return None, str(e)


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("### 🎯 AI Resume Matcher")
    st.markdown("Evaluate and optimize your resume against real job requirements using explainable NLP.")
    
    # Backend Status Badge
    health, health_err = check_backend_health()
    if health and health.get("status") in ["healthy", "degraded", "initializing"]:
        if health.get("status") == "healthy":
            status_icon = "🟢"
            model_state = "Model Active"
        elif health.get("status") == "initializing":
            status_icon = "🔄"
            model_state = "Model Initializing"
        else:
            status_icon = "🟡"
            model_state = "TF-IDF Fallback Active"
        st.success(f"{status_icon} **Backend Connected** ({model_state})")
        if health.get("model_error"):
            st.caption(f"ℹ️ Model notice: {health.get('model_error')}")
    else:
        st.error(f"🔴 **Backend Offline**\n\n{health_err or 'Could not connect to ' + BACKEND_URL}\n\nEnsure FastAPI is running with `python run.py`.")

    st.markdown("---")
    st.markdown("#### 📋 How to Use")
    st.markdown(
        """
        1. **Upload Resume**: PDF or DOCX format (max 5 MB).
        2. **Paste Job Description**: Full job requirements text.
        3. **Analyze**: Click **Analyze Alignment**.
        4. **Review Results**: Inspect match score, skill gaps, and evidence.
        5. **Export Report**: Download full analysis as Markdown or JSON.
        """
    )

    st.markdown("---")
    st.markdown("#### 🔒 Privacy & Security")
    st.markdown(
        """
        - Uploaded files are processed in-memory only.
        - No resume content or PII is saved to disk or logged.
        - All analysis runs locally using open-source models.
        """
    )

    st.markdown("---")
    st.markdown(f"[📖 API Documentation (Swagger)]({BACKEND_URL}/docs)")


# ==========================================
# MAIN PAGE HEADER
# ==========================================
st.markdown('<div class="hero-title">AI Resume & Job Description Matcher</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Production-ready semantic alignment, skill taxonomy comparison, and actionable resume optimization.</div>',
    unsafe_allow_html=True
)

# Input Columns
col_resume, col_jd = st.columns([1, 1], gap="medium")

# Sample JD fallback text
SAMPLE_JD = """Job Title: Senior Python / AI Engineer
Location: Remote

Responsibilities:
- Build and maintain high-performance microservices and REST APIs using FastAPI and Python.
- Develop NLP pipelines and semantic search features using scikit-learn, PyTorch, and Sentence Transformers.
- Collaborate with data teams to process datasets using Pandas, NumPy, and PostgreSQL.
- Deploy scalable services to AWS using Docker, Kubernetes, and GitHub Actions.
- Ensure high code quality through unit testing with pytest and comprehensive code reviews.

Required Qualifications & Skills:
- 3+ years of professional software development experience in Python.
- Strong knowledge of backend web frameworks (FastAPI, Flask, or Django).
- Hands-on experience with Machine Learning or NLP (scikit-learn, PyTorch, or Hugging Face transformers).
- Proficiency in relational databases such as PostgreSQL or MySQL.
- Solid understanding of Docker, Git, and RESTful API principles.
- Strong fundamentals in data structures, algorithms, and automated testing.

Preferred Qualifications:
- Experience deploying ML workloads on AWS (EC2, S3, ECS, CloudWatch).
- Familiarity with Streamlit, React, or frontend dashboards.
- Knowledge of vector embeddings, semantic search, or LLM fine-tuning.
- Experience with Terraform and CI/CD automation."""

with col_resume:
    st.markdown("### 1. Upload Your Resume")
    uploaded_file = st.file_uploader(
        "Choose a file (.pdf or .docx)",
        type=["pdf", "docx"],
        help="Upload your latest resume. Supported formats: PDF, DOCX (Max 5 MB)."
    )
    if uploaded_file:
        file_size_kb = uploaded_file.size / 1024
        st.caption(f"📄 `{uploaded_file.name}` ({file_size_kb:.1f} KB)")

with col_jd:
    st.markdown("### 2. Job Description")
    
    # Optional Job Title
    target_job_title = st.text_input(
        "Target Job Title (Optional)",
        placeholder="e.g. Senior Python / AI Engineer",
        help="Helps contextualize role-specific recommendations."
    )
    
    # Pre-fill sample button
    col_label, col_sample_btn = st.columns([2, 1])
    with col_sample_btn:
        load_sample = st.button("📋 Load Sample JD", use_container_width=True)

    default_jd_value = SAMPLE_JD if load_sample else ""
    
    job_description = st.text_area(
        "Paste Job Description Here",
        value=default_jd_value,
        height=260,
        placeholder="Paste the full job description including responsibilities, required qualifications, and preferred skills..."
    )

st.markdown("")
analyze_clicked = st.button("🚀 Analyze Alignment", type="primary", use_container_width=True)

# ==========================================
# ANALYSIS EXECUTION & DASHBOARD
# ==========================================
if analyze_clicked:
    if not uploaded_file:
        st.error("⚠️ Please upload a resume in PDF or DOCX format before analyzing.")
    elif not job_description or len(job_description.strip()) < 20:
        st.error("⚠️ Please paste a valid job description (at least 20 characters).")
    else:
        with st.spinner("Analyzing semantic similarity, skills taxonomy, and experience evidence..."):
            try:
                # Prepare multipart request
                files = {
                    "resume": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                data = {
                    "job_description": job_description,
                }
                if target_job_title:
                    data["target_job_title"] = target_job_title

                response = requests.post(
                    f"{BACKEND_URL}/analyze",
                    files=files,
                    data=data,
                    timeout=90
                )

                if response.status_code == 200:
                    st.session_state["analysis_result"] = response.json()
                    st.success("✅ Analysis completed successfully!")
                else:
                    try:
                        err_detail = response.json().get("detail", response.text)
                    except Exception:
                        err_detail = response.text
                    st.error(f"❌ Analysis request failed ({response.status_code}): {err_detail}")
            except requests.exceptions.ConnectionError:
                st.error(
                    f"❌ Unable to connect to backend server at `{BACKEND_URL}`. "
                    "Please ensure FastAPI is started with `python run.py` or `uvicorn backend.main:app`."
                )
            except requests.exceptions.Timeout:
                st.error(f"❌ Request timed out (90s). The backend took too long to complete the analysis.")
            except Exception as e:
                st.error(f"❌ An error occurred during analysis: {str(e)}")


# Display analysis results if available
if "analysis_result" in st.session_state:
    res = st.session_state["analysis_result"]
    scores = res["scores"]
    exp = res["experience_analysis"]

    st.markdown("---")
    st.markdown("## 📊 Analysis Dashboard")

    # 1. Metric Cards Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    with m_col1:
        overall = scores["overall_score"]
        status_badge = "Excellent Match" if overall >= 80 else ("Strong Match" if overall >= 65 else ("Moderate Match" if overall >= 50 else "Needs Work"))
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Overall Alignment</div>
                <div class="metric-value">{overall:.1f}%</div>
                <div class="metric-subtext"><b>{status_badge}</b></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with m_col2:
        sem = scores["semantic_score"]
        sem_w = scores["weights_applied"].get("semantic_weight", 0.4) * 100
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Semantic Similarity</div>
                <div class="metric-value">{sem:.1f}%</div>
                <div class="metric-subtext">Weight: {sem_w:.0f}% (Vector Cosine)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with m_col3:
        req = scores["required_skill_score"]
        req_w = scores["weights_applied"].get("required_skill_weight", 0.4) * 100
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Required Skills</div>
                <div class="metric-value">{req:.1f}%</div>
                <div class="metric-subtext">Weight: {req_w:.0f}% (Must-haves)</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with m_col4:
        pref = scores.get("preferred_skill_score")
        if pref is not None:
            pref_w = scores["weights_applied"].get("preferred_skill_weight", 0.2) * 100
            pref_val_str = f"{pref:.1f}%"
            pref_sub_str = f"Weight: {pref_w:.0f}% (Nice-to-haves)"
        else:
            pref_val_str = "N/A"
            pref_sub_str = "Renormalized into core"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Preferred Skills</div>
                <div class="metric-value">{pref_val_str}</div>
                <div class="metric-subtext">{pref_sub_str}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f'<div class="disclaimer-banner"><b>Transparency Notice:</b> {scores["disclaimer"]}</div>',
        unsafe_allow_html=True
    )

    # 2. Score Visualizations
    st.markdown("### 📈 Alignment Breakdown")
    v_col1, v_col2 = st.columns([3, 2])
    with v_col1:
        # Chart data
        chart_data = {
            "Metric": ["Overall Alignment", "Semantic Similarity", "Required Skills"],
            "Score (%)": [scores["overall_score"], scores["semantic_score"], scores["required_skill_score"]]
        }
        if scores.get("preferred_skill_score") is not None:
            chart_data["Metric"].append("Preferred Skills")
            chart_data["Score (%)"].append(scores["preferred_skill_score"])

        import pandas as pd
        df_chart = pd.DataFrame(chart_data)
        st.bar_chart(df_chart.set_index("Metric"), color="#2563eb", use_container_width=True)

    with v_col2:
        st.markdown("#### Evidence Distribution")
        matching_count = len(res["matching_skills"])
        missing_count = len(res["missing_skills"])
        additional_count = len(res["additional_skills"])
        
        dist_df = pd.DataFrame({
            "Category": ["Matching Skills", "Missing Skills", "Additional Skills"],
            "Count": [matching_count, missing_count, additional_count]
        })
        st.dataframe(dist_df, hide_index=True, use_container_width=True)
        st.caption(f"Total resume words: {res['resume_word_count']} | JD words: {res['jd_word_count']}")

    # 3. Skills Breakdown Tabs
    st.markdown("### 🧩 Skills Taxonomy Analysis")
    tab_match, tab_missing, tab_add = st.tabs([
        f"✅ Matching Skills ({matching_count})",
        f"⚠️ Potentially Missing ({missing_count})",
        f"💡 Additional Skills ({additional_count})"
    ])

    with tab_match:
        if res["matching_skills"]:
            st.markdown("These skills were identified in the job description and substantiated in your resume:")
            for s in res["matching_skills"]:
                req_badge = "Required" if s["is_required"] else "Preferred"
                with st.expander(f"🟢 **{s['name']}** — *{s['category']}* ({req_badge})"):
                    st.write(f"**Evidence Snippet from Resume:**")
                    st.info(s.get("evidence_snippet") or "Mentioned in resume text.")
        else:
            st.info("No matching skills detected between the resume and job requirements.")

    with tab_missing:
        if res["missing_skills"]:
            st.markdown(
                "These skills are emphasized in the job description but have **insufficient evidence** in your resume. "
                "Only add a skill if you genuinely possess that capability."
            )
            for s in res["missing_skills"]:
                badge_type = "🔴 Required Prerequisite" if s["is_required"] else "🟡 Preferred / Nice-to-have"
                with st.expander(f"⚠️ **{s['name']}** — *{s['category']}* ({badge_type})"):
                    st.write("**Job Description Context:**")
                    st.warning(s.get("evidence_snippet") or "Found in job posting.")
                    st.write(
                        f"**Guidance:** If you have worked with {s['name']}, highlight a relevant project or coursework bullet demonstrating your experience."
                    )
        else:
            st.success("🎉 Excellent! All identified technical requirements from the job description are present in your resume.")

    with tab_add:
        if res["additional_skills"]:
            st.markdown(
                "These relevant technical competencies were found in your resume but are not explicitly demanded by the job posting. "
                "They demonstrate breadth but shouldn't overshadow core requirements."
            )
            badges_html = " ".join([
                f'<span class="skill-badge skill-additional">{s["name"]}</span>'
                for s in res["additional_skills"]
            ])
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.info("No additional distinct technical competencies detected.")

    # 4. Experience & Qualification Analysis
    st.markdown("### 🎓 Experience & Qualification Observations")
    e_col1, e_col2 = st.columns(2)
    with e_col1:
        st.markdown("**Resume Sections Detected:**")
        if exp["sections_detected"]:
            st.write(", ".join([f"`{sec}`" for sec in exp["sections_detected"]]))
        else:
            st.warning("No explicit standard section headings detected.")

        st.markdown("**Education Qualifications Identified:**")
        if exp["education_detected"]:
            for deg in exp["education_detected"]:
                st.write(f"• {deg}")
        else:
            st.write("• No standard degree keywords identified.")

    with e_col2:
        st.markdown("**Years of Experience Alignment:**")
        st.info(exp.get("experience_years_comparison") or "Not evaluated.")

    if exp["observations"]:
        st.markdown("**Key Observations:**")
        for obs in exp["observations"]:
            st.write(f"• {obs}")

    # 5. Actionable Recommendations Engine
    st.markdown("### 💡 Actionable Resume Recommendations")
    if res["recommendations"]:
        for idx, rec in enumerate(res["recommendations"], 1):
            with st.container():
                st.markdown(
                    f"""
                    <div class="rec-box">
                        <div class="rec-issue">📌 {idx}. {rec['issue']}</div>
                        <div class="rec-why"><b>Why this matters:</b> {rec['why_it_matters']}</div>
                        <div class="rec-action"><b>Recommended Action:</b> {rec['recommended_action']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if rec.get("example_rewrite"):
                    st.markdown("**Illustrative Example Rewrite (Truthful Template):**")
                    st.code(rec["example_rewrite"], language="markdown")
                    st.caption(f"⚠️ *{rec['user_verification_notice']}*")
    else:
        st.success("Your resume aligns closely with the job description. No major issues flagged.")

    # 6. Report Export
    st.markdown("### 📥 Download Analysis Report")
    
    # Import ReportGenerator locally on frontend or generate
    from backend.services.report_generator import ReportGenerator
    from backend.schemas.analysis import AnalysisResponse
    
    resp_obj = AnalysisResponse(**res)
    md_report = ReportGenerator.generate_markdown_report(resp_obj)
    json_report = ReportGenerator.generate_json_report(resp_obj)

    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.download_button(
            label="📄 Download Report (Markdown .md)",
            data=md_report,
            file_name="resume_match_report.md",
            mime="text/markdown",
            use_container_width=True
        )
    with d_col2:
        st.download_button(
            label="💾 Download Report (JSON .json)",
            data=json_report,
            file_name="resume_match_report.json",
            mime="application/json",
            use_container_width=True
        )
