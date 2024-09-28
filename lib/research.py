import argparse
import asyncio
import datetime
import time
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
    researcher = GPTResearcher(query=query, report_type=report_type, verbose=False)
    await researcher.conduct_research()
    return (await researcher.write_report(), researcher)


async def reports_for_query(
    name: str,
    query: str,
    r2config: R2Config,
    reportTypes: List[str] = ["research"],
    outPath: str = ".",
):
    wrote_files = []
    for rep_type in reportTypes:
        report_type = f"{rep_type}_report"
        s_time = time.time()
        (report, researcher) = await write_report(query, report_type)
        elapsed = time.time() - s_time
        ts = (
            datetime.datetime.now()
            .isoformat()
            .replace("-", "")
            .replace(":", "")
            .replace(".", "")
        )
        fname = f"{outPath}/{name}-{rep_type}_{ts}.md"
        fpath = Path(fname).resolve()
        costs = researcher.get_costs()

        preamble = f"# Query\n**{query}**\n\n## Processing time: {elapsed} seconds\n\n"
        with open(fname, "w") as f:
            f.write(preamble)
            f.write(report)

        supl_fname = fpath.with_suffix(".supplementary.txt")
        with open(supl_fname, "w") as f:
            f.write(preamble)
            f.write(f"# Report type: {rep_type}\n\n")

            f.write("# Visited URLs:\n\n")
            for url in researcher.get_source_urls():
                f.write(f"{url}\n\n")
            f.write("\n\n")

            f.write("# Sub-topics:\n\n")
            sts = await researcher.get_subtopics()
            for _, st in sts:
                f.write(f"{st}\n")
            f.write("\n\n")

            f.write("# Full context:\n\n")
            for context in researcher.get_research_context():
                f.write(context)
                f.write("\n")

        with open(supl_fname, "r") as sr:
            supl_html_path = supl_fname.with_suffix(".html")
            with open(supl_html_path, "w") as sh:
                sh.write(markdown2.markdown(sr.read()))

        supl_url = upload_report(supl_fname, r2config)
        supl_html_url = upload_report(supl_html_path, r2config)

        r2_url = upload_report(fpath, r2config)
        html_report = markdown2.markdown(report)
        html_path = fpath.with_suffix(".html")
        with open(html_path, "w") as hf:
            hf.write(html_report)
        html_r2 = upload_report(html_path, r2config)

        wrote_files.append(
            (fpath, costs, elapsed, r2_url, html_r2, supl_url, supl_html_url)
        )
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
