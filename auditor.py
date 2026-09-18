import json
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
}

MAX_PAGES = 5


def normalize_url(url):
    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url.rstrip("/")


def fetch_website(url):
    """
    Try browser-based collection first.
    Fall back to requests if Playwright fails.
    """

    start_time = time.time()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            page = browser.new_page(
                user_agent=HEADERS["User-Agent"]
            )

            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30000
            )

            # Give JavaScript time to render dynamic content.
            page.wait_for_timeout(3000)

            html = page.content()

            status_code = response.status if response else 200

            browser.close()

            response_time = round(time.time() - start_time, 2)

            if status_code == 403:
                return {
                    "success": False,
                    "status_code": 403,
                    "response_time": response_time,
                    "html": "",
                    "error": "Website blocked automated access (HTTP 403 Forbidden)."
                }

            if status_code >= 400:
                return {
                    "success": False,
                    "status_code": status_code,
                    "response_time": response_time,
                    "html": "",
                    "error": f"Website returned HTTP {status_code}."
                }

            return {
                "success": True,
                "status_code": status_code,
                "response_time": response_time,
                "html": html,
                "error": None
            }

    except PlaywrightTimeoutError:
        return {
            "success": False,
            "status_code": None,
            "response_time": round(time.time() - start_time, 2),
            "html": "",
            "error": "Website loading timed out."
        }

    except Exception as browser_error:

        # Fallback to requests
        try:
            response = requests.get(
                url,
                headers=HEADERS,
                timeout=15,
                allow_redirects=True
            )

            response_time = round(time.time() - start_time, 2)

            if response.status_code == 403:
                return {
                    "success": False,
                    "status_code": 403,
                    "response_time": response_time,
                    "html": "",
                    "error": "Website blocked automated access (HTTP 403 Forbidden)."
                }

            if response.status_code >= 400:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "html": "",
                    "error": f"Website returned HTTP {response.status_code}."
                }

            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "html": response.text,
                "error": None
            }

        except requests.Timeout:
            return {
                "success": False,
                "status_code": None,
                "response_time": round(time.time() - start_time, 2),
                "html": "",
                "error": "Request timed out."
            }

        except requests.RequestException as request_error:
            return {
                "success": False,
                "status_code": None,
                "response_time": round(time.time() - start_time, 2),
                "html": "",
                "error": f"Request failed: {request_error}"
            }

        except Exception as request_error:
            return {
                "success": False,
                "status_code": None,
                "response_time": round(time.time() - start_time, 2),
                "html": "",
                "error": f"Unable to access website: {request_error}"
            }


def extract_basic_info(soup):
    title = soup.title.get_text(strip=True) if soup.title else ""

    meta_description = soup.find(
        "meta",
        attrs={"name": re.compile("^description$", re.I)}
    )

    description = (
        meta_description.get("content", "").strip()
        if meta_description
        else ""
    )

    headings = [
        heading.get_text(" ", strip=True)
        for heading in soup.find_all(["h1", "h2", "h3"])
    ]

    h1_count = len(soup.find_all("h1"))

    return {
        "meta_title": title,
        "meta_description": description,
        "headings": headings[:20],
        "h1_count": h1_count
    }


def extract_images(soup):
    images = soup.find_all("img")

    total_images = len(images)

    images_with_alt = sum(
        1 for img in images
        if img.get("alt") and img.get("alt").strip()
    )

    if total_images == 0:
        alt_coverage = None
    else:
        alt_coverage = round(
            (images_with_alt / total_images) * 100,
            1
        )

    return {
        "total_images": total_images,
        "images_with_alt": images_with_alt,
        "alt_coverage": alt_coverage
    }


def extract_navigation(soup, base_url):
    base_domain = urlparse(base_url).netloc

    internal_links = set()

    for link in soup.find_all("a", href=True):
        href = urljoin(base_url, link["href"])
        parsed = urlparse(href)

        if (
            parsed.scheme in ("http", "https")
            and parsed.netloc == base_domain
        ):
            clean_url = href.split("#")[0].rstrip("/")
            internal_links.add(clean_url)

    return sorted(internal_links)


def crawl_internal_pages(base_url, initial_links):
    pages_checked = [base_url]

    for link in initial_links:
        if len(pages_checked) >= MAX_PAGES:
            break

        if link == base_url:
            continue

        try:
            result = fetch_website(link)

            if result["success"]:
                pages_checked.append(link)

        except Exception:
            continue

    return pages_checked


def detect_contact_form(soup):
    return soup.find("form") is not None


def detect_contact_information(soup):
    text = soup.get_text(" ", strip=True).lower()

    keywords = [
        "contact",
        "phone",
        "telephone",
        "email",
        "customer service",
        "support"
    ]

    found = []

    for keyword in keywords:
        if keyword in text:
            found.append(keyword)

    return found


def detect_ctas(soup):
    cta_keywords = [
        "order now",
        "order online",
        "book now",
        "book a table",
        "reserve",
        "reservation",
        "view menu",
        "menu",
        "find a location",
        "find locations",
        "delivery",
        "contact us",
        "call now",
        "shop now",
        "join now",
        "rewards"
    ]

    found = []

    for element in soup.find_all(["a", "button"]):
        text = element.get_text(" ", strip=True).lower()

        if not text:
            continue

        for keyword in cta_keywords:
            if keyword in text:
                if keyword not in found:
                    found.append(keyword)
                break

    return found


def extract_social_links(soup):
    social_domains = [
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "tiktok.com",
        "twitter.com",
        "x.com",
        "linkedin.com"
    ]

    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if any(domain in href.lower() for domain in social_domains):
            if href not in links:
                links.append(href)

    return links


def calculate_scores(
    response_time,
    basic_info,
    images,
    ctas,
    social_links,
    contact_form,
    contact_information
):

    # Performance
    if response_time <= 2:
        performance = 15
    elif response_time <= 4:
        performance = 10
    elif response_time <= 6:
        performance = 5
    else:
        performance = 0

    # SEO
    seo = 15

    if not basic_info["meta_title"]:
        seo -= 5

    if not basic_info["meta_description"]:
        seo -= 3

    if basic_info["h1_count"] != 1:
        seo -= 3

    seo = max(seo, 0)

    # Structure
    structure = 15

    if basic_info["h1_count"] == 0:
        structure -= 5

    if len(basic_info["headings"]) == 0:
        structure -= 5

    structure = max(structure, 0)

    # Accessibility
    if images["alt_coverage"] is None:
        accessibility = 0
    elif images["alt_coverage"] >= 90:
        accessibility = 15
    elif images["alt_coverage"] >= 80:
        accessibility = 12
    elif images["alt_coverage"] >= 50:
        accessibility = 8
    else:
        accessibility = 4

    # CTA
    cta_score = 10 if ctas else 0

    # Social media
    social_score = 10 if social_links else 0

    # Contact
    contact_score = 10 if contact_form else 0

    if contact_information:
        contact_score = max(contact_score, 6)

    # Availability
    availability = 10

    scores = {
        "performance": performance,
        "seo": seo,
        "structure": structure,
        "accessibility": accessibility,
        "cta": cta_score,
        "social_media": social_score,
        "contact": contact_score,
        "availability": availability
    }

    scores["total"] = sum(scores.values())

    return scores


def detect_issues(
    response_time,
    basic_info,
    ctas,
    contact_form,
    contact_information,
    social_links
):

    issues = []
    recommendations = []

    if response_time > 4:
        issues.append(
            "Website response time is above 4 seconds."
        )

        recommendations.append(
            "Improve website loading performance by optimizing images, scripts, and resources."
        )

    if not basic_info["meta_title"]:
        issues.append("Meta title is missing.")
        recommendations.append(
            "Add a concise and descriptive meta title."
        )

    if not basic_info["meta_description"]:
        issues.append("Meta description is missing.")
        recommendations.append(
            "Add a concise meta description describing the food business."
        )

    if basic_info["h1_count"] == 0:
        issues.append(
            "No H1 heading was detected in the fetched HTML."
        )

        recommendations.append(
            "Add one clear H1 heading describing the main purpose of the page."
        )

    elif basic_info["h1_count"] > 1:
        issues.append(
            "Multiple H1 headings were detected."
        )

        recommendations.append(
            "Review the page heading structure and use one primary H1."
        )

    if not ctas:
        issues.append(
            "No common food-business CTA was detected."
        )

        recommendations.append(
            "Consider adding clear CTAs such as 'Order Now', 'View Menu', or 'Find a Location'."
        )

    if not contact_form and not contact_information:
        issues.append(
            "No obvious contact form or contact information was detected."
        )

        recommendations.append(
            "Provide clear customer contact options."
        )

    if not social_links:
        issues.append(
            "No social media links were detected."
        )

        recommendations.append(
            "Consider linking official social media accounts where appropriate."
        )

    return issues, recommendations


def audit_website(url):
    url = normalize_url(url)

    result = fetch_website(url)

    if not result["success"]:
        return {
            "website": url,
            "success": False,
            "status_code": result["status_code"],
            "response_time": result["response_time"],
            "error": result["error"]
        }

    soup = BeautifulSoup(result["html"], "html.parser")

    basic_info = extract_basic_info(soup)

    images = extract_images(soup)

    internal_links = extract_navigation(
        soup,
        url
    )

    pages_checked = crawl_internal_pages(
        url,
        internal_links
    )

    contact_form = detect_contact_form(soup)

    contact_information = detect_contact_information(soup)

    ctas = detect_ctas(soup)

    social_links = extract_social_links(soup)

    scores = calculate_scores(
        result["response_time"],
        basic_info,
        images,
        ctas,
        social_links,
        contact_form,
        contact_information
    )

    issues, recommendations = detect_issues(
        result["response_time"],
        basic_info,
        ctas,
        contact_form,
        contact_information,
        social_links
    )

    audit_data = {
        "website": url,
        "success": True,
        "status_code": result["status_code"],
        "response_time": result["response_time"],

        "seo": {
            "meta_title": basic_info["meta_title"],
            "meta_description": basic_info["meta_description"],
            "h1_count": basic_info["h1_count"]
        },

        "structure": {
            "pages_found": len(pages_checked),
            "internal_links": len(internal_links),
            "pages_checked": pages_checked
        },

        "contact": {
            "contact_form": contact_form,
            "contact_information": contact_information
        },

        "ctas": {
            "count": len(ctas),
            "detected": ctas
        },

        "social_media": {
            "count": len(social_links),
            "links": social_links
        },

        "images": images,

        "scores": scores,

        "issues": issues,

        "recommendations": recommendations
    }

    return audit_data


def save_audit(data):
    with open(
        "website.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def print_report(data):
    print("\n==============================")
    print("FOOD WEBSITE QUALITY AUDIT")
    print("==============================")

    print("Website:", data["website"])
    print("Success:", data["success"])

    if not data["success"]:
        print("Status Code:", data["status_code"])
        print("ERROR:", data["error"])
        return

    print("Status Code:", data["status_code"])
    print("Response Time:", data["response_time"], "seconds")

    print("\n--- SEO ---")
    print("Meta Title:", data["seo"]["meta_title"])
    print("Meta Description:", data["seo"]["meta_description"])
    print("H1 Count:", data["seo"]["h1_count"])

    print("\n--- STRUCTURE ---")
    print("Pages Found:", data["structure"]["pages_found"])
    print("Internal Links:", data["structure"]["internal_links"])

    print("Pages Checked:")

    for page in data["structure"]["pages_checked"]:
        print(" -", page)

    print("\n--- CONTACT ---")
    print(
        "Contact Form:",
        data["contact"]["contact_form"]
    )

    print(
        "Contact Information:",
        data["contact"]["contact_information"]
    )

    print("\n--- CTAs ---")
    print(
        "CTA Count:",
        data["ctas"]["count"]
    )

    print(
        "CTAs:",
        data["ctas"]["detected"]
    )

    print("\n--- SOCIAL MEDIA ---")
    print(
        "Social Links:",
        data["social_media"]["count"]
    )

    print(
        "Links:",
        data["social_media"]["links"]
    )

    print("\n--- IMAGES ---")
    print(
        "Total Images:",
        data["images"]["total_images"]
    )

    print(
        "Images With Alt:",
        data["images"]["images_with_alt"]
    )

    print(
        "Alt Coverage:",
        data["images"]["alt_coverage"]
    )

    print("\n--- QUALITY SCORE ---")

    for key, value in data["scores"].items():
        label = key.replace("_", " ").title()

        if key == "total":
            print("Overall Score:", value, "/ 100")
        else:
            print(f"{label}:", value)

    print("\n--- ISSUES ---")

    if data["issues"]:
        for issue in data["issues"]:
            print(" -", issue)
    else:
        print(" - None detected.")

    print("\n--- RECOMMENDATIONS ---")

    if data["recommendations"]:
        for recommendation in data["recommendations"]:
            print(" -", recommendation)
    else:
        print(" - None.")


if __name__ == "__main__":

    # Change this URL when testing another food website.
    test_url = "https://www.starbucks.com/"

    audit = audit_website(test_url)

    save_audit(audit)

    print_report(audit)