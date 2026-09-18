import streamlit as st
import json
import os

from auditor import audit_website
from llm_analyzer import analyze_website
from report_generator import (
    generate_report,
    save_report
)


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Website Quality Auditor",
    page_icon="🌐",
    layout="wide"
)


# ==========================================
# TITLE
# ==========================================

st.title(
    "🌐 AI Website Quality Auditor"
)

st.write(
    "Analyze food, restaurant, cafe, and "
    "food-business websites using automated "
    "website auditing and AI-powered analysis."
)

st.divider()


# ==========================================
# WEBSITE URL INPUT
# ==========================================

st.subheader(
    "Enter Website URL"
)

website_url = st.text_input(
    "Food / Restaurant Website",
    placeholder="https://www.example.com/",
    help="Enter the website you want to audit."
)


# ==========================================
# RUN AUDIT BUTTON
# ==========================================

run_audit = st.button(
    "🔍 Run Website Audit",
    type="primary"
)


# ==========================================
# RUN COMPLETE AUDIT
# ==========================================

if run_audit:

    if not website_url.strip():

        st.warning(
            "Please enter a website URL."
        )

        st.stop()

    # --------------------------------------
    # STEP 1 — WEBSITE AUDIT
    # --------------------------------------

    with st.spinner(
        "Auditing website..."
    ):

        audit_data = audit_website(
            website_url
        )

    # Save website audit
    with open(
        "website.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            audit_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------
    # CHECK WEBSITE ACCESS
    # --------------------------------------

    if not audit_data.get(
        "success",
        False
    ):

        st.error(
            "The website could not be successfully "
            "accessed."
        )

        st.write(
            "Error:",
            audit_data.get(
                "error",
                "Unknown error"
            )
        )

        st.stop()

    # --------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------

    st.success(
        "Website audit completed successfully."
    )

    # --------------------------------------
    # OVERALL SCORE
    # --------------------------------------

    st.subheader(
        "Overall Quality Score"
    )

    overall_score = audit_data.get(
        "overall_score",
        0
    )

    st.metric(
        "Score",
        f"{overall_score} / 100"
    )

    # --------------------------------------
    # CATEGORY SCORES
    # --------------------------------------

    st.subheader(
        "Category Scores"
    )

    scores = audit_data.get(
        "category_scores",
        {}
    )

    if scores:

        columns = st.columns(
            len(scores)
        )

        for column, (
            category,
            score
        ) in zip(
            columns,
            scores.items()
        ):

            with column:

                st.metric(
                    category.replace(
                        "_",
                        " "
                    ).title(),
                    score
                )

    st.divider()

    # --------------------------------------
    # WEBSITE INFORMATION
    # --------------------------------------

    st.subheader(
        "Website Information"
    )

    info_col1, info_col2, info_col3 = (
        st.columns(3)
    )

    with info_col1:

        st.write(
            "**Website**"
        )

        st.write(
            audit_data.get(
                "url",
                "N/A"
            )
        )

    with info_col2:

        st.write(
            "**Status Code**"
        )

        st.write(
            audit_data.get(
                "status_code",
                "N/A"
            )
        )

    with info_col3:

        st.write(
            "**Response Time**"
        )

        st.write(
            f"{audit_data.get(
                'response_time_seconds',
                'N/A'
            )} seconds"
        )

    # --------------------------------------
    # SEO
    # --------------------------------------

    st.subheader(
        "SEO & Structure"
    )

    seo_col1, seo_col2 = (
        st.columns(2)
    )

    with seo_col1:

        st.write(
            "**Meta Title**"
        )

        st.write(
            audit_data.get(
                "meta_title",
                "Not detected"
            )
        )

        st.write(
            "**Meta Description**"
        )

        st.write(
            audit_data.get(
                "meta_description",
                "Not detected"
            )
        )

    with seo_col2:

        st.metric(
            "H1 Count",
            audit_data.get(
                "h1_count",
                0
            )
        )

        st.metric(
            "Internal Links",
            audit_data.get(
                "internal_link_count",
                0
            )
        )

        st.metric(
            "Pages Checked",
            audit_data.get(
                "page_count_found",
                0
            )
        )

    # --------------------------------------
    # ACCESSIBILITY
    # --------------------------------------

    st.subheader(
        "Accessibility"

    )

    acc_col1, acc_col2, acc_col3 = (
        st.columns(3)
    )

    with acc_col1:

        st.metric(
            "Total Images",
            audit_data.get(
                "total_images",
                0
            )
        )

    with acc_col2:

        st.metric(
            "Images With Alt",
            audit_data.get(
                "images_with_alt",
                0
            )
        )

    with acc_col3:

        st.metric(
            "Alt Coverage",
            f"{audit_data.get(
                'alt_text_coverage_percent',
                'N/A'
            )}%"
        )

    # --------------------------------------
    # FOOD BUSINESS FEATURES
    # --------------------------------------

    st.subheader(
        "Food Business Features"
    )

    feature_col1, feature_col2, feature_col3 = (
        st.columns(3)
    )

    with feature_col1:

        st.metric(
            "CTA Count",
            audit_data.get(
                "cta_count",
                0
            )
        )

    with feature_col2:

        st.metric(
            "Social Links",
            audit_data.get(
                "social_link_count",
                0
            )
        )

    with feature_col3:

        contact_form = audit_data.get(
            "has_contact_form",
            False
        )

        st.metric(
            "Contact Form",
            "Detected"
            if contact_form
            else "Not Detected"
        )

    # --------------------------------------
    # CTAs
    # --------------------------------------

    st.subheader(
        "Detected CTAs"
    )

    ctas = audit_data.get(
        "ctas",
        []
    )

    if ctas:

        for cta in ctas:

            st.write(
                f"• {cta}"
            )

    else:

        st.write(
            "No CTAs detected."
        )

    # --------------------------------------
    # ISSUES
    # --------------------------------------

    st.subheader(
        "Detected Issues"
    )

    issues = audit_data.get(
        "issues",
        []
    )

    if issues:

        for issue in issues:

            st.warning(
                issue
            )

    else:

        st.success(
            "No measurable issues detected."
        )

    # --------------------------------------
    # RULE-BASED RECOMMENDATIONS
    # --------------------------------------

    st.subheader(
        "Recommendations"
    )

    recommendations = audit_data.get(
        "recommendations",
        []
    )

    if recommendations:

        for recommendation in recommendations:

            st.info(
                recommendation
            )

    else:

        st.write(
            "No recommendations."
        )

    st.divider()

    # ======================================
    # AI ANALYSIS
    # ======================================

    st.subheader(
        "🤖 AI-Powered Analysis"
    )

    with st.spinner(
        "Generating AI analysis..."
    ):

        ai_analysis = analyze_website(
            audit_data
        )

    # Save AI analysis
    with open(
        "ai_analysis.txt",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            ai_analysis
        )

    st.markdown(
        ai_analysis
    )

    st.divider()

    # ======================================
    # FINAL REPORT
    # ======================================

    st.subheader(
        "📄 Final Report"
    )

    final_report = generate_report(
        audit_data,
        ai_analysis
    )

    save_report(
        final_report,
        "final_report.txt"
    )

    st.success(
        "Final report generated successfully."
    )

    # --------------------------------------
    # DOWNLOAD REPORT
    # --------------------------------------

    st.download_button(
        label="📥 Download Audit Report",
        data=final_report,
        file_name="website_quality_report.txt",
        mime="text/plain"
    )

    # --------------------------------------
    # RAW AUDIT DATA
    # --------------------------------------

    with st.expander(
        "View Raw Audit Data"
    ):

        st.json(
            audit_data
        )

