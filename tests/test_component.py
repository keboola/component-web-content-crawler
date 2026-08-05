import os
import unittest

import mock
from freezegun import freeze_time
from keboola.component import UserException

from component import Component


class TestPerformCrawlerActionsMissingActions(unittest.TestCase):
    """Regression test for the unhandled TypeError: 'NoneType' object is not iterable.

    A configuration step written without an 'actions' key (or with an explicit null)
    made ``step.get("actions")`` return None, which the action loop then tried to
    iterate — crashing the job with an opaque internal error (exit 2) that named
    neither the problem nor the offending step. It must fail as a UserException
    (exit 1) instead, while every previously-working shape of 'actions' is untouched.
    """

    @staticmethod
    def _component():
        # Bypass __init__ so the test needs neither a config nor a real browser.
        return Component.__new__(Component)

    def test_missing_actions_raises_user_exception_naming_the_step(self):
        with self.assertRaises(UserException) as ctx:
            self._component()._perform_crawler_actions(None, "Click slide menu")
        message = str(ctx.exception)
        self.assertIn("actions", message)
        self.assertIn("Click slide menu", message)

    def test_missing_actions_without_description_still_raises_user_exception(self):
        with self.assertRaises(UserException):
            self._component()._perform_crawler_actions(None)

    def test_empty_actions_list_is_still_a_no_op(self):
        # Behaviour preservation: an empty list already iterated zero times and
        # returned False. It must NOT become an error.
        self.assertFalse(self._component()._perform_crawler_actions([]))

    def test_populated_actions_list_is_performed_unchanged(self):
        # Behaviour preservation: the happy path still builds and performs actions.
        comp = self._component()
        comp.web_crawler = mock.MagicMock()
        comp.web_crawler.perform_action.return_value = None
        actions = [{"action_name": "click", "action_parameters": {"element": "#a"}}]

        with mock.patch("component.CrawlerActionBuilder.build") as build:
            self.assertFalse(comp._perform_crawler_actions(actions, "Some step"))

        build.assert_called_once_with("click", element="#a")
        comp.web_crawler.perform_action.assert_called_once_with(build.return_value)


class TestComponent(unittest.TestCase):
    # set global time to 2010-10-10 - affects functions like datetime.now()
    @freeze_time("2010-10-10")
    # set KBC_DATADIR env to non-existing dir
    @mock.patch.dict(os.environ, {"KBC_DATADIR": "./non-existing-dir"})
    def test_run_no_cfg_fails(self):
        with self.assertRaises(ValueError):
            comp = Component()
            comp.run()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
