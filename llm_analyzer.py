import json
import os
import time

from dotenv import load_dotenv
from google import genai


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

api_key = os.getenv(
    "GEMINI_API_KEY"
)

if not api_key:

    raise ValueError(
        "GEMINI_API_KEY was not found "
        "in the .env file."
    )


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(
    api_key=api_key
)


# ==========================================
# LOAD AUDIT DATA
# ==========================================

def load_audit_data(
    filename="website.json"
):

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ==========================================
# FALLBACK ANALYSIS
# ==========================================

def create_fallback_analysis(audit_data):
    """
    Generate a fact-based analysis when Gemini is unavailable.
    Uses only information contained in website.json.
    """

    scores = audit_data.get("scores", {})
    seo = audit_data.get("seo", {})
    structure = audit_data.get("structure", {})
    images = audit_data.get("images", {})
    ctas = audit_data.get("ctas", {})
    social = audit_data.get("social_media", {})
    contact = audit_data.get("contact", {})

    overall_score = scores.get("total", "N/A")
    response_time = audit_data.get("response_time", "N/A")

    pages_found = structure.get("pages_found", "N/A")
    internal_links = structure.get("internal_links", "N/A")

    alt_coverage = images.get("alt_coverage", "N/A")
    total_images = images.get("total_images", "N/A")
    images_with_alt = images.get("images_with_alt", "N/A")

    cta_count = ctas.get("count", 0)
    cta_detected = ctas.get("detected", [])

    social_count = social.get("count", 0)

    contact_form = contact.get("contact_form", False)

    meta_title = bool(seo.get("meta_title"))
    meta_description = bool(seo.get("meta_description"))
    h1_count = seo.get("h1_count", "N/A")

    issues = audit_data.get("issues", [])
    recommendations = audit_data.get("recommendations", [])

    analysis = []

    analysis.append("### 1. Executive Summary")
    analysis.append("")
    analysis.append(
        f"The website received an automated quality score of "
        f"{overall_score}/100 based on the rule-based audit."
    )
    analysis.append(
        f"The measured response time was {response_time} seconds."
    )
    analysis.append(
        f"The auditor checked {pages_found} sampled pages "
        f"and detected {internal_links} internal links."
    )

    analysis.append("")
    analysis.append("### 2. Verified Strengths")
    analysis.append("")

    if alt_coverage != "N/A":
        analysis.append(
            f"- Image alt-text coverage: {alt_coverage}%."
        )

    analysis.append(
        f"- Detected CTAs: {cta_count}."
    )

    analysis.append(
        f"- Detected social-media links: {social_count}."
    )

    if meta_title:
        analysis.append("- A meta title was detected.")

    if meta_description:
        analysis.append("- A meta description was detected.")

    if not alt_coverage and not cta_count and not social_count:
        analysis.append(
            "- No specific strengths were detected by the rule-based checks."
        )

    analysis.append("")
    analysis.append("### 3. Verified Issues")
    analysis.append("")

    if issues:
        for issue in issues:
            analysis.append(f"- {issue}")
    else:
        analysis.append("- No issues were detected.")

    analysis.append("")
    analysis.append("### 4. SEO Analysis")
    analysis.append("")

    analysis.append(
        f"- Meta title detected: {meta_title}."
    )
    analysis.append(
        f"- Meta description detected: {meta_description}."
    )
    analysis.append(
        f"- H1 count detected: {h1_count}."
    )
    analysis.append(
        "These measurements are based on the fetched rendered HTML."
    )

    analysis.append("")
    analysis.append("### 5. Performance Analysis")
    analysis.append("")

    analysis.append(
        f"- Measured response time: {response_time} seconds."
    )
    analysis.append(
        "This measurement represents the time taken by the automated "
        "browser audit to load and process the website."
    )

    analysis.append("")
    analysis.append("### 6. Accessibility Analysis")
    analysis.append("")

    analysis.append(
        f"- Total detected images: {total_images}."
    )
    analysis.append(
        f"- Images with alt text: {images_with_alt}."
    )
    analysis.append(
        f"- Alt-text coverage: {alt_coverage}%."
    )
    analysis.append(
        "These measurements are based on image elements detected "
        "in the fetched rendered HTML."
    )

    analysis.append("")
    analysis.append("### 7. User Experience Analysis")
    analysis.append("")

    analysis.append(
        f"- Internal links detected: {internal_links}."
    )
    analysis.append(
        f"- Sampled pages checked: {pages_found}."
    )
    analysis.append(
        f"- Contact form detected: {contact_form}."
    )
    analysis.append(
        "These results describe elements detected by the automated audit."
    )

    analysis.append("")
    analysis.append("### 8. Food Business / Conversion Analysis")
    analysis.append("")

    analysis.append(
        f"- Detected CTA count: {cta_count}."
    )
    analysis.append(
        f"- Detected social links: {social_count}."
    )

    if cta_detected:
        analysis.append("- Detected CTA examples:")

        for cta in cta_detected:
            analysis.append(f"  - {cta}")
    else:
        analysis.append("- No CTA examples were detected.")

    analysis.append("")
    analysis.append("### 9. Recommended Improvements")
    analysis.append("")

    if recommendations:
        for recommendation in recommendations:
            analysis.append(f"- {recommendation}")
    else:
        analysis.append("- No additional recommendations were generated.")

    analysis.append("")
    analysis.append("### 10. Priority Actions")
    analysis.append("")

    if issues:
        analysis.append("HIGH")

        for issue in issues:
            analysis.append(f"- Review: {issue}")

        analysis.append("")
        analysis.append("MEDIUM")

        for recommendation in recommendations:
            analysis.append(f"- {recommendation}")
    else:
        analysis.append("HIGH")
        analysis.append("- No high-priority issues detected.")

        analysis.append("")
        analysis.append("MEDIUM")
        analysis.append("- Continue monitoring website quality metrics.")

    analysis.append("")
    analysis.append("LOW")
    analysis.append(
        "- Continue monitoring website quality metrics during future audits."
    )

    analysis.append("")
    analysis.append(
        "NOTE: Gemini AI analysis was temporarily unavailable. "
        "This report section was generated from the rule-based audit data instead."
    )

    return "\n".join(analysis)


# ==========================================
# GEMINI ANALYSIS
# ==========================================

def analyze_website(
    audit_data
):
    """
    Try Gemini first.

    If Gemini is temporarily unavailable,
    use the fact-based fallback analysis.
    """

    prompt = f"""
You are an AI website quality analyst
specializing in food and restaurant websites.

Analyze ONLY the website audit data provided below.

IMPORTANT ACCURACY RULES:

1. Use ONLY facts explicitly present in the audit data.
2. Do NOT browse the website.
3. Do NOT use outside knowledge.
4. Do NOT invent URLs, pages, features, headings,
   links, forms, or website functionality.
5. Do NOT mention specific URLs unless they appear
   explicitly in the audit data.
6. Do NOT claim a feature exists unless it is
   explicitly included in the audit data.
7. Do NOT claim duplicate headings unless duplicate
   headings are explicitly identified in the data.
8. Treat "not detected" as "not detected in the
   fetched HTML".
9. Separate measurable facts from recommendations.
10. Keep the analysis professional and concise.

Provide:

1. Executive Summary
2. Verified Strengths
3. Verified Issues
4. SEO Analysis
5. Performance Analysis
6. Accessibility Analysis
7. User Experience Analysis
8. Food Business / Conversion Analysis
9. Recommended Improvements
10. Priority Actions

For Priority Actions use:

HIGH
MEDIUM
LOW

Website audit data:

{json.dumps(
    audit_data,
    indent=4,
    ensure_ascii=False
)}
"""

    models = [
        "gemini-3.8-flash",
        "gemini-3.7-flash"
    ]

    for model_name in models:

        print(
            f"\nTrying Gemini model: "
            f"{model_name}"
        )

        for attempt in range(1, 3):

            try:

                print(
                    f"Attempt {attempt}/2..."
                )

                response = (
                    client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                )

                print(
                    "\nGemini analysis completed."
                )

                return response.text

            except Exception as e:
             print("\nGemini AI is currently unavailable.")
             print("Using rule-based fallback analysis.")
             print("Reason:", e)

             return create_fallback_analysis(audit_data)

    # ======================================
    # FALLBACK
    # ======================================

    print(
        "\nGemini models are currently "
        "unavailable."
    )

    print(
        "Using rule-based fallback analysis..."
    )

    return create_fallback_analysis(
        audit_data
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    audit_data = load_audit_data(
        "website.json"
    )

    print(
        "\n=============================="
    )

    print(
        "AI WEBSITE ANALYSIS"
    )

    print(
        "=============================="
    )

    if not audit_data.get(
        "success",
        False
    ):

        print(
            "\nWebsite could not be successfully "
            "audited."
        )

        print(
            "Error:",
            audit_data.get(
                "error"
            )
        )

    else:

        analysis = analyze_website(
            audit_data
        )

        print(
            "\n"
        )

        print(
            analysis
        )

        with open(
            "ai_analysis.txt",
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                analysis
            )

        print(
            "\nAI analysis saved to "
            "ai_analysis.txt"
        )

