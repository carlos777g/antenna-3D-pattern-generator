# main.py
"""
CLI entry point for the radiation pattern extraction pipeline.

Run the whole calibrated queue:
    python main.py

Run a single image:
    python main.py --image datasheets/taoglas-1.png --manufacturer taoglas --plane XZ
"""
import argparse
import logging
import sys

from pipeline import DEFAULT_OUTPUT_DIR, PROCESSING_QUEUE, run_pipeline
from modules.result_writer import VALID_PLANES


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract 2D polar radiation patterns from datasheet images.",
    )
    parser.add_argument(
        "--image",
        help="Path to a single image to process. Relative paths resolve "
             "against the service directory, not the working directory.",
    )
    parser.add_argument(
        "--manufacturer",
        help="Manufacturer config key. Required with --image.",
    )
    parser.add_argument(
        "--plane",
        choices=sorted(VALID_PLANES),
        help="Cut plane of the datasheet image. Required with --image.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write results into (default: %(default)s).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and write intermediate overlay images.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    if args.image:
        if not args.manufacturer or not args.plane:
            parser.error("--image requires both --manufacturer and --plane")
        entries = [{
            "image": args.image,
            "manufacturer": args.manufacturer,
            "plane": args.plane,
        }]
    else:
        if args.manufacturer or args.plane:
            parser.error("--manufacturer and --plane are only valid with --image")
        entries = PROCESSING_QUEUE

    results = run_pipeline(entries, output_dir=args.output_dir, debug=args.debug)

    failed = [r for r in results if "error" in r]
    logging.info(
        "Done. %d/%d succeeded.", len(results) - len(failed), len(results)
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
