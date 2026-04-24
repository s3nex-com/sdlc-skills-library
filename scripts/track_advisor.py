"""
sdlc-skills-library Track Advisor

Suggests one or more domain tracks from a PRD excerpt or free-text description,
based on keyword matching against each track's activation signals.

Tracks are domain overlays (parallel to modes) that elevate mandatory skills,
tighten gate criteria, and inject reference material. See docs/tracks.md.

Usage:
    python scripts/track_advisor.py                     # interactive prompt
    python scripts/track_advisor.py --text "..."        # one-shot from text
    python scripts/track_advisor.py --file path/to/PRD.md
    python scripts/track_advisor.py --json
    python scripts/track_advisor.py --help

The advisor never auto-activates a track. It suggests; the user confirms.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Keyword → track mapping. Keys are lowercase. A phrase match against any keyword
# contributes a weight of 1 to that track's score. Multi-word keywords must match
# as a whole phrase (word-boundary on both sides).
TRACKS: dict[str, dict] = {
    "fintech-payments": {
        "title": "Fintech / Payments",
        "keywords": [
            "pci", "pci dss", "cardholder", "card vault", "tokenization",
            "payment intent", "charge flow", "payout", "reconciliation",
            "fraud detection", "chargeback", "dispute handling",
            "kyc", "aml", "money transmitter", "crypto custody",
            "stablecoin", "on-chain settlement",
        ],
    },
    "saas-b2b": {
        "title": "SaaS B2B",
        "keywords": [
            "multi-tenant", "multi tenant", "tenant isolation", "per-customer data",
            "sso", "saml", "oidc", "enterprise login", "idp integration",
            "rbac", "role-based access", "custom roles", "permissions model",
            "sla", "contractual uptime",
            "usage metering", "consumption-based billing", "per-seat pricing",
            "enterprise contract", "msa", "dpa",
        ],
    },
    "web-product": {
        "title": "Web product",
        "keywords": [
            "web product track", "web app track",
            "multi-user web app", "multi user web app",
            "user accounts", "user registration", "user management",
            "subscription billing", "stripe checkout", "stripe billing",
            "pricing tiers", "free plan", "pro plan", "team plan",
            "jwt auth", "oauth2", "pkce", "refresh token", "refresh tokens",
            "rest api and frontend", "api with react", "api with vue",
            "api with next.js", "api with nextjs", "full-stack web app",
            "optimistic locking", "idempotency key", "idempotency keys",
            "row-level security", "rls policy",
            "rate limiting", "abuse prevention",
            "optimistic ui", "error boundaries",
        ],
    },
    "data-platform-mlops": {
        "title": "Data platform / ML ops",
        "keywords": [
            "data pipeline", "etl", "elt", "data warehouse", "data lake",
            "schema registry", "avro", "protobuf topic",
            "data quality", "data contract", "upstream broke us",
            "ml model", "model training", "model versioning",
            "mlflow", "weights & biases", "weights and biases",
            "feature store", "offline/online parity",
            "llm production", "rag pipeline", "prompt eval",
        ],
    },
    "healthcare-hipaa": {
        "title": "Healthcare / HIPAA",
        "keywords": [
            "hipaa", "phi", "protected health information",
            "patient data", "clinical notes", "medical records", "ehr integration",
            "hl7", "fhir", "hie",
            "baa", "business associate agreement",
            "de-identification", "safe harbor method", "expert determination",
            "medical device", "fda 510(k)", "samd",
        ],
    },
    "regulated-government": {
        "title": "Regulated / government",
        "keywords": [
            "fedramp", "stateramp", "authority to operate", "ato",
            "soc 2", "soc2", "type i", "type ii", "trust services criteria",
            "iso 27001", "isms", "statement of applicability",
            "cmmc", "defense contractor", "cui",
            "government contract", "public sector", "fisma",
        ],
    },
    "real-time-streaming": {
        "title": "Real-time / streaming",
        "keywords": [
            "kafka", "kinesis", "pub/sub", "pubsub", "nats", "pulsar", "rabbitmq streams",
            "streaming", "event streaming", "real-time pipeline",
            "low latency", "sub-100ms", "p99 latency budget",
            "exactly-once", "at-least-once", "at-most-once",
            "backpressure", "windowing", "watermarks", "stream processing",
            "flink", "spark streaming", "kafka streams", "ksqldb",
        ],
    },
    "consumer-product": {
        "title": "Consumer product",
        "keywords": [
            "a/b test", "ab test", "experiment", "split test", "variant",
            "product analytics", "event tracking", "funnel analysis",
            "amplitude", "mixpanel", "heap", "posthog", "segment",
            "referral", "viral loop", "growth feature",
            "consumer", "b2c", "end user",
            "push notification engagement", "retention metric",
        ],
    },
    "open-source": {
        "title": "Open source",
        "keywords": [
            "open source this", "publish to npm", "publish to pypi", "publish to crates.io",
            "github public",
            "semver", "semantic versioning", "breaking change policy",
            "deprecation", "sunset this feature", "migration guide",
            "contributor guide", "contributing.md",
            "security advisory", "cve disclosure", "security@",
            "license compliance", "spdx", "osi-approved",
        ],
    },
    "mobile": {
        "title": "Mobile",
        "keywords": [
            "ios", "android", "react native", "flutter",
            "app store", "app store connect", "play console",
            "testflight", "internal testing track",
            "mobile app release", "app version", "app update",
            "push notification", "apns", "fcm",
            "offline-first", "offline mode", "sync engine",
        ],
    },
}


def score_text(text: str) -> list[dict]:
    """Return a list of {track, title, score, matches} sorted by score desc."""
    lower = text.lower()
    results = []
    for track_id, spec in TRACKS.items():
        matches = []
        for kw in spec["keywords"]:
            # Word boundary on both sides. Escape regex-special characters in kw.
            pattern = r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])"
            if re.search(pattern, lower):
                matches.append(kw)
        if matches:
            results.append({
                "track": track_id,
                "title": spec["title"],
                "score": len(matches),
                "matches": matches,
            })
    results.sort(key=lambda r: (-r["score"], r["track"]))
    return results


def format_text(results: list[dict]) -> str:
    if not results:
        return (
            "No tracks matched. The description does not contain domain signals\n"
            "that map to any of the 10 tracks. Proceeding without a track is fine —\n"
            "most projects run without one."
        )

    lines = ["Suggested track(s), ranked by keyword match count:", "-" * 60]
    for i, r in enumerate(results, 1):
        lead = "strong suggestion" if i == 1 and r["score"] >= 3 else "match"
        lines.append(f"{i}. {r['title']}  ({lead}, score {r['score']})")
        lines.append(f"   track id: {r['track']}")
        lines.append(f"   matched: {', '.join(r['matches'][:8])}"
                     + (" ..." if len(r['matches']) > 8 else ""))
        lines.append("")

    lines.append("The orchestrator will never auto-activate a track. Confirm before")
    lines.append("starting the pipeline. Declaration example:")
    top = results[0]
    lines.append(f"  \"Standard mode, {top['title']} track — <feature description>\"")
    return "\n".join(lines)


def read_input(args) -> str:
    if args.text:
        return args.text
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(2)
        return path.read_text(encoding="utf-8")
    # Interactive: read multi-line stdin until EOF.
    print("Paste PRD / feature description (end with Ctrl-D):", file=sys.stderr)
    return sys.stdin.read()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="sdlc-skills-library Track Advisor — suggest domain tracks from text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/track_advisor.py --text "build PCI-compliant card vaulting"
  python scripts/track_advisor.py --file docs/PRD.md
  python scripts/track_advisor.py --text "multi-tenant SSO with SLA credits" --json
        """,
    )
    parser.add_argument("--text", help="Free-text description to analyze")
    parser.add_argument("--file", help="Path to a file to analyze (e.g. a PRD)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    text = read_input(args)
    results = score_text(text)

    if args.json:
        print(json.dumps({"suggested_tracks": results}, indent=2))
    else:
        print(format_text(results))


if __name__ == "__main__":
    main()
