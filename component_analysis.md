# ESPHome Component Analysis

Total components: 688

## Core-owned Components (52)

| Component | Dependencies | Structures | Platforms |
|-----------|--------------|------------|----------|
| adc | - | sensor | - |
| api | network | component | - |
| async_tcp | network | component | - |
| binary_sensor | - | component | - |
| bme280_base | - | component | - |
| button | - | component | - |
| captive_portal | wifi | component | - |
| climate | - | component | - |
| const | - | component | - |
| cover | - | component | - |
| dashboard_import | api | component | - |
| debug | logger | text_sensor, sensor | - |
| epaper_spi | - | display | models |
| esp32 | - | component | - |
| esp8266 | - | component | - |
| font | - | component | - |
| globals | - | component | - |
| gpio | - | component | switch, binary_sensor... |
| homeassistant | - | component | switch, time... |
| host | - | component | time |
| i2c | - | component | - |
| improv_base | - | component | - |
| improv_serial | logger, wifi | component | - |
| interval | - | component | - |
| json | - | component | - |
| light | - | component | - |
| lock | - | component | - |
| logger | - | component | select |
| md5 | - | component | - |
| mdns | network | component | - |
| network | - | component | - |
| number | - | component | - |
| ota | - | component | - |
| output | - | component | switch, button... |
| power_supply | - | component | - |
| preferences | - | component | - |
| psram | PLATFORM_ESP32 | component | - |
| restart | - | component | switch, button |
| script | - | component | - |
| select | - | component | - |
| sensor | - | component | - |
| sha256 | - | component | - |
| shutdown | - | component | switch, button |
| socket | - | component | - |
| spi | - | component | - |
| substitutions | - | component | - |
| switch | - | component | binary_sensor |
| time | - | component | - |
| uart | - | component | event, switch... |
| valve | - | component | - |
| version | - | text_sensor | - |
| web_server_base | network | component | - |

## All Components

| Component | Core | Dependencies | Structures | Codeowners |
|-----------|------|--------------|------------|------------|
| a01nyub |  | - | sensor | @MrSuicideParrot |
| a02yyuw |  | - | sensor | @TH-Braemer |
| a4988 |  | - | component | - |
| absolute_humidity |  | - | sensor | @DAVe3283 |
| ac_dimmer |  | - | output | - |
| adalight |  | uart | component | - |
| adc | ✓ | - | sensor | @esphome/core |
| adc128s102 |  | spi | component | @DeerMaximum |
| addressable_light |  | - | display | - |
| ade7880 |  | - | sensor | @kpfleming |
| ade7953 |  | - | sensor | @angelnu |
| ade7953_base |  | - | component | @angelnu |
| ade7953_i2c |  | - | sensor | @angelnu |
| ade7953_spi |  | - | sensor | @angelnu |
| ads1115 |  | i2c | component | - |
| ads1118 |  | spi | component | @solomondg1 |
| ags10 |  | - | sensor | @mak-42 |
| aht10 |  | - | sensor | - |
| aic3204 |  | - | component | - |
| airthings_ble |  | esp32_ble_tracker | component | @jeromelaban |
| airthings_wave_base |  | ble_client | component | @ncareau |
| airthings_wave_mini |  | - | sensor | @ncareau |
| airthings_wave_plus |  | - | sensor | @jeromelaban |
| alarm_control_panel |  | - | component | @grahambrown11 |
| alpha3 |  | - | sensor | @jan-hofmeier |
| am2315c |  | - | sensor | @swoboda1337 |
| am2320 |  | - | sensor | - |
| am43 |  | - | component | @buxtronix |
| analog_threshold |  | - | binary_sensor | @ianchi |
| animation |  | display | component | @syndlex |
| anova |  | - | climate | - |
| apds9306 |  | - | sensor | @aodrenah |
| apds9960 |  | i2c | sensor, binary_sensor | - |
| api | ✓ | network | component | @esphome/core |
| aqi |  | - | sensor | @jasstrong |
| as3935 |  | - | sensor, binary_sensor | - |
| as3935_i2c |  | i2c | component | - |
| as3935_spi |  | spi | component | - |
| as5600 |  | i2c | component | @ammmze |
| as7341 |  | - | sensor | - |
| async_tcp | ✓ | network | component | @esphome/core |
| at581x |  | i2c | component | @X-Ryl669 |
| atc_mithermometer |  | - | sensor | - |
| atm90e26 |  | - | sensor | @danieltwagner |
| atm90e32 |  | - | sensor | @circuitsetup |
| audio |  | - | component | @kahrendt |
| audio_adc |  | - | component | @kbx81 |
| audio_dac |  | - | component | @kbx81 |
| axs15231 |  | i2c | component | @clydebarrow |
| b_parasite |  | - | sensor | - |
| ballu |  | - | climate | - |
| bang_bang |  | - | climate | @OttoWinter |
| bedjet |  | ble_client | component | @jhansche |
| beken_spi_led_strip |  | - | light | - |
| bh1750 |  | - | sensor | - |
| bh1900nux |  | - | sensor | - |
| binary |  | - | component | - |
| binary_sensor | ✓ | - | component | @esphome/core |
| binary_sensor_map |  | - | sensor | - |
| bk72xx |  | - | component | @kuba2k2 |
| bl0906 |  | - | sensor | @athom-tech |
| bl0939 |  | - | sensor | @ziceva |
| bl0940 |  | - | sensor | @tobias- |
| bl0942 |  | - | sensor | @dbuezas |
| ble_client |  | esp32_ble_tracker | component | @buxtronix |
| ble_nus |  | - | component | @tomaszduda23 |
| ble_presence |  | - | binary_sensor | - |
| ble_rssi |  | - | sensor | - |
| ble_scanner |  | - | text_sensor | - |
| bluetooth_proxy |  | api, esp32 | component | @jesserockz |
| bm8563 |  | - | component | @abmantis |
| bme280_base | ✓ | - | component | @esphome/core |
| bme280_i2c |  | - | sensor | - |
| bme280_spi |  | - | sensor | - |
| bme680 |  | - | sensor | - |
| bme680_bsec |  | i2c | text_sensor, sensor | @trvrnrth |
| bme68x_bsec2 |  | - | text_sensor, sensor | @neffs |
| bme68x_bsec2_i2c |  | i2c | component | @neffs |
| bmi160 |  | - | sensor | @flaviut |
| bmp085 |  | - | sensor | - |
| bmp280 |  | - | sensor | - |
| bmp280_base |  | - | component | @ademuri |
| bmp280_i2c |  | - | sensor | - |
| bmp280_spi |  | - | sensor | - |
| bmp3xx |  | - | sensor | - |
| bmp3xx_base |  | - | component | @martgras |
| bmp3xx_i2c |  | - | sensor | - |
| bmp3xx_spi |  | - | sensor | - |
| bmp581 |  | - | sensor | - |
| bmp581_base |  | - | component | @kahrendt |
| bmp581_i2c |  | - | sensor | - |
| bp1658cj |  | - | output | @Cossid |
| bp5758d |  | - | output | @Cossid |
| bthome_mithermometer |  | esp32_ble_tracker | sensor | @nagyrobi |
| button | ✓ | - | component | @esphome/core |
| bytebuffer |  | - | component | @clydebarrow |
| camera |  | - | component | @DT-art1 |
| camera_encoder |  | - | component | @DT-art1 |
| canbus |  | - | component | @mvturnho |
| cap1188 |  | i2c | binary_sensor | @mreditor97 |
| captive_portal | ✓ | wifi | component | @esphome/core |
| cc1101 |  | spi | component | @lygris |
| ccs811 |  | - | sensor | - |
| cd74hc4067 |  | - | sensor | @asoehlke |
| ch422g |  | i2c | component | @jesterret |
| chsc6x |  | i2c | component | @kkosik20 |
| climate | ✓ | - | component | @esphome/core |
| climate_ir |  | remote_transmitter | component | @glmnet |
| climate_ir_lg |  | - | climate | - |
| cm1106 |  | - | sensor | - |
| color |  | - | component | - |
| color_temperature |  | - | light | - |
| combination |  | - | sensor | - |
| const | ✓ | - | component | @esphome/core |
| coolix |  | - | climate | - |
| copy |  | - | component | @OttoWinter |
| cover | ✓ | - | component | @esphome/core |
| cs5460a |  | - | sensor | - |
| cse7761 |  | - | sensor | - |
| cse7766 |  | - | sensor | - |
| cst226 |  | i2c | component | @clydebarrow |
| cst816 |  | i2c | component | @clydebarrow |
| ct_clamp |  | - | sensor | - |
| current_based |  | - | cover | @djwmarcx |
| custom |  | - | component | - |
| custom_component |  | - | component | - |
| cwww |  | - | light | - |
| dac7678 |  | i2c | output | @NickB1 |
| daikin |  | - | climate | - |
| daikin_arc |  | - | climate | @MagicBear |
| daikin_brc |  | - | climate | @hagak |
| dallas |  | - | sensor | - |
| dallas_temp |  | - | sensor | @ssieb |
| daly_bms |  | uart | text_sensor, sensor... | @s1lvi0 |
| dashboard_import | ✓ | api | component | @esphome/core |
| datetime |  | - | component | @rfdarter |
| debug | ✓ | logger | text_sensor, sensor | @esphome/core |
| deep_sleep |  | - | component | - |
| delonghi |  | - | climate | @grob6000 |
| demo |  | - | component | - |
| dfplayer |  | uart | component | @glmnet |
| dfrobot_sen0395 |  | uart | binary_sensor | @niklasweber |
| dht |  | - | sensor | @OttoWinter |
| dht12 |  | - | sensor | - |
| display |  | - | component | - |
| display_menu_base |  | - | component | @numo68 |
| dps310 |  | - | sensor | - |
| ds1307 |  | - | component | - |
| ds2484 |  | - | component | @mrk-its |
| dsmr |  | uart | text_sensor, sensor | @glmnet |
| duty_cycle |  | - | sensor | - |
| duty_time |  | - | sensor | @dudanov |
| e131 |  | network | component | - |
| ee895 |  | - | sensor | - |
| ektf2232 |  | - | component | - |
| emc2101 |  | i2c | component | @ellull |
| emmeti |  | - | climate | - |
| endstop |  | - | cover | - |
| ens160 |  | - | sensor | - |
| ens160_base |  | - | component | @vincentscode |
| ens160_i2c |  | - | sensor | - |
| ens160_spi |  | - | sensor | - |
| ens210 |  | - | sensor | - |
| epaper_spi | ✓ | - | display | @esphome/core |
| es7210 |  | - | component | - |
| es7243e |  | - | component | - |
| es8156 |  | - | component | - |
| es8311 |  | - | component | - |
| es8388 |  | - | component | - |
| esp32 | ✓ | - | component | @esphome/core |
| esp32_ble |  | esp32 | component | @jesserockz |
| esp32_ble_beacon |  | esp32 | component | - |
| esp32_ble_client |  | esp32 | component | @jesserockz |
| esp32_ble_server |  | esp32 | component | @jesserockz |
| esp32_ble_tracker |  | esp32 | component | @bdraco |
| esp32_camera |  | esp32 | component | - |
| esp32_camera_web_server |  | network | component | @ayufan |
| esp32_can |  | - | component | - |
| esp32_dac |  | - | output | - |
| esp32_hall |  | - | sensor | - |
| esp32_hosted |  | - | component | @swoboda1337 |
| esp32_improv |  | wifi, esp32 | component | @jesserockz |
| esp32_rmt |  | - | component | @jesserockz |
| esp32_rmt_led_strip |  | - | light | - |
| esp32_touch |  | esp32 | binary_sensor | - |
| esp8266 | ✓ | - | component | @esphome/core |
| esp8266_pwm |  | - | output | - |
| esp_ldo |  | - | component | @clydebarrow |
| esphome |  | - | component | - |
| espnow |  | - | component | @jesserockz |
| ethernet |  | esp32 | component | - |
| ethernet_info |  | - | text_sensor | @gtjadsonsantos |
| event |  | - | component | @nohat |
| exposure_notifications |  | esp32_ble_tracker | component | @OttoWinter |
| external_components |  | - | component | - |
| ezo |  | - | sensor | - |
| ezo_pmp |  | i2c | text_sensor, sensor... | @carlos-sarmiento |
| factory_reset |  | - | component | @anatoly-savchenkov |
| fan |  | - | component | - |
| fastled_base |  | - | component | @OttoWinter |
| fastled_clockless |  | - | light | - |
| fastled_spi |  | - | light | - |
| feedback |  | - | cover | @ianchi |
| fingerprint_grow |  | uart | sensor, binary_sensor | @OnFreund |
| font | ✓ | - | component | @esphome/core |
| fs3000 |  | - | sensor | - |
| ft5x06 |  | i2c | component | @clydebarrow |
| ft63x6 |  | - | component | @gpambrozio |
| fujitsu_general |  | - | climate | - |
| gcja5 |  | - | sensor | @gcormier |
| gdk101 |  | i2c | text_sensor, sensor... | @Szewcson |
| gl_r01_i2c |  | - | sensor | - |
| globals | ✓ | - | component | @esphome/core |
| gp2y1010au0f |  | - | sensor | - |
| gp8403 |  | i2c | component | @jesserockz |
| gpio | ✓ | - | component | @esphome/core |
| gpio_expander |  | - | component | - |
| gps |  | uart | component | @coogle |
| graph |  | display, sensor | component | @synco |
| graphical_display_menu |  | - | component | @MrMDavidson |
| gree |  | - | climate | - |
| grove_gas_mc_v2 |  | - | sensor | - |
| grove_tb6612fng |  | i2c | component | @max246 |
| growatt_solar |  | - | sensor | - |
| gt911 |  | i2c | component | @jesserockz |
| haier |  | - | climate | - |
| havells_solar |  | - | sensor | - |
| hbridge |  | - | component | - |
| hc8 |  | - | sensor | @omartijn |
| hdc1080 |  | - | sensor | - |
| hdc2010 |  | - | sensor | @optimusprimespace |
| he60r |  | - | cover | @clydebarrow |
| heatpumpir |  | - | climate | - |
| hitachi_ac344 |  | - | climate | - |
| hitachi_ac424 |  | - | climate | @sourabhjaiswal |
| hlk_fm22x |  | uart | text_sensor, sensor... | @OnFreund |
| hlw8012 |  | - | sensor | - |
| hlw8032 |  | - | sensor | @rici4kubicek |
| hm3301 |  | - | sensor | - |
| hmac_md5 |  | - | component | @dwmw2 |
| hmac_sha256 |  | - | component | @dwmw2 |
| hmc5883l |  | - | sensor | - |
| homeassistant | ✓ | - | component | @OttoWinter |
| honeywell_hih_i2c |  | - | sensor | @Benichou34 |
| honeywellabp |  | - | sensor | - |
| honeywellabp2_i2c |  | - | sensor | @jpfaff |
| host | ✓ | - | component | @esphome/core |
| hrxl_maxsonar_wr |  | - | sensor | - |
| hte501 |  | - | sensor | - |
| http_request |  | network | component | - |
| htu21d |  | - | sensor | - |
| htu31d |  | - | sensor | @betterengineering |
| hub75 |  | - | display | @stuartparmenter |
| hx711 |  | - | sensor | - |
| hydreon_rgxx |  | uart | sensor, binary_sensor | @functionpointer |
| hyt271 |  | - | sensor | @Philippe12 |
| i2c | ✓ | - | component | @esphome/core |
| i2c_device |  | i2c | component | @gabest11 |
| i2s_audio |  | esp32 | component | @jesserockz |
| iaqcore |  | - | sensor | - |
| ili9341 |  | - | display | - |
| ili9xxx |  | - | display | - |
| image |  | display | component | - |
| improv_base | ✓ | - | component | @esphome/core |
| improv_serial | ✓ | logger, wifi | component | @esphome/core |
| ina219 |  | - | sensor | - |
| ina226 |  | - | sensor | @Sergio303 |
| ina260 |  | - | sensor | - |
| ina2xx_base |  | - | component | @latonita |
| ina2xx_i2c |  | - | sensor | - |
| ina2xx_spi |  | - | sensor | - |
| ina3221 |  | - | sensor | - |
| infrared |  | - | component | @kbx81 |
| inkbird_ibsth1_mini |  | - | sensor | - |
| inkplate |  | - | display | @jesserockz |
| inkplate6 |  | - | display | - |
| integration |  | - | sensor | @OttoWinter |
| internal_temperature |  | - | sensor | @Mat931 |
| interval | ✓ | - | component | @esphome/core |
| ir_rf_proxy |  | - | component | @kbx81 |
| jsn_sr04t |  | - | sensor | @Mafus1 |
| json | ✓ | - | component | @esphome/core |
| kalman_combinator |  | - | sensor | - |
| kamstrup_kmp |  | - | sensor | - |
| key_collector |  | - | component | @ssieb |
| key_provider |  | - | component | @ssieb |
| kmeteriso |  | - | sensor | - |
| kuntze |  | - | sensor | - |
| lc709203f |  | - | sensor | @ilikecake |
| lcd_base |  | - | component | - |
| lcd_gpio |  | - | display | - |
| lcd_menu |  | - | component | @numo68 |
| lcd_pcf8574 |  | - | display | - |
| ld2410 |  | uart | text_sensor, sensor... | @sebcaps |
| ld2412 |  | uart | text_sensor, sensor... | @Rihan9 |
| ld2420 |  | uart | component | @descipher |
| ld2450 |  | uart | text_sensor, sensor... | @hareeshmu |
| ld24xx |  | - | component | @kbx81 |
| ledc |  | - | output | @OttoWinter |
| libretiny |  | - | text_sensor | @kuba2k2 |
| libretiny_pwm |  | - | output | @kuba2k2 |
| light | ✓ | - | component | @esphome/core |
| lightwaverf |  | - | component | @max246 |
| lilygo_t5_47 |  | - | component | - |
| lm75b |  | - | sensor | - |
| ln882x |  | - | component | @lamauny |
| lock | ✓ | - | component | @esphome/core |
| logger | ✓ | - | component | @esphome/core |
| lps22 |  | - | sensor | - |
| ltr390 |  | - | sensor | - |
| ltr501 |  | - | sensor | @latonita |
| ltr_als_ps |  | - | sensor | @latonita |
| lvgl |  | display | component | @clydebarrow |
| m5stack_8angle |  | i2c | component | @rnauber |
| mapping |  | - | component | @clydebarrow |
| matrix_keypad |  | - | component | @ssieb |
| max17043 |  | - | sensor | @blacknell |
| max31855 |  | - | sensor | - |
| max31856 |  | - | sensor | - |
| max31865 |  | - | sensor | - |
| max44009 |  | - | sensor | - |
| max6675 |  | - | sensor | - |
| max6956 |  | i2c | component | @looping40 |
| max7219 |  | - | display | - |
| max7219digit |  | - | display | - |
| max9611 |  | - | sensor | @mckaymatthew |
| mcp23008 |  | i2c | component | @jesserockz |
| mcp23016 |  | i2c | component | - |
| mcp23017 |  | i2c | component | @jesserockz |
| mcp23s08 |  | spi | component | @SenexCrenshaw |
| mcp23s17 |  | spi | component | @SenexCrenshaw |
| mcp23x08_base |  | - | component | @jesserockz |
| mcp23x17_base |  | - | component | @jesserockz |
| mcp23xxx_base |  | - | component | @jesserockz |
| mcp2515 |  | - | component | - |
| mcp3008 |  | spi | component | - |
| mcp3204 |  | spi | component | @rsumner |
| mcp3221 |  | - | sensor | @philippderdiedas |
| mcp4461 |  | i2c | component | @p1ngb4ck |
| mcp4725 |  | - | output | - |
| mcp4728 |  | i2c | component | @berfenger |
| mcp47a1 |  | - | output | - |
| mcp9600 |  | - | sensor | - |
| mcp9808 |  | - | sensor | - |
| md5 | ✓ | - | component | @esphome/core |
| mdns | ✓ | network | component | @esphome/core |
| media_player |  | - | component | @jesserockz |
| mhz19 |  | - | sensor | - |
| micro_wake_word |  | microphone | component | @kahrendt |
| micronova |  | uart | component | @jorre05 |
| microphone |  | - | component | @jesserockz |
| mics_4514 |  | - | sensor | - |
| midea |  | - | climate | - |
| midea_ac |  | - | climate | - |
| midea_ir |  | - | climate | - |
| mipi |  | - | component | - |
| mipi_dsi |  | - | display | @clydebarrow |
| mipi_rgb |  | - | display | @clydebarrow |
| mipi_spi |  | - | display | @clydebarrow |
| mitsubishi |  | - | climate | - |
| mixer |  | - | component | - |
| mlx90393 |  | - | sensor | @functionpointer |
| mlx90614 |  | - | sensor | - |
| mmc5603 |  | - | sensor | @benhoff |
| mmc5983 |  | - | sensor | @agoode |
| modbus |  | uart | component | - |
| modbus_controller |  | - | component | @martgras |
| monochromatic |  | - | light | - |
| mopeka_ble |  | esp32_ble_tracker | component | @spbrogan |
| mopeka_pro_check |  | - | sensor | @spbrogan |
| mopeka_std_check |  | - | sensor | @Fabian-Schmidt |
| mpl3115a2 |  | - | sensor | - |
| mpr121 |  | i2c | component | - |
| mpu6050 |  | - | sensor | - |
| mpu6886 |  | - | sensor | - |
| mqtt |  | network | component | - |
| mqtt_subscribe |  | - | component | - |
| ms5611 |  | - | sensor | - |
| ms8607 |  | - | sensor | @e28eta |
| msa3xx |  | i2c | text_sensor, sensor... | @latonita |
| my9231 |  | - | output | - |
| nau7802 |  | - | sensor | - |
| neopixelbus |  | - | light | - |
| network | ✓ | - | component | @esphome/core |
| nextion |  | - | display | - |
| nfc |  | - | component | @jesserockz |
| noblex |  | - | climate | @AGalfra |
| npi19 |  | - | sensor | - |
| nrf52 |  | - | component | @tomaszduda23 |
| ntc |  | - | sensor | - |
| number | ✓ | - | component | @esphome/core |
| one_wire |  | - | component | @ssieb |
| online_image |  | display, http_request | component | @guillempages |
| opentherm |  | - | component | @olegtarasov |
| openthread |  | esp32 | component | @mrene |
| openthread_info |  | - | text_sensor | - |
| opt3001 |  | - | sensor | - |
| ota | ✓ | - | component | @esphome/core |
| output | ✓ | - | component | @esphome/core |
| packages |  | - | component | - |
| packet_transport |  | - | sensor, binary_sensor | @clydebarrow |
| partition |  | - | light | - |
| pca6416a |  | i2c | component | @Mat931 |
| pca9554 |  | i2c | component | @hwstar |
| pca9685 |  | i2c | output | - |
| pcd8544 |  | - | display | - |
| pcf85063 |  | - | component | - |
| pcf8563 |  | - | component | - |
| pcf8574 |  | i2c | component | - |
| pi4ioe5v6408 |  | i2c | component | @jesserockz |
| pid |  | - | climate | @OttoWinter |
| pipsolar |  | uart | component | @andreashergert1984 |
| pm1006 |  | - | sensor | - |
| pm2005 |  | - | sensor | - |
| pmsa003i |  | - | sensor | - |
| pmsx003 |  | - | sensor | - |
| pmwcs3 |  | - | sensor | @SeByDocKy |
| pn532 |  | - | binary_sensor | @OttoWinter |
| pn532_i2c |  | i2c | component | @OttoWinter |
| pn532_spi |  | spi | component | @OttoWinter |
| pn7150 |  | - | component | @kbx81 |
| pn7150_i2c |  | i2c | component | @kbx81 |
| pn7160 |  | - | component | @kbx81 |
| pn7160_i2c |  | i2c | component | @kbx81 |
| pn7160_spi |  | spi | component | @kbx81 |
| power_supply | ✓ | - | component | @esphome/core |
| preferences | ✓ | - | component | @esphome/core |
| prometheus |  | - | component | - |
| psram | ✓ | PLATFORM_ESP32 | component | @esphome/core |
| pulse_counter |  | - | sensor | - |
| pulse_meter |  | - | sensor | - |
| pulse_width |  | - | sensor | - |
| pvvx_mithermometer |  | - | sensor | - |
| pylontech |  | uart | component | @functionpointer |
| pzem004t |  | - | sensor | - |
| pzemac |  | - | sensor | - |
| pzemdc |  | - | sensor | - |
| qmc5883l |  | - | sensor | - |
| qmp6988 |  | - | sensor | @andrewpc |
| qr_code |  | display | component | @wjtje |
| qspi_amoled |  | - | display | - |
| qspi_dbi |  | - | display | @clydebarrow |
| qwiic_pir |  | - | binary_sensor | - |
| radon_eye_ble |  | esp32_ble_tracker | component | @jeffeb3 |
| radon_eye_rd200 |  | - | sensor | @jeffeb3 |
| rc522 |  | - | binary_sensor | @glmnet |
| rc522_i2c |  | i2c | component | @glmnet |
| rc522_spi |  | spi | binary_sensor | @glmnet |
| rd03d |  | uart | sensor, binary_sensor | @jasstrong |
| rdm6300 |  | uart | binary_sensor | - |
| remote_base |  | - | component | - |
| remote_receiver |  | - | binary_sensor | - |
| remote_transmitter |  | - | component | - |
| resampler |  | - | component | - |
| resistance |  | - | sensor | - |
| restart | ✓ | - | component | @esphome/core |
| rf_bridge |  | uart | component | @jesserockz |
| rgb |  | - | light | - |
| rgbct |  | - | light | - |
| rgbw |  | - | light | - |
| rgbww |  | - | light | - |
| rotary_encoder |  | - | sensor | - |
| rp2040 |  | - | component | @jesserockz |
| rp2040_pio |  | rp2040 | component | - |
| rp2040_pio_led_strip |  | - | light | @Papa-DMan |
| rp2040_pwm |  | - | output | - |
| rpi_dpi_rgb |  | - | display | @clydebarrow |
| rtl87xx |  | - | component | @kuba2k2 |
| rtttl |  | - | component | @glmnet |
| runtime_stats |  | - | component | @bdraco |
| rust_test |  | - | component | - |
| ruuvi_ble |  | esp32_ble_tracker | component | - |
| ruuvitag |  | - | sensor | - |
| rx8130 |  | - | component | - |
| safe_mode |  | - | component | @paulmonigatti |
| scd30 |  | - | sensor | - |
| scd4x |  | - | sensor | - |
| script | ✓ | - | component | @esphome/core |
| sdl |  | - | display, binary_sensor | @clydebarrow |
| sdm_meter |  | - | sensor | - |
| sdp3x |  | - | sensor | - |
| sds011 |  | - | sensor | - |
| seeed_mr24hpc1 |  | uart | text_sensor, sensor... | @limengdu |
| seeed_mr60bha2 |  | uart | sensor, binary_sensor | @limengdu |
| seeed_mr60fda2 |  | uart | binary_sensor | @limengdu |
| selec_meter |  | - | sensor | - |
| select | ✓ | - | component | @esphome/core |
| sen0321 |  | - | sensor | @notjj |
| sen21231 |  | - | sensor | - |
| sen5x |  | - | sensor | - |
| senseair |  | - | sensor | - |
| sensirion_common |  | - | component | @martgras |
| sensor | ✓ | - | component | @esphome/core |
| servo |  | - | component | - |
| sfa30 |  | - | sensor | @ghsensdev |
| sgp30 |  | - | sensor | - |
| sgp40 |  | - | sensor | - |
| sgp4x |  | - | sensor | - |
| sha256 | ✓ | - | component | @esphome/core |
| shelly_dimmer |  | - | light | @rnauber |
| sht3xd |  | - | sensor | - |
| sht4x |  | - | sensor | - |
| shtcx |  | - | sensor | - |
| shutdown | ✓ | - | component | @esphome/core |
| sigma_delta_output |  | - | output | @Cat-Ion |
| sim800l |  | uart | sensor, binary_sensor | @glmnet |
| slow_pwm |  | - | output | - |
| sm10bit_base |  | - | component | @Cossid |
| sm16716 |  | - | output | - |
| sm2135 |  | - | output | @BoukeHaarsma23 |
| sm2235 |  | - | output | @Cossid |
| sm2335 |  | - | output | @Cossid |
| sm300d2 |  | - | sensor | - |
| sml |  | uart | component | @alengwenus |
| smt100 |  | - | sensor | @piechade |
| sn74hc165 |  | - | component | @jesserockz |
| sn74hc595 |  | - | component | - |
| sntp |  | - | component | - |
| socket | ✓ | - | component | @esphome/core |
| sonoff_d1 |  | - | light | @anatoly-savchenkov |
| sound_level |  | - | sensor | - |
| speaker |  | - | component | @jesserockz |
| speed |  | - | component | - |
| spi | ✓ | - | component | @esphome/core |
| spi_device |  | spi | component | @clydebarrow |
| spi_led_strip |  | spi | light | @clydebarrow |
| split_buffer |  | - | component | @jesserockz |
| sprinkler |  | - | component | @kbx81 |
| sps30 |  | - | sensor | - |
| ssd1306_base |  | - | component | - |
| ssd1306_i2c |  | - | display | - |
| ssd1306_spi |  | - | display | - |
| ssd1322_base |  | - | component | @kbx81 |
| ssd1322_spi |  | - | display | - |
| ssd1325_base |  | - | component | @kbx81 |
| ssd1325_spi |  | - | display | - |
| ssd1327_base |  | - | component | @kbx81 |
| ssd1327_i2c |  | - | display | - |
| ssd1327_spi |  | - | display | - |
| ssd1331_base |  | - | component | @kbx81 |
| ssd1331_spi |  | - | display | - |
| ssd1351_base |  | - | component | @kbx81 |
| ssd1351_spi |  | - | display | - |
| st7567_base |  | - | component | @latonita |
| st7567_i2c |  | - | display | @latonita |
| st7567_spi |  | - | display | @latonita |
| st7701s |  | - | display | @clydebarrow |
| st7735 |  | - | display | - |
| st7789v |  | - | display | - |
| st7920 |  | - | display | - |
| statsd |  | network | component | @Links2004 |
| status |  | - | binary_sensor | - |
| status_led |  | - | component | - |
| stepper |  | - | component | - |
| sts3x |  | - | sensor | - |
| stts22h |  | - | sensor | @B48D81EFCC |
| substitutions | ✓ | - | component | @esphome/core |
| sun |  | - | component | @OttoWinter |
| sun_gtil2 |  | uart | text_sensor, sensor | @Mat931 |
| switch | ✓ | - | component | @esphome/core |
| sx126x |  | spi | component | @swoboda1337 |
| sx127x |  | spi | component | @swoboda1337 |
| sx1509 |  | i2c | component | - |
| sy6970 |  | i2c | component | @linkedupbits |
| syslog |  | udp, logger... | component | @clydebarrow |
| t6615 |  | - | sensor | - |
| tc74 |  | - | sensor | @sethgirvan |
| tca9548a |  | i2c | component | @andreashergert1984 |
| tca9555 |  | i2c | component | @mobrembski |
| tcl112 |  | - | climate | - |
| tcs34725 |  | - | sensor | - |
| tee501 |  | - | sensor | - |
| teleinfo |  | - | component | @0hax |
| tem3200 |  | - | sensor | - |
| template |  | - | component | - |
| text |  | - | component | @mauritskorse |
| text_sensor |  | - | component | - |
| thermopro_ble |  | - | sensor | - |
| thermostat |  | - | climate | - |
| time | ✓ | - | component | @esphome/core |
| time_based |  | - | cover | - |
| tinyusb |  | - | component | @kbx81 |
| tlc59208f |  | i2c | output | - |
| tlc5947 |  | - | component | @rnauber |
| tlc5971 |  | - | component | @IJIJI |
| tm1621 |  | - | display | @Philippe12 |
| tm1637 |  | - | display, binary_sensor | - |
| tm1638 |  | - | display | - |
| tm1651 |  | - | component | @mrtoy-me |
| tmp102 |  | - | sensor | - |
| tmp1075 |  | - | sensor | @sybrenstuvel |
| tmp117 |  | - | sensor | - |
| tof10120 |  | - | sensor | - |
| tormatic |  | - | cover | @ti-mo |
| toshiba |  | - | climate | - |
| total_daily_energy |  | - | sensor | - |
| touchscreen |  | display | component | @jesserockz |
| tsl2561 |  | - | sensor | - |
| tsl2591 |  | - | sensor | @wjcarpenter |
| tt21100 |  | - | component | @kroimon |
| ttp229_bsf |  | - | binary_sensor | - |
| ttp229_lsf |  | i2c | binary_sensor | - |
| tuya |  | uart | component | - |
| tx20 |  | - | sensor | - |
| uart | ✓ | - | component | @esphome/core |
| udp |  | network | sensor, binary_sensor | @clydebarrow |
| ufire_ec |  | - | sensor | @pvizeli |
| ufire_ise |  | - | sensor | @pvizeli |
| uln2003 |  | - | component | - |
| ultrasonic |  | - | sensor | @OttoWinter |
| update |  | - | component | @jesserockz |
| uponor_smatrix |  | uart | component | @kroimon |
| uptime |  | - | component | - |
| usb_cdc_acm |  | tinyusb | component | @kbx81 |
| usb_host |  | esp32 | component | @clydebarrow |
| usb_uart |  | - | component | @clydebarrow |
| valve | ✓ | - | component | @esphome/core |
| vbus |  | uart | component | @ssieb |
| veml3235 |  | - | sensor | - |
| veml7700 |  | - | sensor | @latonita |
| version | ✓ | - | text_sensor | @esphome/core |
| vl53l0x |  | - | sensor | - |
| voice_assistant |  | api, microphone | component | @jesserockz |
| voltage_sampler |  | - | component | - |
| wake_on_lan |  | - | button | @willwill2will54 |
| watchdog |  | - | component | @oarcher |
| water_heater |  | - | component | @dhoeben |
| waveshare_epaper |  | - | display | @clydebarrow |
| web_server |  | - | component | - |
| web_server_base | ✓ | network | component | @esphome/core |
| web_server_idf |  | - | component | @dentra |
| weikai |  | - | component | @DrCoolZic |
| weikai_i2c |  | - | component | @DrCoolZic |
| weikai_spi |  | - | component | @DrCoolZic |
| whirlpool |  | - | climate | - |
| whynter |  | - | climate | @aeonsablaze |
| wiegand |  | - | component | @ssieb |
| wifi |  | - | component | - |
| wifi_info |  | - | text_sensor | - |
| wifi_signal |  | - | sensor | - |
| wireguard |  | time | text_sensor, sensor... | @lhoracek |
| wk2132_i2c |  | i2c | component | @DrCoolZic |
| wk2132_spi |  | spi | component | @DrCoolZic |
| wk2168_i2c |  | i2c | component | @DrCoolZic |
| wk2168_spi |  | spi | component | @DrCoolZic |
| wk2204_i2c |  | i2c | component | @DrCoolZic |
| wk2204_spi |  | spi | component | @DrCoolZic |
| wk2212_i2c |  | i2c | component | @DrCoolZic |
| wk2212_spi |  | spi | component | @DrCoolZic |
| wl_134 |  | - | text_sensor | - |
| wled |  | - | component | - |
| wts01 |  | - | sensor | - |
| x9c |  | - | output | - |
| xgzp68xx |  | - | sensor | @gcormier |
| xiaomi_ble |  | esp32_ble_tracker | component | - |
| xiaomi_cgd1 |  | - | sensor | - |
| xiaomi_cgdk2 |  | - | sensor | - |
| xiaomi_cgg1 |  | - | sensor | - |
| xiaomi_cgpr1 |  | - | binary_sensor | - |
| xiaomi_gcls002 |  | - | sensor | - |
| xiaomi_hhccjcy01 |  | - | sensor | - |
| xiaomi_hhccjcy10 |  | - | sensor | @fariouche |
| xiaomi_hhccpot002 |  | - | sensor | - |
| xiaomi_jqjcy01ym |  | - | sensor | - |
| xiaomi_lywsd02 |  | - | sensor | - |
| xiaomi_lywsd02mmc |  | - | sensor | - |
| xiaomi_lywsd03mmc |  | - | sensor | - |
| xiaomi_lywsdcgq |  | - | sensor | - |
| xiaomi_mhoc303 |  | - | sensor | @drug123 |
| xiaomi_mhoc401 |  | - | sensor | - |
| xiaomi_miscale |  | - | sensor | - |
| xiaomi_miscale2 |  | - | sensor | - |
| xiaomi_mjyd02yla |  | - | binary_sensor | - |
| xiaomi_mue4094rt |  | - | binary_sensor | - |
| xiaomi_rtcgq02lm |  | esp32_ble_tracker | sensor, binary_sensor | @jesserockz |
| xiaomi_wx08zm |  | - | binary_sensor | - |
| xiaomi_xmwsdj04mmc |  | - | sensor | - |
| xl9535 |  | i2c | component | @mreditor97 |
| xpt2046 |  | - | component | - |
| xxtea |  | - | component | @clydebarrow |
| yashima |  | - | climate | - |
| zephyr |  | - | component | @tomaszduda23 |
| zephyr_ble_server |  | - | component | - |
| zhlt01 |  | - | climate | - |
| zigbee |  | - | component | @tomaszduda23 |
| zio_ultrasonic |  | - | sensor | - |
| zwave_proxy |  | api, uart | component | @kbx81 |
| zyaura |  | - | sensor | - |
