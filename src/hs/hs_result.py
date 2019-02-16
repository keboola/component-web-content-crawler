from kbc.result import *

# Pkeys
COMPANY_PK = ['companyId']
DEAL_PK = ['dealId']
DEAL_STAGE_HIST_PK = ['Deal_ID', 'sourceVid', 'sourceId', 'timestamp']


class DealsWriter(ResultWriter):

    def __init__(self, out_path, columns, buffer=8192):
        # specify result table
        deal_res_table = KBCTableDef('deals', columns, DEAL_PK)
        ResultWriter.__init__(self, out_path, deal_res_table, fix_headers=True, buffer_size=buffer)

        ext_user_table = KBCTableDef('deals_stage_history', [], DEAL_STAGE_HIST_PK)
        self.deals_stage_history_wr = ResultWriter(out_path, ext_user_table,
                                                   exclude_fields=['properties.dealstage.versions'],
                                                   flatten_objects=False,
                                                   user_value_cols={'Deal_ID'}, buffer_size=buffer)

    def write(self, data, file_name=None, user_values=None, object_from_arrays=False, write_header=True):
        # write ext users
        d_stage_history = data.get('properties').get('dealstage').get('versions')
        if d_stage_history and str(
                d_stage_history) != 'nan' and len(d_stage_history) > 0:
            self.deals_stage_history_wr.write_all(d_stage_history,
                                                  user_values={'Deal_ID': self._get_pkey_values(data, {})})
            self.results = {**self.results, **self.deals_stage_history_wr.results}

        super().write(data)
