def apply_configuration(keyValuePairDictionary):
    import gc
    import utils
    import device_info

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
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_esp_gen_1_config_templ.py')
    else:
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_py_gen_1_config_templ.py')
    contents += '\n'

    if board == "sdi12":
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_sdi12_config_templ.py')
        if not device_info.is_esp32():
            contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_ins_py_sdi_gen_1_config_templ.py')
    else:
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_i2c_analog_config_templ.py')
    contents += '\n'

    if board == "ins_esp_gen_1":
        contents += utils.readFromFile(rootFolder + 'apps/demo_console/templ/device_scale.py')

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

    file = rootFolder + 'apps/demo_console/demo_config.py'
    utils.writeToFile(file, contents)

    import utils
    utils.clearCachedStates()

    gc.collect()
