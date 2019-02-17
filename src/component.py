'''
Template Component main class.

'''

import logging

from kbc.env_handler import KBCEnvHandler

from webcrawler.selenium_crawler import *

# configuration variables
KEY_RANDOM_WAIT = 'random_wait_range'
KEY_USER_PARS = 'user_parameters'
KEY_DRIVER_OPTIONS = 'driver_options'
KEY_START_URL = 'start_url'

KEY_STEPS = 'steps'
KEY_DESCRIPTION = 'description'
KEY_ACTIONS = 'actions'
KEY_ACTION_PARAMETERS = 'action_parameters'
KEY_ACTION_NAME = 'action_name'

MANDATORY_PARS = [KEY_STEPS, KEY_START_URL]
MANDATORY_IMAGE_PARS = []

APP_VERSION = '0.0.1'


class Component(KBCEnvHandler):

    def __init__(self, debug=False):
        KBCEnvHandler.__init__(self, MANDATORY_PARS)
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
        self.web_crawler = GenericCrawler(self.cfg_params[KEY_START_URL], self.tables_out_path,
                                          random_wait_range=random_wait, options=options)

    def run(self, debug=False):
        """
        Main execution code
        """
        crawler_steps = self.cfg_params[KEY_STEPS]
        logging.info("Entering first step url %s", self.web_crawler.start_url)
        self.web_crawler.start()

        for st in crawler_steps:
            logging.info(st.get(KEY_DESCRIPTION, ''))
            self._perform_crawler_actions(st.get(KEY_ACTIONS))

        logging.info("Extraction finished")

    def _perform_crawler_actions(self, actions):
        for a in actions:
            logging.info(a.get(KEY_DESCRIPTION, ''))
            action = CrawlerActionBuilder.build(a[KEY_ACTION_NAME], **a.get(KEY_ACTION_PARAMETERS))
            self.web_crawler.perform_action(action)


"""
    Main entrypoint
"""

if __name__ == "__main__":
    comp = Component()
    comp.run()
