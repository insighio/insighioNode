def apply_configuration(keyValuePairDictionary):
    import gc
    import utils
    import device_info
    import ure

    gc.collect()

    operation = ""
    board = ""
    for param in keyValuePairDictionary:
        if param == "network":
            operation = keyValuePairDictionary[param]
        elif param == "selected-board":
            board = keyValuePairDictionary[param]

    rootFolder = device_info.get_device_root_folder()

    contents = utils.readFromFile(rootFolder + 'apps/demo_console/templ/common_templ.py')

    # set project configuration content
    if device_info.is_esp32():
        if board == "ins_esp_gen_1":
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp_gen_1_config_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_i2c_analog_config_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_scale.py')
        elif board == "ins_esp_gen_s1":
            if device_info.get_hw_module_verison() == "esp32s3":
                contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp_gen_s2_s3_config_templ.py')
            else:
                contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp_gen_s1_config_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_i2c_dig_analog_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_i2c_analog_config_templ.py')
        elif board == "ins_esp_gen_sdi12":
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp_gen_s1_config_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/shield_sdi12_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_sdi12_config_templ.py')
    else:
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_py_gen_1_config_templ.py')
        if board == "sdi12":
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_sdi12_config_templ.py')
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/py_sdi12_config_templ.py')
        else:
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_i2c_analog_config_templ.py')
        contents += '\n'
    contents += '\n'

    if operation == 'wifi':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/wifi_config_templ.py')
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/protocol_config_templ.py')
    elif operation == 'cellular':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/cellular_config_templ.py')
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/protocol_config_templ.py')
    elif operation == 'lora':
        contents += '\n' + utils.readFromFile(rootFolder + 'apps/demo_console/templ/lora_config_templ.py')

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
