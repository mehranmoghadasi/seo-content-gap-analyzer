"""In-memory pages for tests and the demo. Topic: 'best CRM software for small business'."""

from urllib.parse import urlsplit


def _page(title, paragraphs, main=True):
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    wrapper = f"<main><h1>{title}</h1>{body}</main>" if main else f"<h1>{title}</h1>{body}"
    return (f"<html><head><title>{title}</title><script>var a=1;</script></head><body>"
            f"<nav><a href='/'>Home</a> pricing customer data platform nav-noise</nav>"
            f"{wrapper}<footer>Copyright pipeline management footer-noise</footer></body></html>")


TARGET = _page("Best CRM Software for Small Business", [
    "A CRM helps small business owners track contacts and deals. Our CRM comparison covers pricing, "
    "ease of use and support. Every small business needs contact management and a simple sales pipeline.",
    "Pricing starts at $12 per user per month. Free trial available for all CRM plans.",
    "Contact management, email templates and reporting are included in every plan.",
] * 3)

COMPETITORS = {
    "https://alpha.example/crm-guide": _page("CRM Software Guide", [
        "Modern CRM platforms double as a customer data platform, unifying contact management with marketing "
        "automation. Lead scoring lets sales teams prioritise the sales pipeline.",
        "Sales pipeline management with lead scoring is the feature most small business buyers ask for. "
        "Workflow automation and email sequences save hours per week.",
        "Pricing for a CRM with marketing automation starts around $20 per user per month. Look for a "
        "customer data platform integration and a mobile app.",
    ] * 3),
    "https://beta.example/best-crm": _page("Best CRM Tools Compared", [
        "We tested ten CRM tools for small business. Lead scoring, workflow automation and a mobile app "
        "separate the leaders from the rest. Sales pipeline management should be drag and drop.",
        "A customer data platform layer matters if you run ads: it syncs audiences to Google and Meta. "
        "Contact management is table stakes.",
        "Pricing ranges from free plans to $50 per user. Marketing automation is usually an add-on.",
    ] * 3, main=False),
    "https://gamma.example/crm-small-business": _page("CRM for Small Business", [
        "Small business CRM buyers want contact management, a sales pipeline and reporting. Lead scoring "
        "is nice to have. Workflow automation reduces manual data entry.",
        "Mobile app quality varies a lot. Marketing automation and email sequences are the next step once "
        "the sales pipeline is under control.",
        "Compare pricing per user, free trial length and support hours before you commit.",
    ] * 3),
}

ROBOTS = {"https://beta.example/robots.txt": "User-agent: *\nDisallow: /private/\n"}


def fetch(url: str):
    if url in COMPETITORS:
        return 200, COMPETITORS[url].encode()
    if url == "https://yoursite.example/best-crm-software":
        return 200, TARGET.encode()
    if url in ROBOTS:
        return 200, ROBOTS[url].encode()
    if urlsplit(url).path == "/robots.txt":
        return 404, b""
    if url == "https://beta.example/private/secret":
        return 200, b"<html><body><main>secret</main></body></html>"
    return 404, b""
