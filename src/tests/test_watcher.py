# import unittest
# import subprocess
# import tempfile
# import time
# import requests
# import signal
# from pathlib import Path

# class TestCLI(unittest.TestCase):

#     @classmethod
#     def setUpClass(cls):
#         return super().setUpClass()
    
#     @classmethod
#     def tearDownClass(cls):
#         return super().tearDownClass()

#     def setUp(self):
#         return super().setUp()

#     def tearDown(self):
#         return super().tearDown()

#     def test_yogen_serve(self):
#         with tempfile.TemporaryDirectory() as tmpdir:
#             tmp_path = Path(tmpdir)
#             site_name = "newsite"

#             # Create the site first
#             subprocess.run(
#                 ["yogen", "create", site_name],
#                 cwd=tmp_path,
#                 capture_output=True,
#                 text=True
#             )

#             site_path = tmp_path / site_name

#             # Start the server in a separate process
#             proc = subprocess.Popen(
#                 ["yogen", "serve", "8001"],
#                 cwd=site_path,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 text=True,
#             )

#             try:
#                 # Give the server a moment to start
#                 time.sleep(1)

#                 # Check that the root URL responds
#                 resp = requests.get("http://127.0.0.1:8001/")
#                 self.assertEqual(resp.status_code, 200)
#                 self.assertIn("<html", resp.text)

#             finally:
#                 # Terminate the server
#                 proc.send_signal(signal.SIGINT)
#                 proc.wait(timeout=5)