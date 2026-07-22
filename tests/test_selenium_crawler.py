import unittest
from types import SimpleNamespace

import mock

from webcrawler.selenium_crawler import GenericCrawler


class TestGenericCrawlerClientTimeout(unittest.TestCase):
    """Regression test for the unhandled requests.exceptions.ReadTimeout failure.

    The Selenium client's HTTP command read-timeout defaults to the ambient
    socket.getdefaulttimeout() of the runtime, which can be far shorter than the
    browser-side page_load_timeout. GenericCrawler must align the client command
    timeout with the configured page-load budget so a slow-but-valid page load does
    not raise a client-side ReadTimeout before page_load_timeout is reached.
    """

    def _build_crawler(self, page_load_timeout, ambient_client_timeout):
        # Fake driver whose command_executor.client_config.timeout starts at the
        # (short) ambient value, mimicking the runtime's socket default.
        fake_client_config = SimpleNamespace(timeout=ambient_client_timeout)
        fake_driver = mock.MagicMock()
        fake_driver.command_executor.client_config = fake_client_config
        fake_driver.current_window_handle = "main-window"

        with mock.patch.object(GenericCrawler, "_get_driver", return_value=fake_driver):
            crawler = GenericCrawler(
                start_url="https://example.com",
                resolution="1920x1080",
                download_folder="/tmp",
                component_interface=mock.MagicMock(),
                page_load_timeout=page_load_timeout,
            )
        return crawler, fake_driver, fake_client_config

    def test_client_timeout_aligned_to_page_load_timeout(self):
        _, fake_driver, fake_client_config = self._build_crawler(
            page_load_timeout=1000, ambient_client_timeout=120
        )
        # The client command timeout must be raised from the ambient 120s cap to the
        # configured page-load budget.
        self.assertEqual(fake_client_config.timeout, 1000)
        # The browser-side budgets are still configured as before (behaviour unchanged).
        fake_driver.set_page_load_timeout.assert_called_once_with(1000)
        fake_driver.set_script_timeout.assert_called_once_with(1000)

    def test_client_timeout_matches_custom_page_load_timeout(self):
        _, _, fake_client_config = self._build_crawler(
            page_load_timeout=300, ambient_client_timeout=120
        )
        self.assertEqual(fake_client_config.timeout, 300)


if __name__ == "__main__":
    unittest.main()
