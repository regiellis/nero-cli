import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import tempfile
import json
import sys

# Import the necessary functions from your main script
from nero_cli.cli import (
    nero,
    Colors,
    get_config_dir,
    CONFIG_FILE,
    get_latest_version,
    check_and_display_config,
    prompt_user,
    check_for_updates,
    update_config,
    load_config,
    save_config,
    cleanup,
    get_rollback_version,
)


class TestInvokeAIInstaller(unittest.TestCase):
    def setUp(self):
        self.args = argparse.Namespace(
            version=None,
            dry_run=False,
            update_config=False,
            download_dir=None,
            download_only=False,
            keep=False,
            check=False,
            latest=False,
            rollback=False,
            use_pyenv=False,
        )
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.config_file = self.config_dir / "nero.json"

        patcher = patch("nero_cli.cli.CONFIG_DIR", self.config_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        patcher = patch("nero_cli.cli.CONFIG_FILE", self.config_file)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        tempfile.rmtree(self.temp_dir)

    @patch("nero_cli.cli.get_latest_version")
    @patch("nero_cli.cli.download_file")
    @patch("nero_cli.cli.run_command_and_wait")
    @patch("nero_cli.cli.update_config")
    @patch("builtins.input", return_value="y")
    def test_successful_installation(
        self,
        mock_input,
        mock_update_config,
        mock_run_command,
        mock_download,
        mock_get_version,
    ):
        mock_get_version.return_value = "0.1"
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.OKGREEN}Installation completed successfully{Colors.ENDC}"
            )

    @patch("nero_cli.cli.get_latest_version")
    @patch("nero_cli.cli.download_file")
    @patch("builtins.input", return_value="y")
    def test_dry_run(self, mock_input, mock_download, mock_get_version):
        mock_get_version.return_value = "0.1"
        self.args.dry_run = True
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.WARNING}[DRY RUN] Would download: https://github.com/invoke-ai/InvokeAI/releases/download/v0.1/InvokeAI-installer-v0.1.zip to {Path(mock_download.call_args[0][1])}{Colors.ENDC}"
            )

    @patch("nero_cli.cli.get_latest_version")
    @patch("nero_cli.cli.update_config")
    @patch("builtins.input", return_value="y")
    def test_update_config_only(self, mock_input, mock_update_config, mock_get_version):
        mock_get_version.return_value = "0.1"
        self.args.update_config = True
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.OKGREEN}Configuration updated successfully{Colors.ENDC}"
            )

    @patch("nero_cli.cli.get_latest_version")
    @patch("nero_cli.cli.download_file")
    @patch("builtins.input", return_value="y")
    def test_download_only_and_keep(self, mock_input, mock_download, mock_get_version):
        mock_get_version.return_value = "0.1"
        self.args.download_only = True
        self.args.keep = True
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.OKGREEN}File saved to: {Path(mock_download.call_args[0][1])}{Colors.ENDC}"
            )

    @patch("nero_cli.cli.get_latest_version")
    @patch("nero_cli.cli.check_directory_permissions")
    @patch("builtins.input", return_value="y")
    def test_no_write_permission_error(
        self, mock_input, mock_check_permissions, mock_get_version
    ):
        mock_get_version.return_value = "0.1"
        mock_check_permissions.return_value = False
        self.args.download_dir = "/no-write-permissions"
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.FAIL}Error: No write permission for directory /no-write-permissions{Colors.ENDC}"
            )

    @patch("nero_cli.cli.get_latest_version")
    @patch("builtins.input", return_value="y")
    def test_general_error(self, mock_input, mock_get_version):
        mock_get_version.side_effect = Exception("Test error")
        with patch("builtins.print") as mock_print:
            nero(self.args)
            mock_print.assert_any_call(
                f"{Colors.FAIL}An error occurred: Test error{Colors.ENDC}"
            )

    @patch("builtins.input")
    @patch("nero_cli.cli.get_latest_version")
    def test_check_and_display_config(self, mock_get_version, mock_input):
        mock_get_version.return_value = "0.2"
        mock_input.side_effect = [
            "u",
            "",
        ]  # Simulate user input for upgrade and empty input for downgrade prompt

        config = {
            "current_version": "0.1",
            "previous_version": None,
            "last_update": "2023-01-01T00:00:00",
        }

        with patch("nero_cli.cli.load_config", return_value=config):
            result = check_and_display_config(config)

        self.assertEqual(result, "0.2")  # Should return the latest version for upgrade

        # Test downgrade scenario
        mock_input.side_effect = ["d", "0.1"]
        with patch("nero_cli.cli.load_config", return_value=config):
            result = check_and_display_config(config)

        self.assertEqual(result, "0.1")  # Should return the specified downgrade version

        # Test cancel scenario
        mock_input.side_effect = ["c"]
        with patch("nero_cli.cli.load_config", return_value=config):
            result = check_and_display_config(config)

        self.assertIsNone(result)  # Should return None for cancel

    @patch("nero_cli.cli.get_latest_version")
    @patch("builtins.input")
    def test_check_for_updates(self, mock_input, mock_get_version):
        mock_get_version.return_value = "0.2"

        # Test upgrade scenario
        mock_input.return_value = "u"
        result = check_for_updates("0.1")
        self.assertEqual(result, "0.2")

        # Test downgrade scenario
        mock_input.side_effect = ["d", "0.1"]
        result = check_for_updates("0.2")
        self.assertEqual(result, "0.1")

        # Test cancel scenario
        mock_input.return_value = "c"
        result = check_for_updates("0.1")
        self.assertIsNone(result)

        # Test when current version is latest
        mock_input.reset_mock()
        result = check_for_updates("0.2")
        self.assertIsNone(result)
        mock_input.assert_not_called()

        # Test when no current version
        mock_input.return_value = "y"
        result = check_for_updates("")
        self.assertEqual(result, "0.2")

        mock_input.return_value = "n"
        result = check_for_updates("")
        self.assertIsNone(result)

    def test_load_and_save_config(self):
        config = {
            "current_version": "0.1",
            "previous_version": None,
            "last_update": "2023-01-01T00:00:00",
        }

        save_config(config)
        loaded_config = load_config()

        self.assertEqual(config, loaded_config)

    @patch("builtins.input", return_value="y")
    def test_prompt_user(self, mock_input):
        result = prompt_user("Do you want to proceed?")
        self.assertTrue(result)

        mock_input.return_value = "n"
        result = prompt_user("Do you want to proceed?")
        self.assertFalse(result)

    @patch("builtins.input")
    def test_get_rollback_version(self, mock_input):
        config = {"previous_version": "0.1"}
        result = get_rollback_version(config)
        self.assertEqual(result, "0.1")

        config = {"previous_version": None}
        mock_input.return_value = "0.2"
        result = get_rollback_version(config)
        self.assertEqual(result, "0.2")

    @patch("os.remove")
    @patch("shutil.rmtree")
    def test_cleanup(self, mock_rmtree, mock_remove):
        zip_path = Path("/tmp/test.zip")
        cleanup(zip_path, keep=False)
        mock_remove.assert_called_once_with(zip_path)
        mock_rmtree.assert_called_once()

        mock_remove.reset_mock()
        mock_rmtree.reset_mock()
        cleanup(zip_path, keep=True)
        mock_remove.assert_not_called()
        mock_rmtree.assert_called_once()


if __name__ == "__main__":
    unittest.main()
