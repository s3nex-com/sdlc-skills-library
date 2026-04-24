# Security policy

## Reporting a vulnerability

Do not open a public GitHub issue for security vulnerabilities.

Email **tzografos@gmail.com** with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 72 hours. If the report is confirmed, a fix will be released as soon as reasonably possible and you will be credited in the release notes unless you prefer to remain anonymous.

## Scope

This library is a collection of Markdown files and Python CLI scripts. It does not run as a service, handle user data, or accept network connections. Security-relevant reports are most likely to involve:

- The Python scripts executing unsafe input (e.g. shell injection via file paths)
- Reference material that gives incorrect security guidance

## Out of scope

- Theoretical vulnerabilities with no practical exploit path
- Issues in third-party dependencies (report those to the dependency maintainer directly)
