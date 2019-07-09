'''
Template Component main class.

'''

import argparse
import json
import logging
import os

from kbc.env_handler import KBCEnvHandler
from nested_lookup import nested_lookup

from webcrawler.selenium_crawler import BreakBlockExecution
from webcrawler.selenium_crawler import CrawlerActionBuilder
from webcrawler.selenium_crawler import GenericCrawler

# configuration variables
KEY_RESOLUTION = 'resolution'
KEY_MAX_WINDOW = 'maximize_window'
KEY_RANDOM_WAIT = 'random_wait_range'
KEY_USER_PARS = 'user_parameters'
KEY_DRIVER_OPTIONS = 'driver_options'
KEY_START_URL = 'start_url'
KEY_STORE_COOKIES = 'store_cookies'
KEY_DOCKER_MODE = 'docker_mode'

KEY_STEPS = 'steps'
KEY_DESCRIPTION = 'description'
KEY_ACTIONS = 'actions'
KEY_ACTION_PARAMETERS = 'action_parameters'
KEY_ACTION_NAME = 'action_name'

MANDATORY_PARS = [KEY_STEPS, KEY_START_URL]
MANDATORY_IMAGE_PARS = []

APP_VERSION = '0.0.1'


class Component(KBCEnvHandler):

    def __init__(self, debug=False, data_path=None):
        KBCEnvHandler.__init__(self, MANDATORY_PARS, data_path=data_path)
        # override debug from config
        if self.cfg_params.get('debug'):
            debug = True

        self.set_default_logger('DEBUG' if debug else 'INFO')
        logging.info('Running version %s', APP_VERSION)
        logging.info('Loading configuration...')

        try:
            self.validate_config()
            self.validate_image_parameters(MANDATORY_IMAGE_PARS)
        except ValueError as e:
            logging.error(e)
            exit(1)

        logging.info("Setting up crawler..")
        # intialize instance parameters
        random_wait = self.cfg_params.get(KEY_RANDOM_WAIT, None)
        options = self.cfg_params.get(KEY_DRIVER_OPTIONS)
        out_files = os.path.join(self.data_path, 'files')
        self.web_crawler = GenericCrawler(self.cfg_params[KEY_START_URL], self.tables_out_path, out_files,
                                          random_wait_range=random_wait, options=options,
                                          docker_mode=self.cfg_params.get(KEY_DOCKER_MODE, True),
                                          resolution=self.cfg_params.get(KEY_RESOLUTION))

    def run(self, debug=False):
        """
        Main execution code
        """
        crawler_steps = self.cfg_params[KEY_STEPS]

        crawler_steps = self._fill_in_user_parameters(crawler_steps, self.cfg_params.get(KEY_USER_PARS))

        logging.info("Entering first step URL %s", self.web_crawler.start_url)
        self.web_crawler.start()
        if self.cfg_params.get(KEY_MAX_WINDOW):
            self.web_crawler.maximize_window()

        # set cookies, needs to be done after the domain load
        if self.cfg_params.get(KEY_STORE_COOKIES):
            logging.info('Loading cookies from last run.')
            last_state = self.get_state_file()
            self.web_crawler.load_cookies(last_state.get('cookies'))

        for st in crawler_steps:
            logging.info(st.get(KEY_DESCRIPTION, ''))
            self._perform_crawler_actions(st.get(KEY_ACTIONS))

        if self.cfg_params.get(KEY_STORE_COOKIES):
            logging.info('Storing cookies for next run.')
            cookies = self.web_crawler.get_cookies()
            state = {'cookies': cookies}
            self.write_state_file(state)

        self.web_crawler.stop()
        logging.info("Extraction finished")

    def _perform_crawler_actions(self, actions):
        for a in actions:
            # KBC bug, empty object as array
            action_params = a.get(KEY_ACTION_PARAMETERS, {})
            if isinstance(action_params, list) and len(action_params) == 0:
                action_params = {}

            logging.info(a.get(KEY_DESCRIPTION, ''))
            action = CrawlerActionBuilder.build(a[KEY_ACTION_NAME], **action_params)

            res = self.web_crawler.perform_action(action)

            # check if is break action
            if isinstance(res, BreakBlockExecution):
                break

    def _fill_in_user_parameters(self, crawler_steps, user_param):
        # convert to string minified
        steps_string = json.dumps(crawler_steps, separators=(',', ':'))
        # dirty and ugly replace
        for key in user_param:
            lookup_str = '{"attr":"' + key + '"}'
            steps_string = steps_string.replace(lookup_str, '"' + str(user_param[key]) + '"')
        new_steps = json.loads(steps_string)
        non_matched = nested_lookup('attr', new_steps)

        if non_matched:
            raise ValueError(
                'Some user attributes [{}] specified in configuration '
                'are not present in "user_parameters" field.'.format(non_matched))
        return new_steps


"""
    Main entrypoint
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--data', help='Data folder path')
    parser.add_argument('--debug', help='Debug mode')

    args = parser.parse_args()
    if args.debug:
        debug = True
    else:
        debug = False

    comp = Component(debug=debug, data_path=args.data)
    comp.run()
