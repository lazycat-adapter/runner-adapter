import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class RunnerAdapterContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.action = yaml.safe_load((ROOT / "lazycat-action.yml").read_text())
        cls.manifest = yaml.safe_load((ROOT / "lzc-manifest.yml").read_text())
        cls.package = yaml.safe_load((ROOT / "package.yml").read_text())
        cls.dockerfile = (ROOT / "image" / "Dockerfile").read_text()
        cls.network_setup = (ROOT / "image" / "network-setup.sh").read_text()

    def test_package_identity_and_online_baseline(self):
        self.assertEqual(self.package["package"], "cloud.lazycat.app.gitearunner")
        self.assertRegex(self.package["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(self.package["homepage"], "https://gitea.com/gitea/runner")

    def test_source_selects_stable_gitea_runner_tags(self):
        source = self.action["source"]
        self.assertEqual(source["url"], "https://gitea.com/gitea/runner.git")
        self.assertEqual(source["select"]["strategy"], "semver-tag")
        regex = source["select"]["tag_regex"]
        self.assertIsNotNone(re.fullmatch(regex, "v6.0.1"))
        self.assertIsNone(re.fullmatch(regex, "v6.0.1-rc1"))

    def test_custom_image_builds_the_upstream_dind_variant(self):
        prepare = self.action["build"]["prepare"]
        self.assertEqual(prepare["mode"], "dockerfile")
        self.assertEqual(prepare["dockerfile"], "image/Dockerfile")
        self.assertEqual(prepare["context"], "image")
        self.assertIn("SOURCE_VERSION", self.dockerfile)
        self.assertIn("docker.io/gitea/runner:${SOURCE_VERSION}-dind", self.dockerfile)
        self.assertIn("lazycat-runner-network-setup", self.dockerfile)
        self.assertEqual(self.action["images"][0]["delivery"]["mode"], "lazycat")

    def test_manifest_preserves_runner_registration_and_persistence(self):
        application = self.manifest["application"]
        self.assertEqual(application["subdomain"], "gitearunner")
        self.assertEqual(application["public_path"], ["/metrics"])
        self.assertEqual(application["routes"], ["/=http://gitearunner.cloud.lazycat.app.gitearunner.lzcapp:8099"])
        service = self.manifest["services"]["gitearunner"]
        self.assertEqual(service["binds"], ["/lzcapp/var/data:/data"])
        self.assertEqual(service["environment"]["CONFIG_FILE"], "/data/config.yaml")
        self.assertEqual(service["environment"]["GITEA_RUNNER_REGISTRATION_TOKEN"], "{{ .U.token }}")
        self.assertIn("lazycat-runner-network-setup", service["setup_script"])

    def test_network_setup_keeps_lazycat_socket_and_buildx_paths(self):
        self.assertIn("/lzcsys/run/lzc-docker/docker.sock", (ROOT / "image/migrate-config.py").read_text())
        self.assertIn("docker network create --driver bridge gitea-build", self.network_setup)
        self.assertIn("docker buildx create", self.network_setup)
        self.assertIn("docker buildx inspect --bootstrap gitea-runner-build", self.network_setup)
        self.assertIn("/data/config.yaml", self.network_setup)

    def test_delivery_uses_official_registry_reference(self):
        image = self.action["images"][0]
        self.assertEqual(image["source"], "docker.io/gitea/runner:{source_version}-dind")
        self.assertEqual(image["delivery"]["mode"], "lazycat")
        self.assertTrue(self.manifest["services"]["gitearunner"]["image"].startswith("registry.lazycat.cloud/"))


if __name__ == "__main__":
    unittest.main()
