import argparse
import asyncio
import datetime
from pathlib import Path
from typing import List

from gpt_researcher import GPTResearcher


async def write_report(query, report_type="research_report"):
    researcher = GPTResearcher(query=query, report_type=report_type)
    rr = await researcher.conduct_research()
    return (await researcher.write_report(), researcher)


async def reports_for_query(
    name: str,
    query: str,
    reportTypes: List[str] = ["research"],
    outPath: str = ".",
    appendSupplementary: bool = False,
):
    print("reports_for_query!!!")
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
        wrote_files.append((Path(fname).resolve(), costs))
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
    args = parser.parse_args()
    reports = asyncio.run(
        reports_for_query(
            name=args.name, query=args.query, reportTypes=args.reportType.split(",")
        )
    )
    print(reports)
