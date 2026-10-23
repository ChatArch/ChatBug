from click.testing import CliRunner

from chatbug import __version__
from chatbug.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert f"chatbug, version {__version__}" in result.output


def test_help_lists_shared_tree_options():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "--tree" in result.output
    assert "--tree-brief" in result.output


def test_registered_generic_web_cli_tree():
    result = CliRunner().invoke(main, ["--tree"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("chatbug\n")
    assert "php2shell" in result.output
    assert "web" in result.output
    assert "check" in result.output
    assert "local-list" in result.output
    assert "docker-list" in result.output
    assert "\n  mail" not in result.output
    assert "owned website" in result.output


def test_tree_brief_keeps_nodes():
    result = CliRunner().invoke(main, ["--tree-brief"])
    assert result.exit_code == 0, result.output
    assert "php2shell" in result.output
    assert "docker-list" in result.output


def test_php2shell_help_lists_generic_groups_not_mail_group():
    result = CliRunner().invoke(main, ["php2shell", "--help"])
    assert result.exit_code == 0
    assert "web" in result.output
    assert "lab" in result.output
    assert "\n  mail" not in result.output
