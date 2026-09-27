import pytest

from main import parse_args


def test_parse_args_defaults():
    args = parse_args([
        "--url",
        "example.com",
    ])

    assert args.url == "example.com"
    assert args.device == "mobile"
    assert args.format == "markdown"
    assert args.output is None
    assert args.recommendation_limit is None


def test_parse_args_accepts_recommendation_limit():
    args = parse_args([
        "--url",
        "https://example.com/",
        "--format",
        "json",
        "--device",
        "desktop",
        "--recommendation-limit",
        "3",
    ])

    assert args.format == "json"
    assert args.device == "desktop"
    assert args.recommendation_limit == 3


def test_parse_args_rejects_unsupported_device():
    with pytest.raises(SystemExit):
        parse_args([
            "--url",
            "example.com",
            "--device",
            "tablet",
        ])
