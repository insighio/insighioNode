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
    module_utils.readFromFile.side_effect = ['{"user_test_tmp":"1"}', '{"device_test_tmp":"2"}']

    assert cfg.init() == True
    assert "device_test_tmp" in cfg.device_settings
    assert "user_test_tmp" in cfg.user_settings
    assert cfg.device_settings["device_test_tmp"] == "2"
    assert cfg.user_settings["user_test_tmp"] == "1"


def test_init_config():
    module_utils.existsFile = Mock()
    module_utils.existsFile.side_effect = [False, True]

    module_utils.readFromFile = Mock()
    module_utils.readFromFile.side_effect = ['{"user_test_tmp":"3"}', '{"device_test_tmp":"4"}']

    assert cfg.init() == True
    assert "device_test_tmp" in cfg.device_settings
    assert "user_test_tmp" in cfg.user_settings
    assert cfg.device_settings["device_test_tmp"] == "4"
    assert cfg.user_settings["user_test_tmp"] == "3"


def test_internal_has_obj_none():
    assert cfg._has(None, "key_one") == False


def test_internal_has_key_none():
    testObj = {"test": 1}
    assert cfg._has(testObj, None) == False


def test_internal_has_not_exist():
    testObj = {"test": 1}
    assert cfg._has(testObj, "key_one") == False


def test_internal_has_exist():
    testObj = {"test": 1}
    assert cfg._has(testObj, "test") == True


def test_internal_get_obj_none():
    assert cfg._get(None, "key_one") == None


def test_internal_get_key_none():
    testObj = {"test": 1}
    assert cfg._get(testObj, None) == None


def test_internal_get_not_exist():
    testObj = {"test": 1}
    assert cfg._get(testObj, "key_one") == None


def test_internal_get_exist():
    testObj = {"test": 1}
    assert cfg._get(testObj, "test") == 1
