from pathlib import Path

from django.test import SimpleTestCase


class DocumentationTests(SimpleTestCase):
    def test_docs_do_not_contain_stale_setup_language(self):
        stale_terms = ["service provider", "composer", "Current scope", "does not yet include"]
        docs = list(Path("docs").glob("**/*.md")) + [Path("README.md")]

        for path in docs:
            content = path.read_text()
            for term in stale_terms:
                self.assertNotIn(term, content, f"{path} contains stale term {term!r}")

    def test_org_php_directory_is_removed(self):
        self.assertFalse(Path("org_php").exists())

    def test_core_platform_topics_are_documented(self):
        combined = "\n".join(path.read_text() for path in Path("docs").glob("**/*.md")) + Path("README.md").read_text()

        for topic in [
            "ApplePass",
            "APNs",
            "Pass Type ID",
            "Passes Class",
            "Passes Object",
            "Save to Wallet",
            "ECv2SigningOnly",
            "set_remote_logo_image",
            "push_updates_on_save",
            "MOBILE_PASS.queue",
            "public HTTPS URLs",
            "Authorization",
            "AGENTS.md",
        ]:
            self.assertIn(topic, combined)

    def test_deprecated_google_callback_setting_is_not_documented(self):
        docs = list(Path("docs").glob("**/*.md")) + [Path("README.md")]

        for path in docs:
            self.assertNotIn(
                "callback_signing_key",
                path.read_text(),
                f"{path} still documents deprecated callback_signing_key",
            )
