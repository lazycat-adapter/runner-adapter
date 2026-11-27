import runpy
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
migrate = runpy.run_path(str(ROOT / "image/migrate-config.py"))["migrate"]


class UpgradeTests(unittest.TestCase):
    def test_legacy_and_custom_configs_survive_restart(self):
        for extra in [{}, {"runner": {"file": "custom.runner", "envs": {"KEEP": "1"}},
                           "container": {"options": "--shm-size 1g", "valid_volumes": ["/work"]}}]:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "config.yaml"
                original = yaml.safe_dump({"metrics": {"enabled": True, "addr": ":8099"}, **extra})
                path.write_text(original)
                migrate(path)
                first = path.read_bytes()
                migrate(path)
                self.assertEqual(path.read_bytes(), first)
                self.assertEqual(path.with_name("config.before-lazycat-network.yaml").read_text(), original)
                config = yaml.safe_load(first)
                self.assertEqual(config["container"]["network"], "gitea-build")
                self.assertEqual(config["container"]["options"].count("/var/run/docker.sock"), 1)
                if extra:
                    self.assertEqual(config["runner"]["file"], "custom.runner")
                    self.assertEqual(config["runner"]["envs"]["KEEP"], "1")
                    self.assertIn("--shm-size 1g", config["container"]["options"])
                    self.assertIn("/work", config["container"]["valid_volumes"])

    def test_install_parameters_and_socket_are_packaged(self):
        build = yaml.safe_load((ROOT / "lzc-build.yml").read_text())
        params = yaml.safe_load((ROOT / build["deploy_params"]).read_text())["params"]
        self.assertEqual({p["id"] for p in params}, {"url", "token", "env", "name"})
        volume, = build["compose_override"]["services"]["gitearunner"]["volumes"]
        self.assertEqual(volume["source"], "/lzcsys/run/lzc-docker/docker.sock")
        self.assertEqual(volume["target"], "/var/run/docker.sock")
        self.assertIs(volume["read_only"], True)
