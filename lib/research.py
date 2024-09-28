import argparse
import asyncio
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import List

import boto3
import markdown2
from gpt_researcher import GPTResearcher


@dataclass
class R2Config:
    endpoint: str
    bucket: str
    domain: str


def upload_report(reportPath: Path, config: R2Config):
    s3 = boto3.client(service_name="s3", endpoint_url=config.endpoint)
    name = f"{reportPath.stem}{reportPath.suffix}"
    s3.upload_file(reportPath, config.bucket, name)
    return f"{config.domain}/{name}"


async def write_report(query, report_type="research_report"):
    researcher = GPTResearcher(query=query, report_type=report_type)
    await researcher.conduct_research()
    return (await researcher.write_report(), researcher)


async def reports_for_query(
    name: str,
    query: str,
    r2config: R2Config,
    reportTypes: List[str] = ["research"],
    outPath: str = ".",
    appendSupplementary: bool = False,
):
    wrote_files = []
    for rep_type in reportTypes:
        report_type = f"{rep_type}_report"
        (report, researcher) = await write_report(query, report_type)
        ts = (
            datetime.datetime.now()
            .isoformat()
            .replace("-", "")
            .replace(":", "")
            .replace(".", "")
        )
        fname = f"{outPath}/{name}-{rep_type}_{ts}.md"
        with open(fname, "w") as f:
            f.write(report)
            costs = researcher.get_costs()
            if appendSupplementary:
                f.write("\n\n---\n\n")
                f.write(f"Costs: {costs}")
                f.write("\n\n---\n\n")
                f.write("Full context:\n")
                for context in researcher.get_research_context():
                    f.write(context)
        fpath = Path(fname).resolve()
        r2_url = upload_report(fpath, r2config)
        html_report = markdown2.markdown(report)
        html_path = fpath.with_suffix(".html")
        with open(html_path, "w") as hf:
            hf.write(html_report)
        html_r2 = upload_report(html_path, r2config)
        wrote_files.append((fpath, costs, r2_url, html_r2))
    return wrote_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Do some research")
    parser.add_argument("--query", help="The full query to research")
    parser.add_argument(
        "--name", help="The name of this query, will be used as a filename"
    )
    parser.add_argument(
        "--reportType",
        default="research",
        help='The report type, default is "research"; options are: \
                      resource,research,outline (can specify multiple as comma,separated)',
    )
    parser.add_argument("--r2endpoint")
    parser.add_argument("--r2bucket")
    parser.add_argument("--r2domain")
    args = parser.parse_args()
    reports = asyncio.run(
        reports_for_query(
            name=args.name,
            query=args.query,
            reportTypes=args.reportType.split(","),
            r2config=R2Config(
                endpoint=args.r2endpoint, bucket=args.r2bucket, domain=args.r2domain
            ),
        )
    )
    print(reports)
