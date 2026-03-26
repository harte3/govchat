import requests
from datetime import datetime, timedelta


def get_today_date() -> dict:
    """Returns today's date and common relative dates for API queries."""
    today = datetime.now()
    return {
        "today": today.strftime("%m/%d/%Y"),
        "thirty_days_ago": (today - timedelta(days=30)).strftime("%m/%d/%Y"),
        "seven_days_ago":  (today - timedelta(days=7)).strftime("%m/%d/%Y"),
    }


def search_opportunities(
    api_key: str,
    keyword: str = None,
    title: str = None,
    ptype: str = None,
    department: str = None,
    naics_code: str = None,
    set_aside: str = None,
    posted_from: str = None,
    posted_to: str = None,
    limit: int = 5,          # lowered from 10 to reduce token usage
    state: str = None,
) -> dict:
    """Search SAM.gov contract opportunities."""
    base_url = "https://api.sam.gov/prod/opportunities/v2/search"

    if not posted_from:
        posted_from = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    if not posted_to:
        posted_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "limit": min(limit, 10),  # cap at 10 to keep payloads small
        "postedFrom": posted_from,
        "postedTo": posted_to,
    }
    if keyword:
        params["title"] = keyword
    if title:
        params["title"] = title
    if ptype:
        params["ptype"] = ptype
    if department:
        params["deptname"] = department
    if naics_code:
        params["naicsCode"] = naics_code
    if set_aside:
        params["typeOfSetAsideDescription"] = set_aside
    if state:
        params["placeOfPerformanceState"] = state

    try:
        response = requests.get(base_url, params=params, timeout=20)
        data = response.json()

        if response.status_code != 200:
            return {"error": f"API error {response.status_code}: {data.get('errorMessage', str(data))}"}

        opportunities = data.get("opportunitiesData", [])
        results = []
        for opp in opportunities:
            contacts = opp.get("pointOfContact", [])
            contact_email = contacts[0].get("email", "N/A") if contacts else "N/A"
            # Only include fields Claude needs — keeps token count low
            results.append({
                "title": opp.get("title", "N/A"),
                "solicitation_number": opp.get("solicitationNumber", "N/A"),
                "department": opp.get("department", "N/A"),
                "agency": opp.get("subtierName", opp.get("subTier", "N/A")),
                "type": opp.get("type", "N/A"),
                "naics_code": opp.get("naicsCode", "N/A"),
                "set_aside": opp.get("typeOfSetAsideDescription", "N/A"),
                "posted_date": opp.get("postedDate", "N/A"),
                "response_deadline": opp.get("responseDeadLine", "N/A"),
                "active": opp.get("active", "N/A"),
                "contact_email": contact_email,
            })

        return {
            "total_records": data.get("totalRecords", len(results)),
            "returned": len(results),
            "date_range": f"{posted_from} to {posted_to}",
            "opportunities": results,
        }
    except Exception as e:
        return {"error": str(e)}


def search_contract_awards(
    api_key: str,
    naics_code: str = None,
    department_code: str = None,
    state: str = None,
    last_modified_from: str = None,
    limit: int = 5,          # lowered from 10 to reduce token usage
) -> dict:
    """Search SAM.gov contract awards."""
    base_url = "https://api.sam.gov/contract-awards/v1/search"

    if not last_modified_from:
        last_modified_from = (datetime.now() - timedelta(days=30)).strftime("%m/%d/%Y")
    last_modified_to = datetime.now().strftime("%m/%d/%Y")

    params = {
        "api_key": api_key,
        "lastModifiedDate": f"[{last_modified_from},{last_modified_to}]",
        "limit": min(limit, 10),  # cap at 10 to keep payloads small
    }
    if naics_code:
        params["naicsCode"] = naics_code
    if department_code:
        params["contractingDepartmentCode"] = department_code
    if state:
        params["placeOfPerformanceState"] = state

    try:
        response = requests.get(base_url, params=params, timeout=20)
        if response.status_code != 200:
            return {"error": f"API error {response.status_code}: {response.text[:300]}"}
        data = response.json()
        return {"awards": data, "date_range": f"{last_modified_from} to {last_modified_to}"}
    except Exception as e:
        return {"error": str(e)}
