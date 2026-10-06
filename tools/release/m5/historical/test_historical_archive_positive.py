"""Required archive-materialization positive, separate from source-only unit suite.

Reads four materialized published files as data. Never imports their Python code.
Paths default to this evidence directory; CI may pass --client and --lock.
"""
import argparse
from pathlib import Path
import historical_runtime_probe as probe


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client', type=Path, default=here / 'materialized-client')
    parser.add_argument('--lock', type=Path, default=here / 'HISTORICAL_CONSUMER_LOCK.json')
    args = parser.parse_args()
    actual = probe.pinned_client(args.client, args.lock)
    if actual != probe.FILES:
        raise AssertionError('Materialized historical client differs')
    print('PASS_ARCHIVE_MATERIALIZATION_POSITIVE: exact four preserved files; no code executed')


if __name__ == '__main__':
    main()
