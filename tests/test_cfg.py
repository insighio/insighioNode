# import utils

import sys

################### Mocking


# Mock - logging
def mock_logging_info(line):
    print("[D]: {}".format(line))


def mock_logging_exception(e, line):
    print("[E]: {}".format(line))


def mock_logging_getLogger():
    pass


# module = type(sys)("logging")
# module.info = mock_logging_info
# module.exception = mock_logging_exception
# module.getLogger = mock_logging_getLogger
# sys.modules["logging"] = module

## Mock - json
import json

sys.modules["ujson"] = json

## Mock - utils
from unittest.mock import Mock

module_utils = type(sys)("utils")
module_utils.existsFile = Mock(return_value=False)
module_utils.readFromFile = Mock(return_value="")
sys.modules["utils"] = module_utils

################### Tests


from insighioNode.apps.demo_console import cfg


def test_init_missing_files():
    module_utils.existsFile = Mock()
    module_utils.existsFile.side_effect = [False, False]

    assert cfg.init() == False


def test_init_tmp_config():
    module_utils.existsFile = Mock()
    module_utils.existsFile.side_effect = [True]

    module_utils.readFromFile = Mock()
    module_utils.readFromFile.side_effect = ['{"user_test_tmp":"1"}', '{"device_test_tmp":"1"}']

    assert cfg.init() == True


def test_init_config():
    module_utils.existsFile = Mock()
    module_utils.existsFile.side_effect = [False, True]

    module_utils.readFromFile = Mock()
    module_utils.readFromFile.side_effect = ['{"user_test_tmp":"2"}', '{"device_test_tmp":"2"}']

    assert cfg.init() == True
