'''
Template Component main class.

'''

import logging
from datetime import datetime

from kbc.env_handler import KBCEnvHandler
from kbc.result import *

from hs import hs_client, hs_result
from hs.hs_result import DealsWriter
from hs.hs_client import HubspotClient

# global constants
SUPPORTED_ENDPOINTS = ['companies', 'deals']

# configuration variables
KEY_API_TOKEN = '#api_token'
KEY_PERIOD_FROM = 'period_from'
KEY_ENDPOINTS = 'endpoints'

KEY_COMPANY_PROPERTIES = 'company_properties'
KEY_DEAL_PROPERTIES = 'deal_properties'

MANDATORY_PARS = [KEY_ENDPOINTS, KEY_API_TOKEN]
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

        # intialize instance parameteres
        token = self.cfg_params[KEY_API_TOKEN]
        self.hs_client = HubspotClient(token)

    def run(self, debug=False):
        '''
        Main execution code
        '''
        params = self.cfg_params  # noqa

        if params.get(KEY_PERIOD_FROM):
            start_date, end_date = self.get_date_period_converted(params.get(KEY_PERIOD_FROM),
                                                                  datetime.utcnow().strftime('%Y-%m-%d'))
            recent = True
        else:
            start_date = None
            recent = False

        endpoints = params.get(KEY_ENDPOINTS, SUPPORTED_ENDPOINTS)

        if 'companies' in endpoints:
            logging.info('Extracting Companies')
            self.extract_companies(recent)

        if 'deals' in endpoints:
            logging.info("Extracting deals")
            self.extract_deals(start_date)

        logging.info("Extraction finished")

    def extract_deals(self, start_time):
        logging.info('Extracting Companies from HubSpot CRM')
        fields = self._parse_props(self.cfg_params.get(KEY_DEAL_PROPERTIES))

        if not fields:
            expected_deal_cols = hs_client.DEAL_DEFAULT_COLS + self._build_property_cols(
                hs_client.DEAL_DEFAULT_PROPERTIES)
        else:
            expected_deal_cols = hs_client.DEAL_DEFAULT_COLS + self._build_property_cols(fields)

        deal_writer = DealsWriter(self.tables_out_path, expected_deal_cols)

        self._get_n_process_results(self.hs_client.get_deals, deal_writer, start_time, fields)

    def extract_companies(self, recent):
        fields = self._parse_props(self.cfg_params.get(KEY_COMPANY_PROPERTIES))
        if not fields:
            expected_company_cols = hs_client.COMPANIES_DEFAULT_COLS + self._build_property_cols(
                hs_client.COMPANY_DEFAULT_PROPERTIES)
        else:
            expected_company_cols = hs_client.COMPANIES_DEFAULT_COLS + self._build_property_cols(fields)
        # table def
        companies_table = KBCTableDef(name='companies', columns=expected_company_cols, pk=hs_result.COMPANY_PK)
        # writer setup
        comp_writer = ResultWriter(result_dir_path=self.tables_out_path, table_def=companies_table, fix_headers=True)
        self._get_n_process_results(self.hs_client.get_companies, comp_writer, recent, fields)

    def _parse_props(self, param):
        """
        Helper method to prepare dataset parameters query.

        :param param:
        :return:
        """
        cols = []
        if param:
            cols = [p.strip() for p in param.split(",")]
        return cols

    def _get_n_process_results(self, ds_getter, writer, *fpars):
        """
               Generic method to get simple objects
               :param res_file_path:
               :param fs_getter:
               :return:
               """
        with writer:
            for res in ds_getter(*fpars):
                if isinstance(res, list):
                    writer.write_all(res)
                else:
                    writer.write(res)

        # store manifest
        logging.info("Storing manifest files.")
        self.create_manifests(writer.collect_results())

    def _build_property_cols(self, properties):
        # get flattened property cols
        prop_cols = []
        for p in properties:
            prop_cols.append('properties.' + p + '.source')
            prop_cols.append('properties.' + p + '.sourceId')
            prop_cols.append('properties.' + p + '.timestamp')
            prop_cols.append('properties.' + p + '.value')
            prop_cols.append('properties.' + p + '.versions')
        return prop_cols


"""
        Main entrypoint
"""
if __name__ == "__main__":
    comp = Component()
    comp.run()
