def apply_configuration(keyValuePairDictionary):
    import gc
    import utils
    import device_info
    import ure

    gc.collect()

    operation = ""
    board = device_info.get_hw_module_verison()
    shield = ""
    for param in keyValuePairDictionary:
        if param == "network":
            operation = keyValuePairDictionary[param]
        elif param == "selected-shield":
            shield = keyValuePairDictionary[param]

    rootFolder = device_info.get_device_root_folder()

    contents = utils.readFromFile(rootFolder + 'apps/demo_console/templ/common_templ.py')

    # set project configuration content
    if board == device_info._CONST_ESP32 or board == device_info._CONST_ESP32_WROOM:
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp32_templ.py')
    elif board == device_info._CONST_ESP32S3:
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp32s3_templ.py')
    else:
        print("[ERROR]: device not supported: {}".format(board))

    contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_i2c_analog_config_templ.py')
    if shield == "advind":
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_advind_templ.py')
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_sdi12_config_templ.py')
    elif shield == "dig_analog":
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_i2c_dig_analog_templ.py')
    elif shield == "scale":
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_scale.py')
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_scale_config.py')

    contents += '\n'

    if operation == 'wifi':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/wifi_config_templ.py')
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/protocol_config_templ.py')
    elif operation == 'cellular':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/cellular_config_templ.py')
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/protocol_config_templ.py')
    elif operation == 'lora':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_lora_templ.py')
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/lora_config_templ.py')
    elif operation == 'satellite':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/satellite_config_templ.py')

    for param in keyValuePairDictionary:
        contents = contents.replace('<' + param + '>', keyValuePairDictionary[param])

    # replace all unused variables with None values
    contents = ure.sub(r'\"?<[a-z\-0-9]+>\"?', 'None', contents)

    file = rootFolder + 'apps/demo_console/demo_config.py'

    # backup old Configuration
    utils.copyFile(file, file + ".prev")

    # create new
    utils.writeToFile(file, contents)

    import utils
    utils.clearCachedStates()

    gc.collect()
