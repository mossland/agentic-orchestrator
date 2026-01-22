"""
CLI entry point for scheduler tasks.

Usage:
    python -m agentic_orchestrator.scheduler signal-collect
    python -m agentic_orchestrator.scheduler run-debate
    python -m agentic_orchestrator.scheduler process-backlog
    python -m agentic_orchestrator.scheduler health-check
"""

import sys
import argparse
from .tasks import signal_collect, run_debate, process_backlog, health_check


def main():
    parser = argparse.ArgumentParser(
        description='Mossland Agentic Orchestrator Scheduler',
        prog='python -m agentic_orchestrator.scheduler',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # signal-collect command
    subparsers.add_parser(
        'signal-collect',
        help='Collect signals from all adapters',
    )

    # run-debate command
    debate_parser = subparsers.add_parser(
        'run-debate',
        help='Run multi-stage debate',
    )
    debate_parser.add_argument(
        '--topic',
        type=str,
        default=None,
        help='Optional debate topic (auto-selected from signals if not provided)',
    )

    # process-backlog command
    subparsers.add_parser(
        'process-backlog',
        help='Process pending backlog items',
    )

    # health-check command
    subparsers.add_parser(
        'health-check',
        help='Check system health',
    )

    args = parser.parse_args()

    if args.command == 'signal-collect':
        signal_collect()
    elif args.command == 'run-debate':
        run_debate(topic=args.topic if hasattr(args, 'topic') else None)
    elif args.command == 'process-backlog':
        process_backlog()
    elif args.command == 'health-check':
        health_check()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
