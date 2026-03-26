SYSTEM_PROMPT = """You are a helpful SAM.gov research assistant. You help users find federal contract opportunities, award data, and vendor information from SAM.gov.

When a user asks a question:
1. Use get_today_date first if the question involves recent or current data.
2. Choose the right tool: search_opportunities for open solicitations/RFPs, search_contract_awards for awarded contracts.
3. Summarize results clearly. Present key details like titles, agencies, deadlines, and solicitation numbers.
4. If no results are found, explain why and suggest alternative search terms or date ranges.
5. Always mention the total number of results found and the date range searched.
6. Format opportunity lists using markdown with bold titles and bullet points for details.
7. Be specific and factual — only report what the API actually returned.
8. Keep responses concise to stay within token limits.

Common NAICS codes:
- 541512: Computer Systems Design
- 541511: Custom Computer Programming
- 541519: Other Computer Related Services
- 541330: Engineering Services
- 541690: Other Scientific/Technical Consulting
- 336411: Aircraft Manufacturing

Common ptype codes:
- o = Solicitation (RFP, RFQ, IFB)
- p = Presolicitation
- a = Award Notice
- r = Sources Sought
- k = Special Notice
"""

TOOLS = [
    {
        "name": "get_today_date",
        "description": "Get today's date and common relative dates (7 days ago, 30 days ago). Use this before building date-based queries.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search_opportunities",
        "description": (
            "Search SAM.gov for federal contract opportunities (solicitations, awards, etc.). "
            "Use this when the user asks about open bids, RFPs, RFQs, solicitations, or contract opportunities. "
            "Dates must be in MM/DD/YYYY format. Default limit is 5 — only request more if the user explicitly asks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword":     {"type": "string",  "description": "Keyword to search in opportunity titles"},
                "ptype":       {"type": "string",  "description": "Notice type: 'o'=solicitation, 'p'=presolicitation, 'a'=award notice, 'r'=sources sought, 'k'=special notice"},
                "department":  {"type": "string",  "description": "Department name (e.g. 'Department of Defense', 'NASA')"},
                "naics_code":  {"type": "string",  "description": "NAICS code (e.g. '541512')"},
                "set_aside":   {"type": "string",  "description": "Set-aside type, e.g. 'Small Business', '8(a)', 'HUBZone', 'WOSB'"},
                "posted_from": {"type": "string",  "description": "Start date MM/DD/YYYY"},
                "posted_to":   {"type": "string",  "description": "End date MM/DD/YYYY"},
                "limit":       {"type": "integer", "description": "Max results (1-10). Default 5. Only go higher if user asks.", "default": 5},
                "state":       {"type": "string",  "description": "2-letter state code (e.g. 'VA', 'CA')"},
            },
            "required": [],
        },
    },
    {
        "name": "search_contract_awards",
        "description": (
            "Search SAM.gov for awarded contracts. Use when the user asks about who won contracts, "
            "award amounts, or past awards. Default limit is 5 — only request more if the user explicitly asks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "naics_code":         {"type": "string",  "description": "NAICS code filter"},
                "department_code":    {"type": "string",  "description": "Contracting department code, e.g. '9700' for DoD"},
                "state":              {"type": "string",  "description": "2-letter state code for place of performance"},
                "last_modified_from": {"type": "string",  "description": "Start date MM/DD/YYYY"},
                "limit":              {"type": "integer", "description": "Max results (1-10). Default 5. Only go higher if user asks.", "default": 5},
            },
            "required": [],
        },
    },
]
