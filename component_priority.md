# ESPHome Component Implementation Priority

Total components: 685

## Tier 1: Critical Foundation (26)

These are core-owned, highly depended-upon components.

| Priority | Component | Score | Dependents | Dependencies | Type |
|----------|-----------|-------|------------|--------------|------|
| 1 | **i2c** | 221 | 51 | - | component |
| 2 | **esp32** | 203 | 13 | - | component |
| 3 | **uart** | 200 | 30 | - | component |
| 4 | **esp8266** | 190 | 0 | - | component |
| 5 | **spi** | 189 | 19 | - | component |
| 6 | **time** | 182 | 2 | - | component |
| 7 | **sensor** | 181 | 1 | - | component |
| 8 | **binary_sensor** | 180 | 0 | - | component |
| 9 | **button** | 180 | 0 | - | component |
| 10 | **climate** | 180 | 0 | - | component |
| 11 | **cover** | 180 | 0 | - | component |
| 12 | **light** | 180 | 0 | - | component |
| 13 | **lock** | 180 | 0 | - | component |
| 14 | **network** | 180 | 10 | - | component |
| 15 | **number** | 180 | 0 | - | component |
| 16 | **output** | 180 | 0 | - | component |
| 17 | **select** | 180 | 0 | - | component |
| 18 | **switch** | 180 | 0 | - | component |
| 19 | **valve** | 180 | 0 | - | component |
| 20 | **api** | 174 | 4 | network | component |
| 21 | **logger** | 173 | 3 | - | component |
| 22 | **async_tcp** | 170 | 0 | network | component |
| 23 | **mdns** | 170 | 0 | network | component |
| 24 | **ota** | 170 | 0 | - | component |
| 25 | **socket** | 170 | 0 | - | component |
| 26 | **web_server_base** | 170 | 0 | network | component |

## Tier 2: High Priority (26)

Core-owned components with moderate dependencies.

| Priority | Component | Score | Dependents | Dependencies | Type |
|----------|-----------|-------|------------|--------------|------|
| 1 | **adc** | 100 | 0 | - | sensor |
| 2 | **bme280_base** | 100 | 0 | - | component |
| 3 | **captive_portal** | 100 | 0 | wifi | component |
| 4 | **const** | 100 | 0 | - | component |
| 5 | **dashboard_import** | 100 | 0 | api | component |
| 6 | **debug** | 100 | 0 | logger | sensor, text_sensor |
| 7 | **epaper_spi** | 100 | 0 | - | display |
| 8 | **font** | 100 | 0 | - | component |
| 9 | **globals** | 100 | 0 | - | component |
| 10 | **gpio** | 100 | 0 | - | component |
| 11 | **homeassistant** | 100 | 0 | - | component |
| 12 | **host** | 100 | 0 | - | component |
| 13 | **improv_base** | 100 | 0 | - | component |
| 14 | **improv_serial** | 100 | 0 | logger, wifi | component |
| 15 | **interval** | 100 | 0 | - | component |
| 16 | **json** | 100 | 0 | - | component |
| 17 | **md5** | 100 | 0 | - | component |
| 18 | **power_supply** | 100 | 0 | - | component |
| 19 | **preferences** | 100 | 0 | - | component |
| 20 | **psram** | 100 | 0 | PLATFORM_ESP32 | component |
| 21 | **restart** | 100 | 0 | - | component |
| 22 | **script** | 100 | 0 | - | component |
| 23 | **sha256** | 100 | 0 | - | component |
| 24 | **shutdown** | 100 | 0 | - | component |
| 25 | **substitutions** | 100 | 0 | - | component |
| 26 | **version** | 100 | 0 | - | text_sensor |

## Tier 3: Medium Priority (16)

Infrastructure and widely-used components.

| Component | Score | Dependents | Core |
|-----------|-------|------------|------|
| rp2040 | 91 | 1 |  |
| bk72xx | 90 | 0 |  |
| libretiny | 90 | 0 |  |
| rtl87xx | 90 | 0 |  |
| display | 87 | 7 |  |
| alarm_control_panel | 80 | 0 |  |
| datetime | 80 | 0 |  |
| event | 80 | 0 |  |
| fan | 80 | 0 |  |
| media_player | 80 | 0 |  |
| text_sensor | 80 | 0 |  |
| update | 80 | 0 |  |
| water_heater | 80 | 0 |  |
| wifi | 73 | 3 |  |
| ethernet | 70 | 0 |  |
| web_server | 70 | 0 |  |

## Tier 4: Standard Priority (0)

Components with some dependents.

Top 20:


## Tier 5: Low Priority (617)

Standalone components with few/no dependents.


## Top 20 Most Depended-Upon Components

| Rank | Component | Dependent Count | Core |
|------|-----------|-----------------|------|
| 1 | i2c | 51 | ✓ |
| 2 | uart | 30 | ✓ |
| 3 | spi | 19 | ✓ |
| 4 | esp32 | 13 | ✓ |
| 5 | network | 10 | ✓ |
| 6 | esp32_ble_tracker | 9 |  |
| 7 | display | 7 |  |
| 8 | api | 4 | ✓ |
| 9 | logger | 3 | ✓ |
| 10 | wifi | 3 |  |
| 11 | ble_client | 2 |  |
| 12 | microphone | 2 |  |
| 13 | time | 2 | ✓ |
| 14 | http_request | 1 |  |
| 15 | remote_transmitter | 1 |  |
| 16 | rp2040 | 1 |  |
| 17 | sensor | 1 | ✓ |
| 18 | tinyusb | 1 |  |
| 19 | udp | 1 |  |
| 20 | a01nyub | 0 |  |

## Recommended Implementation Order

### Phase 1: Core Foundation
Implement these first (in order):

1. **i2c** - base component
2. **esp32** - base component
3. **uart** - base component
4. **esp8266** - base component
5. **spi** - base component
6. **sensor** - base component
7. **binary_sensor** - base component
8. **network** - base component
9. **switch** - base component
10. **api** - base component
11. **logger** - base component

### Phase 2: Infrastructure
Build communication and device interfaces:

1. **mdns** - base component
2. **ota** - base component
3. **web_server_base** - base component

### Phase 3: Common Components
Implement frequently-used sensors and devices:

1. adc
2. bme280_base
3. captive_portal
4. const
5. dashboard_import
6. debug
7. epaper_spi
8. font
9. globals
10. gpio
11. homeassistant
12. host
13. improv_base
14. improv_serial
15. interval
16. json
17. md5
18. power_supply
19. preferences
20. psram

### Phase 4+: Remaining Components
Implement remaining 617 components as needed.
