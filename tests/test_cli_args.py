"""..."""

from qyx.utils import parse_path_arg


def test_parse_path_arg():
    test_cases = [
        ".",
        "https://github.com/user/myProject",
        "/users/me/projects/development/myProject",
        "../../../anotherDir/myProject",
        "https://github.com/user/myproject.git",
    ]

    for test in test_cases:
        # print()
        # print(f"Input: {test}")
        # print(f"  Normalised : {normalised}")
        # print(f"  Name       : {name}")
        # print(f"  Is Git?    : {is_git}")
        normalised, name, is_git = parse_path_arg(test)
