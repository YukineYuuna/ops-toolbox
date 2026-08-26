import unittest

from modules import data, data_linux, data_mac


class CatalogContractTests(unittest.TestCase):
    def test_each_platform_catalog_is_well_formed(self):
        for name, module in (("Windows", data), ("macOS", data_mac), ("Linux", data_linux)):
            with self.subTest(platform=name):
                ids = [item["id"] for item in module.FUNCTIONS]
                self.assertEqual(len(ids), len(set(ids)), "duplicate tool id")
                declared = getattr(module, "CATEGORIES", [])
                categories = {item[0] for item in declared} or {item["category"] for item in module.FUNCTIONS}
                self.assertTrue(categories)
                self.assertTrue(all(item["category"] in categories for item in module.FUNCTIONS))
                self.assertTrue(all(callable(item["func"]) for item in module.FUNCTIONS))
                required = {"id", "name", "desc", "category", "danger", "admin", "reboot", "func"}
                self.assertTrue(all(required <= set(item) for item in module.FUNCTIONS))


if __name__ == "__main__":
    unittest.main()
