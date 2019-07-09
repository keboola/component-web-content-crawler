import abc
import base64
import logging
import os
import random

import pyscreenshot as ImageGrab
import requests
import time
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class CrawlerAction:
    KEY_ACTION_PARAMETERS = 'action_parameters'
    KEY_ACTION_NAME = 'action_name'

    @abc.abstractmethod
    def execute(self, driver: webdriver, **extra_args):
        pass

    # element actions


class ClickElementToDownload(CrawlerAction):
    def __init__(self, xpath: str, delay=30, timeout=60, result_file_name=None):
        """

        :param xpath: XPATH defining the target element
        :param delay: Wait time in seconds before the action is executed.
        :param timeout: Time in seconds that define the maximum time the action waits for the download.
        :param result_file_name:
        """
        self.xpath = xpath
        self.delay = delay
        self.timeout = timeout
        self.result_file_name = result_file_name

    def execute(self, driver: webdriver, **extra_args):
        download_folder = extra_args.pop('download_folder')
        exisitng_files = [f for f in os.listdir(download_folder) if os.path.isfile(os.path.join(download_folder, f))]
        driver.find_element_by_xpath(self.xpath).click()
        time.sleep(self.delay)
        self._wait_until_new_file(exisitng_files, self.timeout, download_folder)

    def _wait_until_new_file(self, original_files, timeout, download_folder):
        # wait until new file is present
        new_files = None
        start_time = time.time()
        is_timedout = False
        while not new_files and not is_timedout:
            existng_files = [f for f in os.listdir(download_folder)
                             if os.path.isfile(os.path.join(download_folder, f))]
            new_files = [f for f in existng_files if f not in original_files]
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                is_timedout = True

        if is_timedout:
            raise TimeoutError('File download timed out! Try to raise the timeout interval.')
        return new_files


class GenericShadowDomElementAction(CrawlerAction):
    CSS_SHADOW_HOST = '#shadow-root'

    def __init__(self, method_name, xpath: str, shadow_parent_element, **kwargs):
        self.xpath = xpath
        self.method_name = method_name
        self.method_args = kwargs
        self.shadow_parent_element = shadow_parent_element

    def execute(self, driver: webdriver, **extra_args):
        positional_args = self.method_args.pop('positional_arguments', [])
        element = self.find_shadow_dom_element(self.xpath, driver, self.shadow_parent_element)
        method = getattr(element, self.method_name)
        return method(*positional_args, **self.method_args)

    def find_shadow_dom_element(self, xpath, driver, root_element_tag):
        shadow_root = self.get_ext_shadow_root(driver, driver.find_element_by_tag_name(root_element_tag))
        element = shadow_root.find_element_by_xpath(xpath)
        return element

    def get_ext_shadow_root(self, driver, element):
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root


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
        """

        :param xpath:
        :param delay: Timeout of the action in case the element is never available
        """
        self.xpath = xpath
        self.delay = delay

    def execute(self, driver: webdriver, **extra_args):
        wait = WebDriverWait(driver, self.delay)
        el = wait.until(ec.visibility_of_element_located((By.XPATH, self.xpath)))
        return el


class BreakBlockExecution(CrawlerAction):
    """
    Returns self to notify executor that it should break the current branch and switch to another.
    """

    def execute(self, driver: webdriver, **extra_args):
        return self


class PrintHtmlPage(CrawlerAction):
    def __init__(self, log_level=None):
        """

        :type log_level: int
        """
        self.log_level = log_level

    def execute(self, driver: webdriver, **extra_args):
        html = driver.page_source
        if self.log_level:
            logging.log(self.log_level, html)


class ConditionalAction(CrawlerAction):
    def __init__(self, test_action, result_action=None, fail_action=None):
        """


        :param test_action: Testing action, if the action passes the result_action will be executed.
        :type test_action: CrawlerAction
        :param result_action: The action executed if the entry action passes
        :type result_action: CrawlerAction
        :param fail_action: The action executed if the entry action fails.
        If not specified, excution continues on failure.
        :type result_action: CrawlerAction
        """
        self.test_action = test_action
        self.result_action = result_action
        self.fail_action = fail_action

    def execute(self, driver: webdriver, **extra_args):
        logging.info('Executing test action %s', type(self.test_action).__name__)
        try:
            self.test_action.execute(driver, **extra_args)
        except WebDriverException as e:
            logging.debug('The testing action %s with params [%s]  failed with error: %s',
                          type(self.test_action).__name__,
                          self.test_action.__dict__, str(e))

            logging.info('The testing action %s failed with error: %s',
                         type(self.test_action).__name__, str(e))
            if self.fail_action:
                logging.info('Executing action (%s) defined on failure.', type(self.fail_action).__name__)
                return self.fail_action.execute(driver, **extra_args)
            else:
                logging.info('Continue execution..')
                return

        # test passed
        if self.result_action:
            logging.info('Test action passed, executing result_action %s', type(self.result_action).__name__)
            return self.result_action.execute(driver, **extra_args)
        else:
            logging.info('No result action specified, continuing..')


# System actions

class GenericDriverAction(CrawlerAction):
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


class Wait(CrawlerAction):
    """
    Pauses execution for specified amount of time (s).
    """

    def __init__(self, seconds):
        """

        :param seconds: Seconds to wait
        """
        self.seconds = seconds

    def execute(self, driver: webdriver, **extra_args):
        time.sleep(self.seconds)


class TakeScreenshot(CrawlerAction):
    """
    Pauses execution for specified amount of time (s).
    """

    def __init__(self, name, folder='screens', imgbb_token=None):
        """

        :param seconds: Seconds to wait
        """
        self.folder = folder
        self.name = name
        self.imgbb_token = imgbb_token

    def execute(self, driver: webdriver, **extra_args):
        folder_path = os.path.join(extra_args.pop('data_folder'), self.folder)
        runid_prefix = extra_args.get('runid', '')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        im = ImageGrab.grab()
        # save image file
        img_path = os.path.join(folder_path, self.name + '.png')
        im.save(img_path)
        if self.imgbb_token:
            self._store_in_imgbb(img_path, self.imgbb_token, str(runid_prefix) + '_' + self.name)

    def _store_in_imgbb(self, img_path, token, name):
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        values = {
            "image": encoded_string
        }

        params = {
            'key': token,
            "name": name
        }
        response = requests.post('https://api.imgbb.com/1/upload', data=values,
                                 params=params)

        if response.status_code > 299:
            raise RuntimeError(F'Failed to store image {name} in the ImgBB repository')


class CrawlerActionBuilder:

    @staticmethod
    def build(action_name, **parameters):
        # TODO: validate parameters based on type
        supported_actions = CrawlerActionBuilder.get_supported_actions()
        if action_name not in list(supported_actions.keys()):
            raise ValueError('{} is not supported action, '
                             'suported values are: [{}]'.format(action_name,
                                                                CrawlerAction.__subclasses__()))

        # special case of conditional action
        if action_name == 'ConditionalAction':
            cond_action = supported_actions[action_name](**parameters)
            return CrawlerActionBuilder._build_conditional_action(cond_action)
        else:
            return supported_actions[action_name](**parameters)

    @staticmethod
    def get_supported_actions():
        supported_actions = {}
        for c in CrawlerAction.__subclasses__():
            supported_actions[c.__name__] = c
        return supported_actions

    @staticmethod
    def _build_conditional_action(cond_action: ConditionalAction):
        test_action_def = cond_action.test_action
        action_pars = test_action_def.get(CrawlerAction.KEY_ACTION_PARAMETERS, {})
        cond_action.test_action = CrawlerActionBuilder.build(test_action_def[CrawlerAction.KEY_ACTION_NAME],
                                                             **action_pars)

        if cond_action.result_action:
            action_def = cond_action.result_action
            action_pars = action_def.get(CrawlerAction.KEY_ACTION_PARAMETERS, {})
            cond_action.result_action = CrawlerActionBuilder.build(action_def[CrawlerAction.KEY_ACTION_NAME],
                                                                   **action_pars)

        if cond_action.fail_action:
            action_def = cond_action.fail_action
            action_pars = action_def.get(CrawlerAction.KEY_ACTION_PARAMETERS, {})
            cond_action.fail_action = CrawlerActionBuilder.build(action_def[CrawlerAction.KEY_ACTION_NAME],
                                                                 **action_pars)
        return cond_action


class GenericCrawler:

    def __init__(self, start_url, download_folder, data_folder, runid='', docker_mode=True, random_wait_range=None,
                 resolution='1920x1080',
                 proxy=None,
                 driver_type='Chrome',
                 options=None):

        if resolution is None:
            resolution = '1920x1080'

        res_sizes = resolution.split('x')
        if len(res_sizes) != 2:
            raise ValueError("Resolution is in invalid format, you must provide it as WIDTHxEIGHT. e.g. 1024x980")
        if docker_mode:
            self._display = Display(visible=0, size=(res_sizes[0], res_sizes[1]))
            self._display.start()
        self.start_url = start_url
        self.random_wait_range = random_wait_range
        self.download_folder = download_folder
        self.data_folder = data_folder
        self.runid = runid
        self._docker_mode = docker_mode

        self._driver = self._get_driver(driver_type, download_folder, options, docker_mode)
        self._main_window_handle = None
        while not self._main_window_handle:
            self._main_window_handle = self._driver.current_window_handle

    def start(self):
        # TODO: validate URL
        self._driver.get(self.start_url)

    def get_cookies(self):
        return self._driver.get_cookies()

    def load_cookies(self, cookies):
        if not cookies:
            return
        for cookie in cookies:
            self._driver.add_cookie(cookie)

    def stop(self):
        self._driver.quit()
        if self._docker_mode:
            self._display.stop()

    def maximize_window(self):
        self._driver.maximize_window()

    def perform_action(self, action: CrawlerAction):
        res = action.execute(self._driver, download_folder=self.download_folder, data_folder=self.data_folder,
                             runid=self.runid, main_handle=self._main_window_handle)

        self._wait_random(self.random_wait_range)
        return res

    def _get_driver(self, driver_type, download_folder, options, docker_mode):
        if driver_type == 'Chrome':
            options = webdriver.ChromeOptions()
            prefs = {'download.default_directory': download_folder,
                     "download.prompt_for_download": False,
                     "safebrowsing.enabled": False
                     }
            options.add_experimental_option('prefs', prefs)
            # setting for running in docker
            # TODO: remove hardcoding
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-features=VizDisplayCompositor')
            # start maximized does not work when in docker mode
            driver = webdriver.Chrome(options=options)
            # self.enable_download_in_headless_chrome()
        else:
            raise ValueError('{} web driver is not supported!'.format(driver_type))
        return driver

    def _wait_random(self, _range):
        if _range:
            wait_int = random.randint(_range[0], _range[1])
            time.sleep(wait_int)
        else:
            return
