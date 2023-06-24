# Copyright (c) 2023 One DB Ventures, LLC (AKA, No Flipping Switches)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# TODO_LIST
# Write catch for temps greater or less than the temp sensor can read, make sure its 10deg past range


import time
# get time when code starts
start_time_ticks_ms = time.ticks_ms()
import usocket as socket
import umqtt.simple
# import esp32
import machine
import network
import onewire
import ds18x20
import os
import gc
import json
import ubinascii
import umsgpack
from micropython import const


# [Exceptions]
# noinspection PyPep8Naming
class ds18b20_85C_Exception(Exception):
    """Raised when the ds18b20 value is 85"""
    pass


# noinspection PyPep8Naming
class ds18b20_not_int_float_Exception(Exception):
    """Raised when the ds18b20 value is not an integer or float"""
    pass


# [ Functions ]
# returns json as a python dictionary
def json_to_dictionary(path_and_or_file_name_to_json):
    with open(path_and_or_file_name_to_json, 'r') as openfile:
        # noinspection PyTypeChecker
        return json.load(openfile)


# writes dictionary to a json file
def dictionary_to_json(python_dictionary, path_and_or_file_name_to_json):
    with open(path_and_or_file_name_to_json, "w") as outfile:
        # noinspection PyTypeChecker
        json.dump(python_dictionary, outfile)


# Battery (Volts, Remaining%)
def batt():
    # supply voltage gpio pin for voltage divider
    gpio_pos_volts_supply = machine.Pin(Constant_batt_gpio_pos_volts_supply_pin, machine.Pin.OUT)

    # set gpio_pos_volts_supply high/(+)
    gpio_pos_volts_supply.value(1)
    # give time for voltage to settle
    time.sleep_ms(50)

    # analog voltage gpio pin
    adc_gpio_read_batt_voltage = machine.Pin(Constant_adc_gpio_read_batt_voltage_pin)
    # Create an ADC object out of our pin object
    adc_object = machine.ADC(adc_gpio_read_batt_voltage)

    # 11 dB attenuation means full 0.15 - 2.45V range
    adc_object.atten(adc_object.ATTN_11DB)

    # read voltage
    microvolts_after_divider = adc_object.read_uv()

    # turn off voltage pin used to supply gpio (+)
    gpio_pos_volts_supply.value(0)

    # Calculate voltage from microvolts to volts
    volts_after_divider = microvolts_after_divider / 1000000
    # convert to original voltage before voltage divider
    volts = volts_after_divider * 1.523809524  # Voltage In = Voltage Out * (R1+R2/R2) R1=1.1Kohms R2=2.1Kohms

    # Calculate estimated battery percentage remaining, also keep from going past 100% or under 0%
    remaining_percent = int(100 * (volts - Constant_battery_min_voltage) / (Constant_battery_max_voltage - Constant_battery_min_voltage))  # 100 * (adc_volts - BATTERY_MIN_ADC) / (BATTERY_MAX_ADC - BATTERY_MIN_ADC)
    if remaining_percent > 100:
        remaining_percent = 100
    elif remaining_percent < 0:
        remaining_percent = 0
    return volts, remaining_percent


# ds18b20 Temperature Sensor
def ds18b20(ds18b20_serial_number):
    # check that sensor was found and loaded else report code
    if not ds18b20_serial_number:
        return 'XXXXXXXX', 999
    # pin used to supply gpio (+) voltage to temp sensor
    gpio_pin_pos_volt_supply_for_ds18b20 = machine.Pin(Constant_ds18b20_gpio_pos_pin, machine.Pin.OUT)
    # set pin1 high/(+)
    gpio_pin_pos_volt_supply_for_ds18b20.value(1)
    # give time for voltage to settle
    time.sleep_ms(2500)
    # pin used to communicate with one wire ds18b20 temp sensor
    ds18b20_one_wire = machine.Pin(Constant_ds18b20_one_wire_pin)
    # define sensors object useing library
    ds_sensors = ds18x20.DS18X20(onewire.OneWire(ds18b20_one_wire))
    # convert human-readable serial number back into bytearray
    ds18b20rom = bytearray(8)
    for i in range(8):
        ds18b20rom[i] = int(ds18b20_serial_number[i * 2:i * 2 + 2], 16)
    # Check for error in python import when reading temp and handle temp sensor 85C
    ds18b20_85C_Exception_count = 1
    ds18b20_not_int_float_Exception_count = 1
    any_exception_count = 1
    while True:
        # noinspection PyShadowingNames,PyUnusedLocal,PyBroadException
        try:
            ds_sensors.convert_temp()
            time.sleep_ms(1000)
            temp = ds_sensors.read_temp(ds18b20rom)
            if temp == 85:
                raise ds18b20_85C_Exception('Temperature is 85C, are we sure this is the temp or is it a code from sensor')
            if not isinstance(temp, (int, float)):
                raise ds18b20_not_int_float_Exception('Temperature is not an integer or float')
            break
        except ds18b20_85C_Exception as e:
            print('Error: {0}'.format(e))
            print('attempt {0} of 10'.format(ds18b20_85C_Exception_count))
            if ds18b20_85C_Exception_count == 10:
                temp = 85
                break
            ds18b20_85C_Exception_count += 1
        except ds18b20_not_int_float_Exception as e:
            print('Error: {0}'.format(e))
            print('attempt {0} of 10'.format(ds18b20_not_int_float_Exception_count))

            if ds18b20_not_int_float_Exception_count == 10:
                temp = 998
                break
            ds18b20_not_int_float_Exception_count += 1
        except Exception as e:
            print('Error: {0}'.format(e))
            print('unable to get temperature')
            print('attempt {0} of 10'.format(any_exception_count))
            if any_exception_count == 10:
                # set temp error code
                temp = 997
                break
            any_exception_count += 1
    # set pin1 low/(-)
    gpio_pin_pos_volt_supply_for_ds18b20.value(0)
    return ds18b20_serial_number, temp


# Return the current status of the wireless connection
def wifi_connection_status(stat):
    if stat == network.STAT_ASSOC_FAIL:
        return 'STAT_ASSOC_FAIL: received frame other than authentication or probe request'
    elif stat == network.STAT_BEACON_TIMEOUT:
        return 'STAT_BEACON_TIMEOUT: missed a number beacon frames from wifi station'
    elif stat == network.STAT_CONNECTING:
        return 'STAT_CONNECTING: connecting in progress'
    elif stat == network.STAT_GOT_IP:
        return 'STAT_GOT_IP: connection successful'
    elif stat == network.STAT_HANDSHAKE_TIMEOUT:
        return 'STAT_HANDSHAKE_TIMEOUT: missed handshakes with wifi station'
    elif stat == network.STAT_IDLE:
        return 'STAT_IDLE: no connection and no activity'
    elif stat == network.STAT_NO_AP_FOUND:
        return 'STAT_NO_AP_FOUND: failed because no wifi station found or replied'
    elif stat == network.STAT_WRONG_PASSWORD:
        return 'STAT_WRONG_PASSWORD: failed due to incorrect password'
    else:
        return 'STAT_UNKNOWN: unknown return value of {0}'.format(stat)


# control the blinks of led
def led_blink(pin, blinks, interval_on, interval_off, interval_before_sets, interval_after_sets):
    # establish pin
    gpio_pin_for_led = machine.Pin(pin, machine.Pin.OUT)
    # set pin1 low/(-)
    gpio_pin_for_led.value(0)

    time.sleep_ms(interval_before_sets)
    for x in range(blinks):
        gpio_pin_for_led.value(1)
        time.sleep_ms(interval_on)
        gpio_pin_for_led.value(0)
        time.sleep_ms(interval_off)
    time.sleep_ms(interval_after_sets)


def wifi_client_scan():  # returns wifi_client_scan_formatted
    # scan for other wireless networks, so we can calculate best channel to use
    # must enable network.STA_IF, station aka client that connects to upstream Wi-Fi's
    wifi_client = network.WLAN(network.STA_IF)
    # Make sure wifi_client is not active before trying to connect (if no True/False given it will output current state)
    if wifi_client.active():
        # Make sure we are not connected to a wi-fi network
        if wifi_client.isconnected():
            wifi_client.disconnect()
            # give wi-fi time to disconnect
            time.sleep_ms(250)
        wifi_client.active(False)
        # give wi-fi time to go down
        time.sleep_ms(250)

    wifi_client.active(True)
    # give wi-fi time to come up
    time.sleep_ms(250)
    # noinspection PyShadowingNames
    try:
        wifi_client_scan_raw = wifi_client.scan()
        # disconnect after scan
        wifi_client.active(False)
        # give wi-fi time to go down
        time.sleep_ms(250)
        if wifi_client.active():
            # Make sure we are not connected to a wi-fi network
            wifi_client.active(False)
        # give wi-fi time to go down
        time.sleep_ms(250)
    except Exception as e:
        print('Error: {0}'.format(e))
        print('wifi_client_scan_raw')
        return False

    # format wifi_client_scan_raw, a list containing tuples, some containing binary form, into something human-readable
    wifi_client_scan_formatted = []  # create new list for formatted tuple's
    scan_security_to_readable_string = 'unknown'

    # noinspection PyShadowingNames
    for the_tuple in wifi_client_scan_raw:

        # ssid - only list tuple's that have a ssid or are not hidden
        # noinspection PyUnresolvedReferences
        scan_ssid = str(the_tuple[0].decode('UTF-8'))
        scan_hidden = the_tuple[5]
        if len(scan_ssid) > 0 and not scan_hidden:
            # noinspection PyTypeChecker
            scan_bssid = ubinascii.hexlify(the_tuple[1]).decode('UTF-8')
            scan_channel = the_tuple[2]
            scan_rssi = the_tuple[3]
            scan_security = the_tuple[4]

            if scan_security == 0:
                scan_security_to_readable_string = 'open'
            elif scan_security == 1:
                scan_security_to_readable_string = 'WEP'
            elif scan_security == 2:
                scan_security_to_readable_string = 'WPA-PSK'
            elif scan_security == 3:
                scan_security_to_readable_string = 'WPA2-PSK'
            elif scan_security == 4:
                scan_security_to_readable_string = 'WPA/WPA2-PSK'

            wifi_client_scan_formatted.append((scan_ssid, scan_bssid, scan_channel, scan_rssi, scan_security_to_readable_string))

    return wifi_client_scan_formatted


# [Static]
# Battery - Min and Max voltage range
Constant_battery_min_voltage = const(3.025)
Constant_battery_max_voltage = const(3.425)
# Battery - Pin used to supply gpio (+) voltage to voltage divider resister 1.1kohms
Constant_batt_gpio_pos_volts_supply_pin = const(11)
# Battery - Pin used for taking analog voltage
Constant_adc_gpio_read_batt_voltage_pin = const(4)

# ds18b20 temp sensor - Pin used to supply gpio (+) voltage to temperature sensor
Constant_ds18b20_gpio_pos_pin = const(5)
# ds18b20 temp sensor - Pin used to communicate with one wire ds18b20 temperature sensor
Constant_ds18b20_one_wire_pin = const(3)

# onboard led - pin used to turn on and off the onboard led
Constant_onboard_led_gpio_pin = const(15)

# Jumper pin  (station 0/access point 1) mode - Pin input used to decided what mode selected
Constant_jumper_station_or_access_point_pin = const(16)

# Intermittent button pin
Constant_intermittent_button_pin = const(0)

# [Global]
# Jumper pin detect if in station or access point mode
station_or_access_point = machine.Pin(Constant_jumper_station_or_access_point_pin, machine.Pin.IN, machine.Pin.PULL_UP)
# needs time to settle
time.sleep_ms(50)
station_or_access_point_startup_value = station_or_access_point.value()

# Intermittent button pin detect if pressed for factory reset of device
factory_reset = machine.Pin(Constant_intermittent_button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
# needs time to settle
time.sleep_ms(50)
factory_reset_startup_value = factory_reset.value()  # 0 pressed, 1 released


# [START]
# print('NFS - starting the machine')

# uncomment when working on code. Adds delay, so we have time to work with the IDE
time.sleep_ms(2000)

# Load device_settings.json to Python dictionary, Else create them
try:
    device_settings_dictionary = json_to_dictionary('device_settings.json')
    # print('Loaded device_settings.json')
except Exception as e:
    print(' ')
    print('Error: {0}'.format(e))
    print('Unable to open file: device_settings.json')
    print('cetch_all: try to delete device_settings.json if it cant be opened')
    try:
        os.remove('device_settings.json')
    except Exception as e:
        print('Error: {0}'.format(e))

    import hashlib

    # Get unique ID from the esp32, every device has a different one
    raw_unique_id = machine.unique_id()
    unique_id_b1 = ubinascii.hexlify(raw_unique_id)
    unique_id = unique_id_b1.decode('UTF-8')

    # create access_point_ssid by hashing unique_id
    raw_hash_unique_id = hashlib.sha256(unique_id_b1)
    hash_unique_id_b1 = ubinascii.hexlify(raw_hash_unique_id.digest())
    hash_unique_id_b2 = hash_unique_id_b1.decode('UTF-8')
    hash_unique_id = hash_unique_id_b2[-12:]

    # Get ds18b20 Serial number,
    # this is so we don't have to waste battery scanning for it after each wake from deep sleap
    # pin used to supply gpio (+) voltage to temp sensor
    gpio_pin_pos_volt_supply_for_ds18b20_x1 = machine.Pin(Constant_ds18b20_gpio_pos_pin, machine.Pin.OUT)
    # set pin1 high/(+)
    gpio_pin_pos_volt_supply_for_ds18b20_x1.value(1)
    # give time for voltage to initialize ds18b20 temp sensor
    time.sleep_ms(1000)

    # pin used to communicate with one wire ds18b20 temp sensor
    ds18b20_one_wire_x1 = machine.Pin(Constant_ds18b20_one_wire_pin)

    # define sensors object using library
    ds_sensors_x1 = ds18x20.DS18X20(onewire.OneWire(ds18b20_one_wire_x1))

    # scan for the serial number of the temp sensor
    sensorIDs = ds_sensors_x1.scan()

    # set pin1 low/(-)
    gpio_pin_pos_volt_supply_for_ds18b20_x1.value(0)

    # convert bytearray into a human-readable serial number
    try:
        ds18b20_sn = ''.join('%02X' % i for i in iter(sensorIDs[0]))
    except Exception as e:
        print(' ')
        print('Error: {0}'.format(e))
        print('Unable convert bytearray into a human-readable serial number')
        print('Make sure ds18b20 is connected and not broken')
        print('ds18b20_sn set to False')
        print(' ')
        ds18b20_sn = False

    device_settings_dictionary = {
        "device": "NFS.1001.a",
        "board": "esp32-s2-mini-wemos",
        "battery": "1x3.6V_D_ER34615@3.6v",
        "software_version": "0.2.18",
        "unique_id": 'NFS-{0}'.format(unique_id),
        "ds18b20_sn": ds18b20_sn,
        "hash_unique_id": hash_unique_id
    }
    dictionary_to_json(device_settings_dictionary, 'device_settings.json')
    print('Created device_settings.json')
    print(' ')
    print('Machine will reset')
    machine.reset()

# Load wifi_settings.json to Python dictionary, Else create it
try:
    wifi_settings_dictionary = json_to_dictionary('wifi_settings.json')
    # print('Loaded wifi_settings.json')
except Exception as e:
    print(' ')
    print('Error: {0}'.format(e))
    print('Unable to open file: wifi_settings.json')
    print('cetch_all: try to delete wifi_settings.json if it cant be opened')

    try:
        os.remove('wifi_settings.json')
    except Exception as e:
        print('Error: {0}'.format(e))

    wifi_settings_dictionary = {
        "record_data_interval_ms": 5 * 60000,
        "send_data_interval_list_length": 12,
        "send_data_interval_min": 60,
        "access_point": {
            "wifi_ssid": device_settings_dictionary['unique_id'],
            "wifi_password": device_settings_dictionary['hash_unique_id']
        },
        "known_wifi": {
        },
        "mqtt_url": 'noflippingswitches.com',
        "mqtt_ssl": False,
        "mqtt_port": 1883,
        "mqtt_username": '',
        "mqtt_password": ''
    }
    dictionary_to_json(wifi_settings_dictionary, 'wifi_settings.json')
    print('Created wifi_settings.json')
    print(' ')
    print('Machine will reset')
    machine.reset()


# [ Factory Reset ]
if factory_reset_startup_value == 0:
    led_blink(Constant_onboard_led_gpio_pin, 20, 20, 120, 0, 0)  # (pin, blinks, interval_on, interval_off, interval_before_sets, interval_after_sets)
    try:
        os.remove('wifi_settings.json')
    except Exception as e:
        print('Error: {0}'.format(e))
    try:
        os.remove('device_settings.json')
    except Exception as e:
        print('Error: {0}'.format(e))
    machine.reset()


# [ Station Mode ]
# watchdog timmer, The WDT is used to restart the system when the application crashes and ends up into a non-recoverable state.
# Once started it cannot be stopped or reconfigured in any way.
# After enabling, you must “feed” the watchdog periodically to prevent it from expiring and resetting the system.
wdt = machine.WDT(timeout=45000)  # enable it with a timeout of 45s

# if no wi-fi is declared by user then enable hotspot setup
if station_or_access_point_startup_value == 0:  # station 0 jumper bridged/connected, 1 dissconected

    print('station mode selected')
    # get tempature of ds18b20 located inside the case
    tempC_internal = ds18b20(device_settings_dictionary["ds18b20_sn"])
    # print('ds18b20_unit_tempC: {0}'.format(tempC_internal[1]))

    # if the rtc memry lenth is < 1 we know this is the first temp reading and only need to save the temp
    # noinspection PyArgumentList
    rtc_read_memory = machine.RTC().memory()
    rtc_read_memory_len = len(rtc_read_memory)
    if rtc_read_memory_len < 1:
        rtc_memory_list = [int(tempC_internal[1] * 10000)]
        # convert rtc_memory_list to a MessagePack serialization and write it to rtc memory
        rtc_memory_list_bytes = umsgpack.dumps(rtc_memory_list)
        # write rtc_memory_list_bytes to rtc memory

        # noinspection PyArgumentList
        machine.RTC().memory(rtc_memory_list_bytes)

        # garbage collection before deep sleap
        gc.collect()
        # feed the watchdog timmer
        wdt.feed()

        # calculate time to sleap
        time_to_sleep = wifi_settings_dictionary['record_data_interval_ms']  # * wifi_settings_dictionary['send_data_interval_list_length']

        # calculate time to offset sleap by how long it took to run code
        stop_time_ticks_ms = time.ticks_ms()
        diff_start_stop = time.ticks_diff(stop_time_ticks_ms, start_time_ticks_ms)

        # calculate corrected time to sleep
        corrected_time_to_sleep = time_to_sleep - diff_start_stop

        # ya cant sleep less than nothin!
        # you cant go back in time!
        # there is no foo.enable(time_machine)
        if corrected_time_to_sleep < 1:
            machine.deepsleep(100)
        else:
            machine.deepsleep(corrected_time_to_sleep)

    else:
        # else the rtc memry lenth is > 1 get the length of the list in rtc_memory and check that it's less than the wifi_settings_dictionary['send_data_interval_list_length']
        # try to convert contents of rtc memory, that should be a MessagePack serialization byte literal, into a list

        # noinspection PyBroadException
        try:
            rtc_memory_list = umsgpack.loads(rtc_read_memory)
            # check that rtc_memory_list is formatted correctly if not reset machine to clear the rtc memory
            if not all([isinstance(item, int) for item in rtc_memory_list]):
                machine.reset()
        except Exception as e:
            # print('Error: {0}'.format(e))
            # print('Unable to convert rtc_read_memory back into a python rtc_memory_list')
            # print('instead resetting machine to clear read_memory')
            rtc_memory_list = False  # rtc_memory_list cant be undefined
            machine.reset()

        rtc_memory_list_len = len(rtc_memory_list)
        # if list is less than the wifi_settings_dictionary['send_data_interval_list_length'] record another temp
        if rtc_memory_list_len < wifi_settings_dictionary['send_data_interval_list_length']:

            # add temp to end of rtc_memory_list
            rtc_memory_list.append(int(tempC_internal[1] * 10000))

            # convert rtc_memory_list to a MessagePack serialization and write it to rtc memory
            rtc_memory_list_bytes = umsgpack.dumps(rtc_memory_list)

            # write rtc_memory_list_bytes to rtc memory
            # noinspection PyArgumentList
            machine.RTC().memory(rtc_memory_list_bytes)

            # garbage collection before deep sleap
            gc.collect()
            # feed the watchdog timmer
            wdt.feed()

            # calculate time to sleap
            time_to_sleep = wifi_settings_dictionary['record_data_interval_ms']  # * wifi_settings_dictionary['send_data_interval_list_length']

            # calculate time to offset sleap by how long it took to run code
            stop_time_ticks_ms = time.ticks_ms()
            diff_start_stop = time.ticks_diff(stop_time_ticks_ms, start_time_ticks_ms)

            # calculate corrected time to sleep
            corrected_time_to_sleep = time_to_sleep - diff_start_stop

            # ya cant sleep less than nothin!
            # you cant go back in time!
            # there is no foo.enable(time_machine)
            if corrected_time_to_sleep < 1:
                machine.deepsleep(100)
            else:
                machine.deepsleep(corrected_time_to_sleep)

        # else it's time to send the data to the server!
        else:
            # do as much as possible before connecting to wi-fi, as it eats the most power while on.

            # add temp to end of rtc_memory_list
            rtc_memory_list.append(int(tempC_internal[1] * 10000))

            # Reverse list and re-float all items in list
            rtc_memory_reversed_list = list([items / 10000 for items in reversed(rtc_memory_list)])

            # get battery voltage
            batt_result = batt()

            # CONNECT
            # define Wi-Fi station
            wifi_station = network.WLAN(network.STA_IF)
            # Make sure wifi_station is not active (note: if no True/False given as an argument it will output current state)
            # Make sure we are not connected to a Wi-Fi network
            if wifi_station.active():
                # Make sure we are not connected to a Wi-Fi network
                if wifi_station.isconnected():
                    wifi_station.disconnect()
                    # give Wi-Fi time to disconnect
                    time.sleep_ms(250)
                wifi_station.active(False)
                # give Wi-Fi time to go down
                time.sleep_ms(250)

            wifi_station.active(True)
            # give Wi-Fi time to come up
            time.sleep_ms(250)

            # how many attemps to connect to this network/ssid. will try # of times if good conection is lost NOTE: call them one at a time else jams up
            wifi_station.config(hostname=device_settings_dictionary['unique_id'])
            wifi_station.config(reconnects=15)

            # NOTE: anoying you cannot unassign static values for ifconfig, you must reset device. rather try dhcp networks first.
            # NOTE: if a ssid had a password and now does not the last 5 values are cashed. user must change the ssid for network on thier router/device! Gerrr.

            # make sure we are not connected
            if not wifi_station.isconnected():
                # if no Wi-Fi is declared by user then sleep for max time to save batt until user sets a value
                if 'wifi_ssid' not in wifi_settings_dictionary['known_wifi']:
                    # garbage collection before deep sleap
                    gc.collect()
                    machine.deepsleep()
                else:
                    if 'wifi_password' not in wifi_settings_dictionary['known_wifi']:
                        wifi_station.connect(wifi_settings_dictionary['known_wifi']['wifi_ssid'])
                    else:
                        wifi_station.connect(wifi_settings_dictionary['known_wifi']['wifi_ssid'], wifi_settings_dictionary['known_wifi']['wifi_password'])

                    # print('Trying to Connect to: {0}'.format(wifi_settings_dictionary['known_wifi']['wifi_ssid']))
                    while wifi_station.status() == network.STAT_CONNECTING:
                        pass
                    # get status after while loop finishes
                    status = wifi_connection_status(wifi_station.status())
                    # print(str(status))
                    wifi_station.disconnect()

                    # IMPORTANT! feed the watchdog after trying to connect to Wi-Fi ssid
                    wdt.feed()  # feed the watchdog timmer

            # unable to connect, try to store extra entry into avalible rtc memory. If no room in rtc memory left then remove oldeset entry from list. Then preform a defined sleep cycle
            if not wifi_station.isconnected():
                if rtc_read_memory_len < 1920:
                    # convert rtc_memory_list to a MessagePack serialization and write it to rtc memory
                    rtc_memory_list_bytes = umsgpack.dumps(rtc_memory_list)

                    # write rtc_memory_list_bytes to rtc memory
                    # noinspection PyArgumentList
                    machine.RTC().memory(rtc_memory_list_bytes)

                    # garbage collection before deep sleap
                    gc.collect()

                    # calculate time to sleap
                    time_to_sleep = wifi_settings_dictionary['record_data_interval_ms']  # * wifi_settings_dictionary['send_data_interval_list_length']

                    # calculate time to offset sleap by how long it took to run code
                    stop_time_ticks_ms = time.ticks_ms()
                    diff_start_stop = time.ticks_diff(stop_time_ticks_ms, start_time_ticks_ms)

                    # calculate corrected time to sleep
                    corrected_time_to_sleep = time_to_sleep - diff_start_stop

                    wdt.feed()  # feed the watchdog timmer

                    # ya cant sleep less than nothin!
                    # you cant go back in time!
                    # there is no foo.enable(time_machine)
                    if corrected_time_to_sleep < 1:
                        machine.deepsleep(100)
                    else:
                        machine.deepsleep(corrected_time_to_sleep)

                else:
                    del rtc_memory_list[0]
                    rtc_memory_list_bytes = umsgpack.dumps(rtc_memory_list)

                    # write rtc_memory_list_bytes to rtc memory
                    # noinspection PyArgumentList
                    machine.RTC().memory(rtc_memory_list_bytes)

                    # garbage collection before deep sleap
                    gc.collect()

                    # calculate time to sleap
                    time_to_sleep = wifi_settings_dictionary['record_data_interval_ms']  # * wifi_settings_dictionary['send_data_interval_list_length']

                    # calculate time to offset sleap by how long it took to run code
                    stop_time_ticks_ms = time.ticks_ms()
                    diff_start_stop = time.ticks_diff(stop_time_ticks_ms, start_time_ticks_ms)

                    # calculate corrected time to sleep
                    corrected_time_to_sleep = time_to_sleep - diff_start_stop

                    # ya cant sleep less than nothin!
                    # you cant go back in time!
                    # there is no foo.enable(time_machine)
                    if corrected_time_to_sleep < 1:
                        machine.deepsleep(100)
                    else:
                        machine.deepsleep(corrected_time_to_sleep)

            # We have connected to the Wi-Fi, do stuff
            if wifi_station.isconnected():
                # get connection info
                ifconfig = wifi_station.ifconfig()
                hostname = wifi_station.config('hostname')
                ssid = wifi_station.config('ssid')
                # print('Connected to: {0}'.format(ssid))

                data_out_dictionary = {
                    device_settings_dictionary['unique_id']: {
                        "sensor": {
                            "tempC": rtc_memory_reversed_list,
                            "record_data_interval_ms": int(wifi_settings_dictionary['record_data_interval_ms']),
                            "send_data_interval_min": int(wifi_settings_dictionary['send_data_interval_min'])
                        },
                        "battery": {
                            "volts": batt_result[0],
                            "percentage": batt_result[1]
                        },
                        "device": {
                            "device": device_settings_dictionary['device'],
                            "sensor_id": device_settings_dictionary['ds18b20_sn']
                        }

                    }
                }

                data_out_json = json.dumps(data_out_dictionary)

                # mqtt
                client_id = hostname
                server = 'sun-tmp-mqtt.no-fs.com'
                port = 8883
                user = 'admin'
                password = 'J61X0vog851odYpAqlEfr1gI8ytoHVZQSF9p'
                mqttc = umqtt.simple.MQTTClient(client_id, server, port, user, password,  keepalive=60, ssl=True)
                mqttc.connect(clean_session=True)
                # print('mqttc.ping(): ', mqttc.ping())
                topic_byte = ('noflippingswitches/sensor/' + hostname).encode()
                msg_byte = data_out_json.encode()
                mqttc.publish(topic_byte, msg_byte, retain=False, qos=1)
                mqttc.disconnect()
                wifi_station.disconnect()
                wifi_station.active(False)

                # create checks for disconnect on qos=1, so we can save the msg and keep loggin temps!

                # clear rtc memory
                # noinspection PyArgumentList
                machine.RTC().memory(b'')

                # garbage collection before deep sleap
                gc.collect()

                # calculate time to sleap
                time_to_sleep = wifi_settings_dictionary['record_data_interval_ms']  # * wifi_settings_dictionary['send_data_interval_list_length']

                # calculate time to offset sleap by how long it took to run code
                stop_time_ticks_ms = time.ticks_ms()
                diff_start_stop = time.ticks_diff(stop_time_ticks_ms, start_time_ticks_ms)

                # calculate corrected time to sleep
                corrected_time_to_sleep = time_to_sleep - diff_start_stop

                wdt.feed()  # feed the watchdog timmer

                # ya cant sleep less than nothin!
                # you cant go back in time!
                # there is no foo.enable(time_machine)
                if corrected_time_to_sleep < 1:
                    machine.deepsleep(100)
                else:
                    machine.deepsleep(corrected_time_to_sleep)

# [ Access Point Mode ]
    # ------------------------------------------------------------------------------------------------------------------
else:  # access_point

    # global vars
    html_wifi_connection_status = ''
    ip_address_html = ''
    subnet_mask_html = ''
    gateway_server_html = ''
    dns_server_html = ''
    hostname_html = ''
    ssid_html = ''
    html_mqtt_connection_status = ''
    data_out_dictionary = {}

    print('Access Point mode selected')

    # log system info if dictionary loadded successfully
    print('\ndevice: {0}\nboard: {1}\nbattery: {2}\nsoftware_version: {3}\nunique_id: {4}\nhash_unique_id: {5}\nds18b20_sn: {6}\n'.format(
        device_settings_dictionary['device'],  # {0}
        device_settings_dictionary['board'],  # {1}
        device_settings_dictionary['battery'],  # {2}
        device_settings_dictionary['software_version'],  # {3}
        device_settings_dictionary['unique_id'],  # {4}
        device_settings_dictionary['hash_unique_id'],  # {5}
        device_settings_dictionary['ds18b20_sn'],  # {6}
    ))

    # get tempature of ds18b20
    tempC_internal_ap = ds18b20(device_settings_dictionary["ds18b20_sn"])
    # get battery voltage and % estleft
    batt_result_ap = batt()

    # scan for Wi-Fi networks and get best channel to use for Access Point
    ap_client_scan = wifi_client_scan()
    print('ap_client_scan: ', ap_client_scan)

    # check connection to mqtt
    # has user set ssid for his Wi-Fi connection?
    if 'wifi_ssid' not in wifi_settings_dictionary['known_wifi']:
        html_wifi_connection_status = 'Select_a_SSID_Network_Name'
    else:
        # CONNECT to user defined wifi network
        # define wifi station
        wifi_station = network.WLAN(network.STA_IF)
        # Make sure wifi_station is not active (note: if no True/False given as an argument it will output current state)
        # Make sure we are not connected to a wifi network
        if wifi_station.active():
            # Make sure we are not connected to a wifi network
            if wifi_station.isconnected():
                wifi_station.disconnect()
                # give wifi time to disconnect
                time.sleep_ms(250)
            wifi_station.active(False)
            # give wifi time to go down
            time.sleep_ms(250)

        wifi_station.active(True)
        # give wifi time to come up
        time.sleep_ms(250)

        # how many attemps to connect to this network/ssid. will try # of times if good conection is lost NOTE: call them one at a time else jams up
        wifi_station.config(hostname=device_settings_dictionary['unique_id'])
        wifi_station.config(reconnects=5)

        # NOTE: anoying you cannot unassign static values for ifconfig, you must reset device. rather try dhcp networks first.
        # NOTE: if a ssid had a password and now does not the last 5 values are cashed. user must change the ssid for network on thier router/device! Gerrr.

        # make sure we are not connected
        if not wifi_station.isconnected():
            if 'wifi_password' not in wifi_settings_dictionary['known_wifi']:
                wifi_station.connect(wifi_settings_dictionary['known_wifi']['wifi_ssid'])
            else:
                wifi_station.connect(wifi_settings_dictionary['known_wifi']['wifi_ssid'], wifi_settings_dictionary['known_wifi']['wifi_password'])

            # print('Trying to Connect to: {0}'.format(wifi_settings_dictionary['known_wifi']['wifi_ssid']))
            while wifi_station.status() == network.STAT_CONNECTING:
                pass
            # get status after while loop finishes
            status = wifi_connection_status(wifi_station.status())
            if status == 'STAT_GOT_IP: connection successful':
                html_wifi_connection_status = 'connection_successful'
            print(html_wifi_connection_status)
            print(str(status))

        # We have connected to the wifi, do stuff
        if wifi_station.isconnected():
            # get connection info
            ifconfig = wifi_station.ifconfig()
            ip_address_html = ifconfig[0]
            subnet_mask_html = ifconfig[1]
            gateway_server_html = ifconfig[2]
            dns_server_html = ifconfig[3]
            hostname_html = wifi_station.config('hostname')
            ssid_html = wifi_station.config('ssid')
            # print('Connected to: {0}'.format(ssid))

            data_out_dictionary = {
                device_settings_dictionary['unique_id']: {
                    "sensor": {
                        "tempC": tempC_internal_ap[1],
                        "record_data_interval_ms": 0,
                        "send_data_interval_min": 0
                    },
                    "battery": {
                        "volts": batt_result_ap[0],
                        "percentage": batt_result_ap[1]
                    },
                    "device": {
                        "device": device_settings_dictionary['device'],
                        "sensor_id": device_settings_dictionary['ds18b20_sn']
                    }

                }
            }

            data_out_json = json.dumps(data_out_dictionary)

            # mqtt
            client_id = hostname_html
            server = wifi_settings_dictionary['mqtt_url']
            if server == 'noflippingswitches.com' or server == 'no-fs.com':
                port = 8883
                keepalive = 60
                ssl = True
                user = None
                password = None
            else:
                port = wifi_settings_dictionary['mqtt_port']
                keepalive = 60
                ssl = wifi_settings_dictionary['mqtt_ssl']
                user = wifi_settings_dictionary['mqtt_username']
                if user == '':
                    user = None
                password = wifi_settings_dictionary['mqtt_password']
                if password == '':
                    password = None

            mqttc = umqtt.simple.MQTTClient(client_id, server, port, user, password, keepalive, ssl)

            while_loop_counter = 1
            while True:
                # noinspection PyBroadException
                try:
                    mqttc.connect(clean_session=True)
                    topic_byte = ('noflippingswitches/sensor/' + hostname_html).encode()
                    msg_byte = data_out_json.encode()
                    mqttc.publish(topic_byte, msg_byte, retain=False, qos=1)
                    mqttc.disconnect()
                    html_mqtt_connection_status = 'mqtt_connection_successful'
                    print('mqtt connection successful')
                    break
                except Exception as e:
                    if while_loop_counter == 5:
                        html_mqtt_connection_status = 'mqtt_unable_to_connect_check_mqtt_settings_or_internet_connection'
                        break
                    while_loop_counter += 1
                    print('mqtt exception')

        wifi_station.disconnect()
        wifi_station.active(False)
        # give wifi time to go down
        time.sleep_ms(250)

    # start up access point
    # noinspection PyUnresolvedReferences
    ap = network.WLAN(network.AP_IF)
    # Make sure ap is not active (note: if no True/False given as an argument it will output current state)
    # Make sure we are not connected to ap network
    if ap.active():
        ap.active(False)
        # give ap time to go down
        time.sleep_ms(250)
    ap.active(True)
    # give ap time to come up
    time.sleep_ms(250)

    # config ap
    # use AUTH_WPA2_PSK for authmode. Note, AUTH_WPA_WPA2_PSK, WPA2 has been standard scence 2006! if users device cant handle it ... tooo bad! also apple does not like WPA1
    # noinspection PyUnresolvedReferences
    ap.config(channel=1, hidden=False, essid=wifi_settings_dictionary['access_point']['wifi_ssid'], authmode=network.AUTH_WPA2_PSK, password=wifi_settings_dictionary['access_point']['wifi_password'])
    print('essid:', ap.config('essid'))
    print("password: ", wifi_settings_dictionary['access_point']['wifi_password'])
    print('channel:', ap.config('channel'))
    print('hidden:', ap.config('hidden'))

    while ap.active() is False:
        pass
    # IMPORTANT! feed the watchdog after trying to setup_ ap
    wdt.feed()  # feed the watchdog timmer

    print('AP creation successful and Broadcasting')
    print(ap.ifconfig())

    placeholder = 'placeholder'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # used if socket is soft reset.
    s.bind(('', 80))
    s.listen(1)
    # s.settimeout(3)

    first_tab_access_point_machine_reset = False
    third_tab_access_point_machine_reset = False
    while True:
        try:
            # set watchdog time, so it resets if server locks up
            # also see about How to retry after exception? https://stackoverflow.com/questions/2083987/how-to-retry-after-exception
            # also try new device as this one may be foobar! If that does not work then try a limited for loop

            # noinspection PyTupleAssignmentBalance,PyNoneFunctionAssignment
            connection, address = s.accept()
            request = connection.recv(1024).decode('utf-8')
            request_list = request.split(' ')  # Split request from spaces
            # print('address: ', address)  # Client IP address
            # print('client request list: ', request_list)

            # Check if client has a language preff, if so set it
            html_language_list = []  # default lang english
            for i in range(len(request_list)):
                # print(i, request_list[i])
                if request_list[i].find('Accept-Language') != -1:
                    clean_returns_off_languages_header = request_list[i + 1].splitlines()[0]
                    # print('clean_returns_off_languages_header:', clean_returns_off_languages_header)
                    languages = clean_returns_off_languages_header.split(",")
                    # print('languages: ', languages)
                    locale_q_pairs = []
                    for language in languages:
                        if language.split(";")[0] == language:
                            # no q => q = 1
                            locale_q_pairs.append((language.strip(), "1"))
                        else:
                            locale = language.split(";")[0].strip()
                            q = language.split(";")[1].split("=")[1]
                            locale_q_pairs.append((locale, q))

                    # Sort by second element of tuple
                    def by_second_elem_off_tuple(elem):
                        return float(elem[1])


                    locale_q_pairs.sort(key=by_second_elem_off_tuple, reverse=True)
                    # print(locale_q_pairs)

                    for the_tuple in locale_q_pairs:
                        if the_tuple[0][0:2] not in html_language_list:
                            html_language_list.append(the_tuple[0][0:2])
                    print('language_list:', html_language_list)

            language_dictionary_html = {}
            language_html_code = 'en'
            if html_language_list:
                for language in html_language_list:
                    # translations path
                    path = '/lang/html/language_{0}.json'.format(language)
                    language_html_code = language
                    print('set language_html_code to:', language_html_code)
                    try:
                        # load translation
                        language_dictionary_html = json_to_dictionary(path)
                        # print('Loaded language_dictionary_html: {0}'.format(path))
                        break
                    except Exception as e:
                        print(' ')
                        print('Error: {0}'.format(e))
                        print('Unable to load language_dictionary_html: {0}'.format(path))
            else:
                # translations path
                path = '/lang/html/language_en.json'
                try:
                    # load translation
                    language_dictionary_html = json_to_dictionary(path)
                    # print('Loaded language_dictionary_html: {0}'.format(path))
                except Exception as e:
                    print(' ')
                    print('Error: {0}'.format(e))
                    print('Unable to load language_dictionary_html: {0}'.format(path))

            param_request_dictionary = {}
            if language_dictionary_html:
                get_request_list = request_list[1].split('?')
                print('get request list: ', get_request_list)

                file_request = get_request_list[0].lstrip('/')
                # print('file request: ', file_request)

                if request_list[1].find('=') != -1:
                    split_param_requests = get_request_list[1].split("&")
                    for i in split_param_requests:
                        key, value = i.split("=")
                        # assigning keys with values
                        param_request_dictionary[key] = value

                print('param_request_dictionary: ', param_request_dictionary)

                # what to send client based on request
                if file_request == '' or file_request == 'wifi-static' or file_request == 'wifi-dhcp' or file_request == 'wifi-scan' or file_request == 'wifi-apply' or file_request == 'sensor-apply' or file_request == 'test-connection':
                    header = 'HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n'

                    # set Meta Refresh empty
                    meta_refresh = ''

                    # -=[ first-tab, WiFi }=-
                    # format found/scanned for networks
                    found_networks_html = ''

                    if 'ssid' in param_request_dictionary:
                        # header = 'HTTP/1.1 303 See Other\nLocation: /#first-tab\nContent-Type: text/html\nConnection: close\n\n'
                        meta_refresh = '<meta http-equiv="refresh" content="0; url=/#first-tab"/>'

                        if 'ipaddress' in param_request_dictionary:
                            wifi_settings_dictionary['known_wifi'] = {
                                "wifi_ssid": param_request_dictionary['ssid'],
                                "wifi_password": param_request_dictionary['password'],
                                "ip_address": param_request_dictionary['ipaddress'],
                                "subnet_mask": param_request_dictionary['subnetmask'],
                                "gateway_server": param_request_dictionary['gateway'],
                                "dns_server": param_request_dictionary['dns']
                            }
                        else:
                            wifi_settings_dictionary['known_wifi'] = {
                                "wifi_ssid": param_request_dictionary['ssid'],
                                "wifi_password": param_request_dictionary['password']
                            }
                        dictionary_to_json(wifi_settings_dictionary, 'wifi_settings.json')
                        print('Updated wifi_settings.json')
                        print('{0}'.format(wifi_settings_dictionary))

                    if 'scan' in param_request_dictionary or first_tab_access_point_machine_reset:
                        if first_tab_access_point_machine_reset:
                            meta_refresh = '<meta http-equiv="refresh" content="30; url=/#first-tab"/>'
                        else:
                            # header = 'HTTP/1.1 303 See Other\nLocation: /#first-tab\nContent-Type: text/html\nConnection: close\n\n'
                            meta_refresh = '<meta http-equiv="refresh" content="0; url=/#first-tab"/>'

                        found_networks_html += '{0}&#13;&#10;{1}&#13;&#10;{2}%&#13;&#10;{3}&#13;&#10;{4}&#13;&#10;'.format(
                            language_dictionary_html["Disconnecting_WiFi_access_point"],  # {0}
                            language_dictionary_html["Scanning_WiFi_networks"],  # {1}
                            language_dictionary_html["Webpage_will_automatically_refresh"],  # {2}
                            language_dictionary_html["Please_wait_x_seconds"],  # {3}
                            language_dictionary_html["You_may_have_to_reconnect_to_the_WiFi"],  # {4}
                        )

                    elif ap_client_scan:
                        for i in range(len(ap_client_scan)):
                            # print(i, ap_client_scan[1][i])
                            if ap_client_scan[i][3] < -90:
                                signal_quality = 0
                            elif ap_client_scan[i][3] > -40:
                                signal_quality = 100
                            else:
                                signal_quality = 2 * (ap_client_scan[i][3] + 90)

                            found_networks_html += '{6}: {0}&#13;&#10;{7}: {1}&#13;&#10;{8}: {2}%&#13;&#10;{9}: {3}dBm&#13;&#10;{10}: {4}&#13;&#10;{11}: {5}&#13;&#10;&#13;&#10;'.format(
                                ap_client_scan[i][0],  # {0} SSID
                                ap_client_scan[i][1],  # {1} BSSID
                                signal_quality,  # {2} Signal Quality
                                ap_client_scan[i][3],  # {3} RSSI
                                ap_client_scan[i][2],  # {4} Channel
                                ap_client_scan[i][4],  # {5} Security
                                language_dictionary_html["SSID_Network_Name"],  # {6}
                                'BSSID',  # {7}
                                language_dictionary_html["Signal_Quality"],  # {8}
                                'RSSI',  # {9}
                                language_dictionary_html["Channel"],  # {10}
                                language_dictionary_html["Security"],  # {11}
                            )

                    # when hover over DHCP / Static (Order of if statments matter!)
                    style_content = 'Static'  # default DHCP --> Static

                    if 'wifi_ssid' in wifi_settings_dictionary['known_wifi']:
                        ssid_html_input_vlaue = '<input type="text" name="ssid" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['wifi_ssid'])
                        password_html_input_vlaue = '<input type="password" name="password" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['wifi_password'])

                    else:
                        ssid_html_input_vlaue = '<input type="text" name="ssid" placeholder="{0} *" required>'.format(language_dictionary_html["SSID_Network_Name"])
                        password_html_input_vlaue = '<input type="password" name="password" placeholder="{0} *" required>'.format(language_dictionary_html["Password"])

                    html_content_wifi = '<form action="/#first-tab" method="GET"><legend><input type="hidden"/><button class="dhcpButton" formaction="/wifi-static#first-tab"><span>{0}</span></button></legend></form><form action="/wifi-apply#first-tab" method="GET">{1}{2}'.format(
                        language_dictionary_html["DHCP"],  # {0}
                        ssid_html_input_vlaue,  # {1}
                        password_html_input_vlaue  # {2}
                    )
                    if file_request == 'wifi-static' or (file_request != 'wifi-dhcp' and 'ip_address' in wifi_settings_dictionary['known_wifi']):
                        style_content = 'DHCP'

                        if 'ip_address' in wifi_settings_dictionary['known_wifi']:
                            ip_address_html_input_vlaue = '<input type="text" name="ipaddress" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['ip_address'])
                            subnetmask_html_input_vlaue = '<input type="text" name="subnetmask" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['subnet_mask'])
                            gateway_html_input_vlaue = '<input type="text" name="gateway" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['gateway_server'])
                            dns_html_input_vlaue = '<input type="text" name="dns" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" value="{0}" required>'.format(wifi_settings_dictionary['known_wifi']['dns_server'])

                        else:
                            ip_address_html_input_vlaue = '<input type="text" name="ipaddress" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" placeholder="{0}: xxx.xxx.xxx.xxx" required>'.format(language_dictionary_html["IP_Address"])
                            subnetmask_html_input_vlaue = '<input type="text" name="subnetmask" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" placeholder="{0}: xxx.xxx.xxx.xxx" required>'.format(language_dictionary_html["Subnet_Mask"])
                            gateway_html_input_vlaue = '<input type="text" name="gateway" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" placeholder="{0}: xxx.xxx.xxx.xxx" required>'.format(language_dictionary_html["Gateway"])
                            dns_html_input_vlaue = '<input type="text" name="dns" minlength="7" maxlength="15" pattern="^((\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])\\.){{3}}(\\d{{1,2}}|1\\d\\d|2[0-4]\\d|25[0-5])$" placeholder="{0}: xxx.xxx.xxx.xxx" required>'.format(language_dictionary_html["DNS_Server"])

                        html_content_wifi = '<form action="/#first-tab" method="GET"><legend><input type="hidden"/><button class="dhcpButton" formaction="/wifi-dhcp#first-tab"><span>{0}</span></button></legend></form><form action="/wifi-apply#first-tab" method="GET">{5}{6}{1}{2}{3}{4}'.format(
                            language_dictionary_html["Static"],  # {0}
                            ip_address_html_input_vlaue,  # {1}
                            subnetmask_html_input_vlaue,  # {2}
                            gateway_html_input_vlaue,  # {3}
                            dns_html_input_vlaue,  # {4}
                            ssid_html_input_vlaue,  # {5}
                            password_html_input_vlaue  # {6}
                        )

                    # -=[ second-tab, Sensor }=-
                    # get/format sensor information for html
                    sensor_info_html = '{3} °C: {0}&#13;&#10;{4} V: {1}&#13;&#10;{4} %: {2}&#13;&#10;'.format(
                        tempC_internal_ap[1],
                        batt_result_ap[0],
                        batt_result_ap[1],
                        language_dictionary_html["Tempature"],
                        language_dictionary_html["Battery"]
                    )

                    if 'refresh_second_tab' in param_request_dictionary:
                        # header = 'HTTP/1.1 303 See Other\nLocation: /#second-tab\nContent-Type: text/html\nConnection: close\n\n'
                        meta_refresh = '<meta http-equiv="refresh" content="0; url=/#second-tab"/>'

                    if 'record_every_int' in param_request_dictionary:
                        # header = 'HTTP/1.1 303 See Other\nLocation: /#first-tab\nContent-Type: text/html\nConnection: close\n\n'
                        meta_refresh = '<meta http-equiv="refresh" content="0; url=/#second-tab"/>'

                        if param_request_dictionary['record_every_min_hr'] == 'hours':
                            record_data_interval = 60 * int(param_request_dictionary['record_every_int'])
                        else:
                            record_data_interval = int(param_request_dictionary['record_every_int'])
                        # protect deepsleep from overflow
                        if record_data_interval > 31536000000:
                            record_data_interval = 31536000000

                        if param_request_dictionary['send_every_min_hr'] == 'hours':
                            send_data_interval = 60 * int(param_request_dictionary['send_every_int'])
                        else:
                            send_data_interval = int(param_request_dictionary['send_every_int'])
                        # protect deepsleep from overflow
                        if record_data_interval > 31536000000:
                            record_data_interval = 31536000000

                        interval_list_length = int(send_data_interval / record_data_interval)
                        if interval_list_length <= 1:
                            interval_list_length = 0
                            send_data_interval = record_data_interval
                            wifi_settings_dictionary['record_data_interval_ms'] = record_data_interval * 60000  # 60000ms in a minute
                            wifi_settings_dictionary['send_data_interval_list_length'] = interval_list_length
                            wifi_settings_dictionary['send_data_interval_min'] = send_data_interval

                        else:
                            # rtc memory bytes: 2003 when rtc memory list len: 400 (max 2048)
                            if interval_list_length <= 400:
                                wifi_settings_dictionary['record_data_interval_ms'] = record_data_interval * 60000  # 60000ms in a minute
                                wifi_settings_dictionary['send_data_interval_list_length'] = interval_list_length
                                wifi_settings_dictionary['send_data_interval_min'] = send_data_interval
                            else:
                                interval_list_length = 400
                                send_data_interval = int(record_data_interval * interval_list_length)
                                wifi_settings_dictionary['record_data_interval_ms'] = record_data_interval * 60000  # 60000ms in a minute
                                wifi_settings_dictionary['send_data_interval_list_length'] = interval_list_length
                                wifi_settings_dictionary['send_data_interval_min'] = send_data_interval

                        dictionary_to_json(wifi_settings_dictionary, 'wifi_settings.json')
                        print('Updated wifi_settings.json')
                        print('{0}'.format(wifi_settings_dictionary))

                    # -=[ third-tab, Data }=-
                    if wifi_settings_dictionary['mqtt_url'] == 'noflippingswitches.com' or wifi_settings_dictionary['mqtt_url'] == 'no-fs.com':
                        html_content_data_extra_settings = ''
                    else:
                        html_content_data_extra_settings = '<label for="mqtt_user_name" style="font-size:16px">{0}: <input type="text" id="mqtt_user_name" name="mqtt_user_name" value="{1}"></label><label for="mqtt_password" style="font-size:16px">{2}: <input type="password" id="mqtt_password" name="mqtt_password" value="{3}"></label><label for="mqtt_port_number" style="font-size:16px">{4}: <input type="number" id="mqtt_port_number" name="mqtt_port_number" value="{5}" min="1" max="65535"></label>'.format(
                            language_dictionary_html['user_name'],  # {0}
                            wifi_settings_dictionary['mqtt_username'],  # {1}
                            language_dictionary_html['Password'],  # {2}
                            wifi_settings_dictionary['mqtt_password'],  # {3}
                            language_dictionary_html['port_number'],  # {4}
                            wifi_settings_dictionary['mqtt_port']  # {5}
                        )

                        if wifi_settings_dictionary['mqtt_ssl']:
                            html_content_data_extra_settings += '<label for="ssl" style="font-size:16px">SSL: <input type="checkbox" id="ssl" name="ssl" value="True" checked></label>'
                        else:
                            html_content_data_extra_settings += '<label for="ssl" style="font-size:16px">SSL: <input type="checkbox" id="ssl" name="ssl" value="True"></label>'

                    # format output for html_content_data
                    html_content_data = '{0}'.format(language_dictionary_html['failed_incorrect_password_out_of_range_or_unreachable'])

                    if html_wifi_connection_status == 'connection_successful':
                        html_content_data = '{12}&#13;&#10;{0}: {1}&#13;&#10;{2}: {3}&#13;&#10;{4}: {5}&#13;&#10;{6}: {7}&#13;&#10;{8}: {9}&#13;&#10;{10}: {11}&#13;&#10;'.format(
                            language_dictionary_html['hostname'],  # {0}
                            hostname_html,  # {1}
                            language_dictionary_html['SSID_Network_Name'],  # {2}
                            ssid_html,  # {3}
                            language_dictionary_html['IP_Address'],  # {4}
                            ip_address_html,  # {5}
                            language_dictionary_html['Subnet_Mask'],  # {6}
                            subnet_mask_html,  # {7}
                            language_dictionary_html['Gateway'],  # {8}
                            gateway_server_html,  # {9}
                            language_dictionary_html['DNS_Server'],  # {10}
                            dns_server_html,  # {11},
                            language_dictionary_html['connection_successful']  # {12}
                        )
                        if html_mqtt_connection_status == 'mqtt_unable_to_connect_check_mqtt_settings_or_internet_connection':
                            html_content_data += '&#13;&#10;{0}'.format(language_dictionary_html['mqtt_unable_to_connect_check_mqtt_settings_or_internet_connection'])
                        if html_mqtt_connection_status == 'mqtt_connection_successful':
                            html_content_data += '&#13;&#10;{3}&#13;&#10;{0}: {1}&#13;&#10;{2}'.format(
                                language_dictionary_html['mqtt_server'],  # {0}
                                wifi_settings_dictionary['mqtt_url'],  # {1}
                                language_dictionary_html['data_sent'],  # {2}
                                language_dictionary_html['mqtt_connection_successful']  # {3}
                            )

                    if 'refresh_third_tab' in param_request_dictionary or third_tab_access_point_machine_reset:
                        if third_tab_access_point_machine_reset:
                            meta_refresh = '<meta http-equiv="refresh" content="30; url=/#third-tab"/>'
                            print('content=30')
                        else:
                            # header = 'HTTP/1.1 303 See Other\nLocation: /#third-tab\nContent-Type: text/html\nConnection: close\n\n'
                            meta_refresh = '<meta http-equiv="refresh" content="0; url=/#third-tab"/>'

                            if 'mqtt_address' in param_request_dictionary:
                                wifi_settings_dictionary['mqtt_url'] = param_request_dictionary['mqtt_address']
                            if 'mqtt_user_name' in param_request_dictionary:
                                wifi_settings_dictionary['mqtt_username'] = param_request_dictionary['mqtt_user_name']
                            if 'mqtt_password' in param_request_dictionary:
                                wifi_settings_dictionary['mqtt_password'] = param_request_dictionary['mqtt_password']
                            if 'mqtt_port_number' in param_request_dictionary:
                                wifi_settings_dictionary['mqtt_port'] = param_request_dictionary['mqtt_port_number']

                            if 'ssl' not in param_request_dictionary:
                                wifi_settings_dictionary['mqtt_ssl'] = False
                            else:
                                wifi_settings_dictionary['mqtt_ssl'] = True

                            dictionary_to_json(wifi_settings_dictionary, 'wifi_settings.json')
                            print('Updated wifi_settings.json')
                            print('{0}'.format(wifi_settings_dictionary))
                            print('content=30')

                        html_content_data = '{0}&#13;&#10;{1}&#13;&#10;{2}%&#13;&#10;{3}%&#13;&#10;'.format(
                            language_dictionary_html["Disconnecting_WiFi_access_point"],  # {0}
                            language_dictionary_html["Webpage_will_automatically_refresh"],  # {1}
                            language_dictionary_html["Please_wait_x_seconds"],  # {2}
                            language_dictionary_html["You_may_have_to_reconnect_to_the_WiFi"],  # {3}
                        )

                    # START CREATION OF HTML FOR SITE
                    html_start = '<!DOCTYPE html>'
                    html_lang = '<html lang={0}>'.format(language_html_code)
                    html_head_start = '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1">{0}<link rel="icon" type="image/svg" href="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIj8+IDxzdmcgd2lkdGg9IjUwMCIgaGVpZ2h0PSI1MDAiIHZpZXdCb3g9IjAgMCA1MDAgNTAwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPiA8IS0tIENyZWF0ZWQgd2l0aCBTVkctZWRpdCAtIGh0dHBzOi8vZ2l0aHViLmNvbS9TVkctRWRpdC9zdmdlZGl0LS0+IDxnIGNsYXNzPSJsYXllciI+IDx0aXRsZT5MYXllciAxPC90aXRsZT4gPHRleHQgZmlsbD0iIzAwMDAwMCIgZm9udC1mYW1pbHk9IlNlcmlmIiBmb250LXNpemU9IjMwMCIgaWQ9InN2Z18yIiBzdHJva2U9IiMwMDAwMDAiIHN0cm9rZS13aWR0aD0iMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgeD0iMTIxLjQiIHhtbDpzcGFjZT0icHJlc2VydmUiIHk9IjIyNS44Ij5OPC90ZXh0PiA8dGV4dCBmaWxsPSIjMDAwMDAwIiBmb250LWZhbWlseT0iU2VyaWYiIGZvbnQtc2l6ZT0iMzAwIiBpZD0ic3ZnXzMiIHN0cm9rZT0iIzAwMDAwMCIgc3Ryb2tlLXdpZHRoPSIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiB4PSIzMDIuNCIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSIgeT0iMzQ2LjgiPkY8L3RleHQ+IDx0ZXh0IGZpbGw9IiMwMDAwMDAiIGZvbnQtZmFtaWx5PSJTZXJpZiIgZm9udC1zaXplPSIzMDAiIGlkPSJzdmdfNCIgc3Ryb2tlPSIjMDAwMDAwIiBzdHJva2Utd2lkdGg9IjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIHRyYW5zZm9ybT0ibWF0cml4KDEgMCAwIDEgMCAwKSIgeD0iNDEwLjQiIHhtbDpzcGFjZT0icHJlc2VydmUiIHk9IjQ4OC44Ij5TPC90ZXh0PiA8L2c+IDwvc3ZnPg=="><title>NFS</title><meta name="noflippingswitches" content="NFS">'.format(meta_refresh)
                    html_static_style = 'body {background: #CDDC39;font-family: Verdana, Arial, Helvetica, Tahoma, sans-serif;}.tab {display: none;}.tab:target {display: block;}.tab:last-child {display: block;}.tab:target~section.tab:last-child {display: none;}.tab>nav>a.active {background: #fffffff6;color: #000;}main .tab {width: 100%;max-width: 500px;}main {width: 100%;max-width: 500px;margin: 0 auto;padding: 50px 0;}.tab>* {width: 100%;padding-top: 10px;margin: 0;}.tab>nav {padding: 0;display: flex;justify-content: center;gap: 5px;}.tab>nav>a {cursor: pointer;padding: 13px 25px;margin: 0px 2px;background: #000;display: inline-block;color: #fff;border-top: 3px solid #000;border-radius: 3px 3px 0px 0px;text-decoration: none;}.tab-box {padding: 5px;background: #fff;box-shadow: 0 2rem 2rem #00000080;animation: fadein 2s;border-radius: 5px;}.tab-box img {width: 100%;height: 100%;}@keyframes fadein {from {opacity: 0;}to {opacity: 1;}}.form-style-5{max-width: 500px;background: #f4f7f8;padding: 20px;border-radius: 5px;}.form-style-5 fieldset{border: none;}.form-style-5 legend {font-size: 1.4em;margin-bottom: 10px;}.form-style-5 label {display: block;margin-bottom: 8px;}.form-style-5 input[type="text"], .form-style-5 input[type="date"], .form-style-5 input[type="datetime"], .form-style-5 input[type="email"], .form-style-5 input[type="number"], .form-style-5 input[type="search"], .form-style-5 input[type="time"], .form-style-5 input[type="url"], .form-style-5 input[type="password"], .form-style-5 textarea, .form-style-5 select {border: none;border-radius: 4px;font-size: 15px;margin: 0;outline: 0;padding: 10px;width: 100%;box-sizing: border-box;-webkit-box-sizing: border-box;-moz-box-sizing: border-box;background-color: #e8eeef;color:#8a97a0;-webkit-box-shadow: 0 1px 0 rgba(0,0,0,0.03) inset;-moz-box-shadow: 0 1px 0 rgba(0,0,0,0.03) inset;box-shadow: 0 1px 0 rgba(0,0,0,0.03) inset;margin-bottom: 30px;}.form-style-5 input[type="text"]:focus, .form-style-5 input[type="date"]:focus, .form-style-5 input[type="datetime"]:focus, .form-style-5 input[type="email"]:focus, .form-style-5 input[type="number"]:focus, .form-style-5 input[type="search"]:focus, .form-style-5 input[type="time"]:focus, .form-style-5 input[type="url"]:focus, .form-style-5 input[type="password"]:focus, .form-style-5 textarea:focus, .form-style-5 select:focus{background: #d2d9dd;}.form-style-5 select{-webkit-appearance: menulist-button;-moz-appearance: menulist-button;height:35px;}.form-style-5 .section_titles {background: #1abc9c;color: #fff;height: 30px;display: inline-block;font-size: 0.8em;margin-right: 4px;line-height: 30px;text-align: center;text-shadow: 0 1px 0 rgba(255,255,255,0.2);border-radius: 5px 5px 5px 5px;}.form-style-5 input[type="submit"], .form-style-5 input[type="button"] {position: relative;display: block;padding: 19px 39px 18px 39px;color: #FFF;margin: 0 auto;background: #DC9A39;font-size: 18px;text-align: center;font-style: normal;width: 100%;margin-bottom: 10px;border: none;border-radius: 5px 5px 5px 5px;}.form-style-5 input[type="submit"]:hover, .form-style-5 input[type="button"]:hover {background: #ba8536;}'
                    html_style = '<style>.scanButton{{font-size: 18px; border: none; text-align: center; background: #DC9A39; color: #fff; height: 30px; width: 110px; display: inline-block; margin-right: 4px; line-height: 0px; text-align: center; text-shadow: 0 1px 0 rgba(255,255,255,0.2); border-radius: 5px 5px 5px 5px;}}.scanButton:hover span {{display:none;}}.scanButton:hover:before {{content:"{0}";}}.scanButton:hover {{background-color: #ba8536;}}.dhcpButton {{font-size: 18px; border: none; text-align: center; background: #DC9A39; color: #fff; height: 30px; width: 80px; display: inline-block; margin-right: 4px; line-height: 0px; text-align: center; text-shadow: 0 1px 0 rgba(255,255,255,0.2); border-radius: 5px 5px 5px 5px;}}.dhcpButton:hover span {{display:none;}}.dhcpButton:hover:before {{content:"{1}";}} .dhcpButton:hover {{background-color: #ba8536;}}{2}</style>'.format(
                        language_dictionary_html["Scan"],
                        language_dictionary_html[style_content],
                        html_static_style
                    )
                    html_head_end = '</head>'
                    html_body = '<body><main><section class="tab" id="third-tab"><nav><a href="#first-tab">{0}</a><a href="#second-tab">{1}</a><a href="#third-tab" class="active">{2}</a></nav><div class="tab-box"><div class="form-style-5"><form action="/test-connection#third-tab" method="GET"><fieldset><input type="hidden" name="refresh_third_tab" value="True"/><textarea rows="4" style="white-space: pre; overflow: scroll; resize: vertical;" wrap="off" name="test_connection_output" disabled>{15}</textarea><br><br><label for="mqtt_address" style="font-size:20px">MQTT URL/IP:</label><input type="text" id="mqtt_address" name="mqtt_address" minlength="1" maxlength="2048" value="{17}" required>{18}<br><br><input type="submit" value="{16}" /></fieldset></form></div></div></section><section class="tab" id="second-tab"><nav><a href="#first-tab">{0}</a><a href="#second-tab" class="active">{1}</a><a href="#third-tab">{2}</a></nav><div class="tab-box"><div class="form-style-5"><form action="/#second-tab" method="GET"><fieldset><legend><input type="hidden" name="refresh_second_tab" value="True"/><button class="scanButton"><span>{1}</span></button></legend><textarea rows="3" style="white-space: pre; overflow: scroll; resize: vertical; width: 100%;" wrap="off" name="scanned_sensors" disabled>{8}</textarea></form><form action="/sensor-apply#second-tab" method="GET"><label for="take_reading" style="font-size:20px">{9}:</label><input type="number" min="0" max="31536000000" name="record_every_int" style="width:135px;text-align:right;direction: rtl;height:38px;"value="{13}" required><select id="take_reading" name="record_every_min_hr" style="width:120px;text-align:left;height:38px;"><option value="minutes">{11}</option><option value="hours">{12}</option></select><br><label for="send_reading" style="font-size:20px">{10}:</label><input type="number" min="0" max="31536000000" name="send_every_int" style="width:135px;text-align:right;direction: rtl;height:38px;" value="{14}" required><select id="send_reading" name="send_every_min_hr" style="width:120px;text-align:left;height:38px;"><option value="minutes">{11}</option><option value="hours">{12}</option></select><br><br><input type="submit" value="{6}" /></fieldset></form></div></div></section><section class="tab" id="first-tab"><nav><a href="#first-tab" class="active">{0}</a><a href="#second-tab">{1}</a><a href="#third-tab">{2}</a></nav><div class="tab-box"><div class="form-style-5"><form action="/{7}#first-tab" method="GET"><fieldset><legend><input type="hidden" name="scan" value="True"/><button class="scanButton"><span>{3}</span></button></legend><textarea rows="4" style="white-space: pre; overflow: scroll; resize: vertical;" wrap="off" name="scanned_networks" disabled>{4}</textarea></form>{5}<br><br><input type="submit" value="{6}" /></fieldset></form></div></div></section></main></body>'.format(
                        language_dictionary_html["WiFi"],  # {0}
                        language_dictionary_html["Sensor"],  # {1}
                        language_dictionary_html["Data"],  # {2}
                        language_dictionary_html["Network"],  # {3}
                        found_networks_html,  # {4}
                        html_content_wifi,  # {5}
                        language_dictionary_html["Apply"],  # {6}
                        file_request,   # {7}
                        sensor_info_html,  # {8}
                        language_dictionary_html["Take_Reading_Every"],  # {9}
                        language_dictionary_html["Send_Readings_Every"],  # {10}
                        language_dictionary_html["Minutes"],  # {11}
                        language_dictionary_html["Hours"],  # {12}
                        int(wifi_settings_dictionary['record_data_interval_ms'] / 60000),  # {13}
                        wifi_settings_dictionary['send_data_interval_min'],  # {14}
                        html_content_data,  # {15}
                        language_dictionary_html["Test_Connection"],  # {16}
                        wifi_settings_dictionary['mqtt_url'],  # {17}
                        html_content_data_extra_settings  # {18}
                    )
                    html_end = '</html>'
                    response = '{0}{1}{2}{3}{4}{5}{6}'.format(
                        html_start,  # {0}
                        html_lang,  # {1}
                        html_head_start,  # {2}
                        html_style,  # {3}
                        html_head_end,  # {4}
                        html_body,  # {5}
                        html_end  # {6}
                    )

                else:
                    try:
                        file = open(file_request, 'rb')  # open file , r => read , b => byte format
                        response = file.read()
                        file.close()

                        if file_request.endswith(".html"):
                            mimetype = 'text/html'
                        elif file_request.endswith(".svg"):
                            mimetype = 'image/svg+xml'
                        elif file_request.endswith(".css"):
                            mimetype = 'text/css'
                        else:
                            mimetype = 'application/octet-stream'

                        header = 'HTTP/1.1 200 OK\nContent-Type: {0}\nConnection: close\n\n'.format(mimetype)

                    except Exception as e:
                        header = 'HTTP/1.1 404 Not Found\nContent-Type: text/html\nConnection: close\n\n'
                        response = '<!DOCTYPE html><html lang=en><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1"><title>NFS</title><meta name="noflippingswitches" content="NFS"></head><center><h3>Error 404: File {0} not found</h3><p>{1}</p></center></body></html>'.format(file_request, e)

            else:
                # Unable to load language_dictionary_html
                header = 'HTTP/1.1 500 Internal Server Error\nContent-Type: text/html\nConnection: close\n\n'
                response = '<!DOCTYPE html><html lang=en><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1"><title>NFS</title><meta name="noflippingswitches" content="NFS"></head><body><center><h3>Error 500: Unable to load a language_dictionary_html</h3></center></body></html>'

            connection.send(header)
            connection.sendall(response)
            connection.close()
            # garbage collection after serving each page
            gc.collect()

            # Things to_do after serving page
            if 'scan' in param_request_dictionary:
                first_tab_access_point_machine_reset = True
            elif first_tab_access_point_machine_reset:
                machine.reset()

            if 'refresh_third_tab' in param_request_dictionary:
                third_tab_access_point_machine_reset = True
            elif third_tab_access_point_machine_reset:
                machine.reset()

        except Exception as e:
            print('Error: {0}'.format(e))
