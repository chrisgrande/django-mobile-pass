from pathlib import Path

from django.test import SimpleTestCase


class DocumentationTests(SimpleTestCase):
    def test_docs_do_not_contain_stale_setup_language(self):
        stale_terms = ["service provider", "composer", "Current scope", "does not yet include"]
        docs = list(Path("docs").glob("**/*.md")) + [Path("README.md"), Path("AGENTS.md")]

        for path in docs:
            content = path.read_text()
            for term in stale_terms:
                self.assertNotIn(term, content, f"{path} contains stale term {term!r}")

    def test_org_php_directory_is_removed(self):
        self.assertFalse(Path("org_php").exists())

    def test_core_platform_topics_are_documented(self):
        combined = "\n".join(path.read_text() for path in Path("docs").glob("**/*.md"))
        combined += Path("README.md").read_text()
        combined += Path("AGENTS.md").read_text()

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
            "PkPassReader.from_bytes",
            "apple_passes()",
            "is_currently_in_wallet",
            "InvalidPass",
        ]:
            self.assertIn(topic, combined)

    def test_deprecated_google_callback_setting_is_not_documented(self):
        docs = list(Path("docs").glob("**/*.md")) + [Path("README.md"), Path("AGENTS.md")]

        for path in docs:
            self.assertNotIn(
                "callback_signing_key",
                path.read_text(),
                f"{path} still documents deprecated callback_signing_key",
            )

    def test_docs_do_not_document_incorrect_pkpass_reader_api(self):
        docs = list(Path("docs").glob("**/*.md")) + [Path("AGENTS.md")]

        for path in docs:
            content = path.read_text()
            self.assertNotIn("pass_data()", content, f"{path} documents nonexistent PkPassReader.pass_data()")
            self.assertNotIn("PkPassReader(BytesIO", content, f"{path} documents incorrect PkPassReader constructor")

    def test_agents_md_does_not_document_invalid_has_mobile_passes_api(self):
        content = Path("AGENTS.md").read_text()
        self.assertNotIn("mobile_passes.apple()", content)
        self.assertNotIn("mobile_passes.google()", content)
