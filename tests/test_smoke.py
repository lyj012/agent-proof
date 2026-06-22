import argparse

import agentproof
from agentproof.cli import create_parser


def test_package_can_be_imported() -> None:
    assert agentproof is not None


def test_version_is_0_1_0() -> None:
    assert agentproof.__version__ == "0.1.0"


def test_cli_parser_can_be_created() -> None:
    parser = create_parser()
    assert isinstance(parser, argparse.ArgumentParser)
