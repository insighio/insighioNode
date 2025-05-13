import scenario_pcnt_ulp_dynamic_strings
import scenario_pcnt_ulp_static_strings


def test_pcnt_assembly_generation():
    # Test case 1: Both PCNTs enabled
    pcnt_1_enabled = True
    pcnt_1_gpio = 4
    pcnt_1_high_freq = False
    pcnt_2_enabled = True
    pcnt_2_gpio = 5
    pcnt_2_high_freq = False

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_enabled_low_frequency_gpio_4_pcnt_2_enabled_low_frequency_gpio_5()
    # print("========== Expected Assembly ==========")
    # print(expected)
    # print("========== Generated Assembly ==========")
    # print(res)

    # assert res == expected

    # Test case 2: Only PCNT 1 enabled
    pcnt_1_enabled = True
    pcnt_1_gpio = 4
    pcnt_1_high_freq = False
    pcnt_2_enabled = False
    pcnt_2_gpio = 5
    pcnt_2_high_freq = False

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_enabled_low_frequency_gpio_4_pcnt_2_disabled()
    # print("========== Expected Assembly ==========")
    # print(expected)
    # print("========== Generated Assembly ==========")
    # print(res)

    # assert res == expected

    # Test case 3: Only PCNT 2 enabled
    pcnt_1_enabled = False
    pcnt_1_gpio = 4
    pcnt_1_high_freq = False
    pcnt_2_enabled = True
    pcnt_2_gpio = 5
    pcnt_2_high_freq = False

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_disabled_pcnt_2_enabled_low_frequency_gpio_5()
    # print("========== Expected Assembly ==========")
    # print(expected)
    # print("========== Generated Assembly ==========")
    # print(res)

    # assert res == expected

    pcnt_1_enabled = True
    pcnt_1_gpio = 4
    pcnt_1_high_freq = True
    pcnt_2_enabled = False
    pcnt_2_gpio = 5
    pcnt_2_high_freq = False

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_enabled_high_frequency_gpio_4_pcnt_2_disabled()
    # print("========== Expected Assembly ==========")
    # print(expected)
    # print("========== Generated Assembly ==========")
    # print(res)

    # assert res == expected

    pcnt_1_enabled = False
    pcnt_1_gpio = 4
    pcnt_1_high_freq = False
    pcnt_2_enabled = True
    pcnt_2_gpio = 5
    pcnt_2_high_freq = True

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_disabled_pcnt_2_enabled_high_frequency_gpio_5()

    # print("========== Expected Assembly ==========")
    # print(expected)
    # print("========== Generated Assembly ==========")
    # print(res)

    # assert res == expected

    pcnt_1_enabled = True
    pcnt_1_gpio = 4
    pcnt_1_high_freq = True
    pcnt_2_enabled = True
    pcnt_2_gpio = 5
    pcnt_2_high_freq = True

    res = scenario_pcnt_ulp_dynamic_strings.generate_assembly(
        pcnt_1_enabled, pcnt_1_gpio, pcnt_1_high_freq, pcnt_2_enabled, pcnt_2_gpio, pcnt_2_high_freq
    )
    expected = scenario_pcnt_ulp_static_strings.get_assembly_pcnt_1_enabled_high_frequency_gpio_4_pcnt_2_enabled_high_frequency_gpio_5()

    print("========== Expected Assembly ==========")
    print(expected)
    print("========== Generated Assembly ==========")
    print(res)

    assert res == expected


test_pcnt_assembly_generation()
