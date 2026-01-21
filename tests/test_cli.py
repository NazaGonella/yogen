import unittest
import subprocess
import tempfile
import time
import requests
import signal
from pathlib import Path

class TestCLI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()
    
    @classmethod
    def tearDownClass(cls):
        return super().tearDownClass()

    def setUp(self):
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_yogen_create(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            site_name = "newsite"

            # run in temp folder
            result = subprocess.run(
                ["yogen", "create", site_name],
                cwd=tmp_path,
                capture_output=True,
                text=True
            )

            # CLI should exit successfully
            self.assertEqual(result.returncode, 0)

            # the site folder should exist
            site_path = tmp_path / site_name
            self.assertTrue(site_path.exists())
            self.assertTrue(site_path.is_dir())

            # .yogen marker file exists
            self.assertTrue((site_path / "yogen.toml").exists())

            # default folders exist
            for folder in ["content", "static", "templates"]:
                folder_path = site_path / folder
                print("Checking folder:", folder_path)
                self.assertTrue(folder_path.exists())
                self.assertTrue(folder_path.is_dir())

            # Default files exist (e.g., any markdown in content)
            self.assertTrue(any((site_path / "content").glob("*.md")))

    def test_yogen_build(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            site_name = "newsite"

            result = subprocess.run(
                ["yogen", "create", site_name],
                cwd=tmp_path,
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 0)

            site_path = tmp_path / site_name

            result = subprocess.run(
                ["yogen", "build"],
                cwd=site_path,
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 0)

            # The build folder should exist
            build_path = site_path / "build"
            self.assertTrue(build_path.exists())
            self.assertTrue(build_path.is_dir())

            # There should be an HTML file for each markdown in content
            content_path = site_path / "content"
            md_files = list(content_path.rglob("*.md"))
            for md in md_files:
                rel = md.relative_to(content_path)
                output_html = build_path / rel.parent / "index.html"
                self.assertTrue(output_html.exists())
                self.assertTrue(output_html.is_file())
    
    def test_yogen_serve(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            site_name = "newsite"

            # Create the site first
            subprocess.run(
                ["yogen", "create", site_name],
                cwd=tmp_path,
                capture_output=True,
                text=True
            )

            site_path = tmp_path / site_name

            # Start the server in a separate process
            proc = subprocess.Popen(
                ["yogen", "serve", "8001"],
                cwd=site_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                # Give the server a moment to start
                time.sleep(1)

                # Check that the root URL responds
                resp = requests.get("http://127.0.0.1:8001/")
                self.assertEqual(resp.status_code, 200)
                self.assertIn("<html", resp.text)

            finally:
                # Terminate the server
                proc.send_signal(signal.SIGINT)
                proc.wait(timeout=5)