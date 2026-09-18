import json


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)


def load_text(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def get_first(data, keys, default="N/A"):
    """Return the first existing value from a list of possible keys."""
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            return data[key]

    return default


def generate_report(audit_data, ai_analysis):

    # Main website information
    website = audit_data.get("website", "N/A")
    status_code = audit_data.get("status_code", "N/A")
    response_time = audit_data.get("response_time", "N/A")

    scores = audit_data.get("scores", {})
    seo = audit_data.get("seo", {})
    structure = audit_data.get("structure", {})
    images = audit_data.get("images", {})
    ctas = audit_data.get("ctas", {})
    social = audit_data.get("social_media", {})
    contact = audit_data.get("contact", {})

    issues = audit_data.get("issues", [])
    recommendations = audit_data.get("recommendations", [])

    # Handle possible field names
    overall_score = get_first(
        scores,
        ["overall", "overall_score", "total", "score"],
        audit_data.get("overall_score", "N/A")
    )

    total_images = get_first(
        images,
        ["total", "total_images", "count"],
        audit_data.get("total_images", "N/A")
    )

    images_with_alt = get_first(
        images,
        ["with_alt", "images_with_alt", "images_with_alt_text", "alt_images"],
        audit_data.get("images_with_alt", "N/A")
    )

    alt_coverage = get_first(
        images,
        ["alt_coverage", "alt_text_coverage"],
        audit_data.get("alt_coverage", "N/A")
    )

    contact_form = get_first(
        contact,
        ["form_detected", "contact_form", "form"],
        audit_data.get("contact_form", "N/A")
    )

    report = []

    report.append("=" * 60)
    report.append("AI WEBSITE QUALITY AUDIT REPORT")
    report.append("=" * 60)

    # Website Information
    report.append("\nWEBSITE INFORMATION")
    report.append("-" * 60)
    report.append(f"Website: {website}")
    report.append(f"Status Code: {status_code}")
    report.append(f"Response Time: {response_time} seconds")

    # Overall Score
    report.append("\nOVERALL QUALITY SCORE")
    report.append("-" * 60)
    report.append(f"Overall Score: {overall_score} / 100")

    # Category Scores
    report.append("\nCATEGORY SCORES")
    report.append("-" * 60)

    categories = [
        ("performance", "Performance"),
        ("seo", "SEO"),
        ("structure", "Structure"),
        ("accessibility", "Accessibility"),
        ("cta", "CTA"),
        ("social_media", "Social Media"),
        ("contact", "Contact"),
        ("availability", "Availability"),
    ]

    for key, label in categories:
        report.append(
            f"{label}: {scores.get(key, 'N/A')}"
        )

    # SEO & Structure
    report.append("\nSEO & STRUCTURE DATA")
    report.append("-" * 60)

    report.append(
        f"Meta Title: {seo.get('meta_title', 'N/A')}"
    )

    report.append(
        f"Meta Description: {seo.get('meta_description', 'N/A')}"
    )

    report.append(
        f"H1 Count: {seo.get('h1_count', 'N/A')}"
    )

    report.append(
        f"Internal Links: {structure.get('internal_links', 'N/A')}"
    )

    pages_checked = structure.get("pages_checked", [])

    if isinstance(pages_checked, list):
        pages_count = len(pages_checked)
    else:
        pages_count = pages_checked

    report.append(
        f"Pages Checked: {pages_count}"
    )

    # Accessibility
    report.append("\nACCESSIBILITY DATA")
    report.append("-" * 60)

    report.append(
        f"Total Images: {total_images}"
    )

    report.append(
        f"Images With Alt Text: {images_with_alt}"
    )

    report.append(
        f"Alt Text Coverage: {alt_coverage}%"
    )

    # Food Business Features
    report.append("\nFOOD BUSINESS FEATURES")
    report.append("-" * 60)

    report.append(
        f"CTA Count: {ctas.get('count', 'N/A')}"
    )

    report.append(
        f"Contact Form: {contact_form}"
    )

    report.append(
        f"Social Links: {social.get('count', 'N/A')}"
    )

    # Issues
    report.append("\nDETECTED ISSUES")
    report.append("-" * 60)

    if issues:
        for issue in issues:
            report.append(f"- {issue}")
    else:
        report.append("- No major issues detected.")

    # Recommendations
    report.append("\nRULE-BASED RECOMMENDATIONS")
    report.append("-" * 60)

    if recommendations:
        for recommendation in recommendations:
            report.append(f"- {recommendation}")
    else:
        report.append("- No recommendations generated.")

    # AI Analysis
    report.append("\n" + "=" * 60)
    report.append("AI-POWERED ANALYSIS")
    report.append("=" * 60)

    report.append(ai_analysis)

    report.append("\n" + "=" * 60)
    report.append("END OF REPORT")
    report.append("=" * 60)

    return "\n".join(report)


def save_report(report, filename="final_report.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(report)


if __name__ == "__main__":

    print("==============================")
    print("REPORT GENERATOR")
    print("==============================")
    print()

    try:
        audit_data = load_json("website.json")
        ai_analysis = load_text("ai_analysis.txt")

        final_report = generate_report(
            audit_data,
            ai_analysis
        )

        print(final_report)

        save_report(final_report)

        print("\nFinal report saved to final_report.txt")

    except Exception as e:
        print("ERROR:", e)