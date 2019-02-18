import abc
import random
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class CrawlerAction:
    @abc.abstractmethod
    def execute(self, driver: webdriver, **extra_args):
        pass

    # element actions


class ClickElement(CrawlerAction):
    def __init__(self, xpath: str):
        self.xpath = xpath

    def execute(self, driver: webdriver, **extra_args):
        driver.find_element_by_xpath(self.xpath).click()


class GenericElementAction(CrawlerAction):
    def __init__(self, method_name, xpath: str, **kwargs):
        self.xpath = xpath
        self.method_name = method_name
        self.method_args = kwargs

    def execute(self, driver: webdriver, **extra_args):
        positional_args = self.method_args.pop('positional_arguments', [])
        element = driver.find_element_by_xpath(self.xpath)
        method = getattr(element, self.method_name)
        return method(*positional_args, **self.method_args)


class WaitForElement(CrawlerAction):
    def __init__(self, xpath: str, delay=10):
        self.xpath = xpath
        self.delay = delay

    def execute(self, driver: webdriver, **extra_args):
        wait = WebDriverWait(driver, self.delay)
        el = wait.until(ec.visibility_of_element_located((By.XPATH, self.xpath)))
        return el


# System actions

class GenericBrowserAction(CrawlerAction):
    def __init__(self, method_name, **kwargs):
        self.method_name = method_name
        self.method_args = kwargs

    def execute(self, driver: webdriver, **extra_args):
        positional_args = self.method_args.pop('positional_arguments', [])
        method = getattr(driver, self.method_name)
        return method(*positional_args, **self.method_args)


class SwitchToPopup(CrawlerAction):
    def execute(self, driver: webdriver, **extra_args):
        main_handle = extra_args.pop('main_handle')
        new_window_handle = None
        while not new_window_handle:
            for handle in driver.window_handles:
                if handle != main_handle:
                    new_window_handle = handle
                    break
        driver.switch_to.window(new_window_handle)


class SwitchToMainWindow(CrawlerAction):
    def execute(self, driver: webdriver, **extra_args):
        main_handle = extra_args.pop('main_handle')
        driver.switch_to.window(main_handle)


class CrawlerActionBuilder:
    @staticmethod
    def build(action_name, **parameters):
        # TODO: validate parameters based on type
        supported_actions = CrawlerActionBuilder.get_supported_actions()
        if action_name not in list(supported_actions.keys()):
            raise ValueError('{} is not supported action, '
                             'suported values are: [{}]'.format(action_name,
                                                                CrawlerAction.__subclasses__()))

        return supported_actions[action_name](**parameters)

    @staticmethod
    def get_supported_actions():
        supported_actions = {}
        for c in CrawlerAction.__subclasses__():
            supported_actions[c.__name__] = c
        return supported_actions


class GenericCrawler:

    def __init__(self, start_url, download_folder, random_wait_range=None, proxy=None, driver_type='Chrome',
                 options=None):
        self.start_url = start_url
        self.random_wait_range = random_wait_range
        self.download_folder = download_folder

        self._driver = self._get_driver(driver_type, download_folder, options)
        self._main_window_handle = None
        while not self._main_window_handle:
            self._main_window_handle = self._driver.current_window_handle

    def start(self):
        # TODO: validate URL
        self._driver.get(self.start_url)

    def stop(self):
        self._driver.quit()

    def perform_action(self, action: CrawlerAction):
        res = action.execute(self._driver, main_handle=self._main_window_handle)

        self._wait_random(self.random_wait_range)
        return res

    def _get_driver(self, driver_type, download_folder, options):
        if driver_type == 'Chrome':
            options = webdriver.ChromeOptions()
            options.set_capability('download.default_directory', download_folder)
            # setting for running in docker
            # TODO: remove hardcoding
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1420,1080')
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            driver = webdriver.Chrome(options=options)
            driver.fullscreen_window()
        else:
            raise ValueError('{} web driver is not supported!'.format(driver_type))
        return driver

    def _wait_random(self, range):
        if range:
            wait_int = random.randint(range[0], range[1])
            time.sleep(wait_int)
        else:
            return
