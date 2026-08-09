from crewai.tools import tool
import requests

@tool("Dependency Vulnerability Checker")
def check_vulnerabilities(package_name: str, ecosystem: str = "PyPI") -> str:
    """
    Checks a package name against the OSV.dev vulnerability database for known CVEs.
    package_name: name of the package, e.g. 'flask', 'requests', 'lodash'
    ecosystem: package ecosystem - 'PyPI' for Python, 'npm' for JavaScript, etc.
    Returns a summary of any known vulnerabilities found.
    """
    url = "https://api.osv.dev/v1/query"
    payload = {
        "package": {
            "name": package_name,
            "ecosystem": ecosystem
        }
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        return f"Error checking {package_name}: {response.status_code}"

    data = response.json()
    vulns = data.get("vulns", [])

    if not vulns:
        return f"{package_name}: No known vulnerabilities found."

    output = f"{package_name}: {len(vulns)} known vulnerabilities found:\n"
    for v in vulns[:3]:  # limit to top 3 per package to keep output manageable
        output += f"- {v.get('id')}: {v.get('summary', 'No summary available')}\n"

    return output


@tool("Bulk Dependency Vulnerability Checker")
def check_multiple_vulnerabilities(package_names_comma_separated: str, ecosystem: str = "PyPI") -> str:
    """
    Checks MULTIPLE packages at once against the OSV.dev vulnerability database.
    package_names_comma_separated: comma-separated package names, e.g. 'flask, requests, jinja2'
    ecosystem: package ecosystem - 'PyPI' for Python, 'npm' for JavaScript, etc.
    Returns a combined summary of vulnerabilities found across all packages.
    """
    packages = [p.strip() for p in package_names_comma_separated.split(",") if p.strip()]

    if not packages:
        return "No packages provided to check."

    results = []
    for pkg in packages[:10]:  # cap at 10 packages to avoid excessive API calls
        url = "https://api.osv.dev/v1/query"
        payload = {"package": {"name": pkg, "ecosystem": ecosystem}}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                results.append(f"{pkg}: Error checking (status {response.status_code})")
                continue
            data = response.json()
            vulns = data.get("vulns", [])
            if not vulns:
                results.append(f"{pkg}: No known vulnerabilities.")
            else:
                results.append(f"{pkg}: {len(vulns)} vulnerabilities found (e.g. {vulns[0].get('id')})")
        except Exception as e:
            results.append(f"{pkg}: Error - {str(e)}")

    return "\n".join(results)