# -*- coding: utf-8 -*-
"""
keith2400_logic directs a Keithley 2400 to perform IV measurements and save.

methods_
    general_input(str, opt type, opt float/int, opt float/int, opt list,
                  opt object)
    match(str, str)
    test_inclusion(obj, list)
    get_out_type(str)
    write_visa(str, str)
    set_gpib(opt int)
    check_connected(int)
    set_output_type(opt str)
    set_output_range(opt float/int/str)
    set_output_autorange(opt bool)
    set_output_val(opt float/int)
    set_measure_type(opt str, opt bool)
    set_compliance(opt float/int)
    set_measure_range(opt str/int/float)
    set_measure_autorange(opt bool)
    set_delay(opt str/int/float)
    set_ohm_meas_type(opt str/int)
    set_measure_speed(opt float/int)
    set_num_points(opt int)
    set_sweep_output(opt bool, opt str, opt bool)
    set_sweep_type(opt str, opt bool)
    set_sweep_range(opt str, opt bool)
    set_sweep_start(opt int/float, opt bool)
    set_sweep_stop(opt int/float, opt int/float, opt bool)
    set_sweep_points(opt int, opt bool)
    set_sweep_list(opt list/tuple, opt bool)
    set_sweep(opt bool, opt str, opt str, opt str/float, opt float, opt float,
              opt int, opt list, opt bool)
    list_params(opt bool)
    check_parameters()
    set_format()
    make_header(list)
    set_all_to_globals()
    save_as()
    save_data(list/str, opt bool)
    process_data(list/str, int, opt str, opt str, opt bool)
    clear_data()
    start(opt bool, opt bool)
    stop()

@author: Sarh Friedensen
"""
# from IPython import get_ipython
# get_ipython().magic('reset -sf')

import visa
import easygui as gui
import pprint
from distutils.util import strtobool
from typing import Union, Optional

a = 'auto'
c = 'current'
r = 'resistance'
v = 'voltage'

fa1 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/A_02_discharge_vac.txt')
fa2 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/A_02_charge_vac.txt')
fb1 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/B_01_discharge_vac.txt')
fb2 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/B_01_charge_vac.txt')
fc1 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/C_01_discharge_vac.txt')
fc2 = ('G:/.shortcut-targets-by-id/128cjRwD6Qd8fhTyYFHrkDuYwwpdMwzjZ/'
       'Project Pinpoint/Testing/20200513'
       '/C_01_charge_vac.txt')

rm = visa.ResourceManager()

keith = None
filename = None
address = 25
out_type = None
meas_type = None
delay = None
out_val = {'VOLT': None,
           'CURR': None}
compl = {'VOLT': None,  # Compliance for voltage measurements
         'CURR': None}  # Compliance for current measurements
out_rng = {'VOLT': None,
           'CURR': None}
meas_rng = {'VOLT': None,
            'CURR': None,
            'RES': None}
ohm_meas_type = 'Four'
meas_speed = {'VOLT': None,
              'CURR': None,
              'RES': None}
max_out = {'VOLT': 200,
           'CURR': 1}
num_points = None
sweep_params = {'Enabled': False,
                'Type': None,
                'Output': None,
                'Ranging': None,
                'Start': None,
                'Stop': None,
                'Points': None,
                'List': None}
data = []
header = ''
format_ = ''


def general_input(prompt: str, type_: Optional[type] = None,
                  min_: Optional[Union[int, float]] = None,
                  max_: Optional[Union[int, float]] = None,
                  choices: Optional[Union[list, tuple]] = None, esc=None):
    """Prompt the user for input.

    Can request a specific input type, min and max values, options to choose
    from (with wildcard and case insensitive), and an escape sequence.
    """
    print(type_)
    if min_ is not None and max_ is not None and max_ < min_:
        raise ValueError('min_ must be less than or equal to max_.')
    while True:
        val = input(prompt)
        if (val == esc or val is None or val == ''):
            print('Escape used; no value assigned.')
            return None
        elif type_ is not None:
            if type(val) is list and type_ is not list:
                val = val[0]
            try:
                if type_ is bool:
                    val = strtobool(val)
                if type_ in (list, tuple):
                    delimiter = (', ' if ', ' in val else ',' if ',' in val
                                 else ' ')
                    val = val.split(delimiter)
                else:
                    val = type_(val)
            except ValueError:
                print(f'Input type must be {type_}.')
                continue
        if max_ is not None and val > max_:
            raise ValueError(f'Inupt must be less than or equal to {max_}.')
        elif min_ is not None and val < min_:
            raise ValueError(f'Input must be greater than or equal to {min_}.')
        elif choices is None:
            return val
        elif choices is not None and not test_inclusion(val, choices):
            raise ValueError(f'Input must be chosen from among {choices}.')
        else:
            return val


def match(first: str, second: str):
    """Test whether two string inputs are the same, up to case and wildcard."""
    assert type(first) is str and type(second) is str, 'inputs are not strings'
    first = first.upper()
    second = second.upper()
    if len(first) == 0 and len(second) == 0:
        return True
    if len(first) > 1 and first[0] == '*' and len(second) == 0:
        return False
    if (len(first) != 0 and len(second) != 0 and first[0] == second[0]):
        return match(first[1:], second[1:])
    if len(first) != 0 and first[0] == '*':
        return match(first[1:], second) or match(first, second[1:])
    return False


def test_inclusion(element, list_: list):
    """Test whether an element is part of a list, up to wildcard and case."""
    if element is not None:
        return True in [match(x, element) for x in list_]
    else:
        return False


def get_out_type(string: str):
    """Return SCPI representation of voltage, current, or resistance."""
    string = str(string)[0].upper()
    return ('VOLT' if 'V' in string else ('CURR' if 'C' in string
            else ('RES' if 'R' in string else 'ERR')))


def write_visa(cmd: str, query: str):
    """Try to write a command to the instrument and return a query about it."""
    global keith
    try:
        keith.write(cmd)
    except AttributeError:
        print('Instrument is not connected--cannot set parameter')
        return None
    else:
        return keith.query(query)


def set_gpib(gpib: Optional[int] = None):
    """Set GPIB address of the instrument."""
    if type(gpib) is not int or gpib not in list(range(1, 30)):
        prompt = 'Specify the GPIB address of the instrument.'
        gpib = general_input(prompt=prompt, type_=int, min_=1, max_=30, esc=0)
    if gpib is not None:
        check_connected(gpib)


def check_connected(gpib: int):
    """See if instrument connected at GPIB address and open comunication."""
    global keith
    global address
    inst_list = [x for x in rm.list_resources() if (str(gpib) in x
                                                    and 'GPIB' in x)]
    try:
        keith = rm.open_resource(inst_list[0], read_termination='\n',
                                 write_termination='\n')
    except IndexError:
        keith = None
        address = None
        print(f'Instrument is not connected at address {gpib}.')
    else:
        address = gpib
#        keith.read_termination = '\n'
#        keith.write_termination = '\n'
        keith.write(':SOUR:CLE:AUTO ON; :OUTP:SMOD HIMP; :SYST:RSEN OFF;')
        keith.timeout = None


def set_output_type(type_str: Optional[str] = None):
    """Set whether instrument acts as a voltage or current source."""
    global out_type
    choices = ['volt*', 'cur*']
    if not test_inclusion(type_str, choices):
        prompt = "Specify whether you wish to source voltage or current."
        type_str = general_input(prompt=prompt, type_=str, choices=choices)
    if test_inclusion(type_str, choices):
        cmd = (f'SOUR:FUNC {get_out_type(type_str)};')
        out_type = get_out_type(write_visa(cmd, 'SOUR:FUNC?'))


def set_output_range(val=None):
    """Set the instrument range for its output."""
    global out_type
    global out_rng
    out = get_out_type(out_type)
    if out == 'ERR':
        print('Output type not specified.')
        return
    if val is not None and match('auto*', str(val)):
        set_output_autorange(True)
        return
    (sort, unit) = (('voltage', 'volts') if out == 'VOLT'
                    else ('current', 'amps'))
    prompt = f'Enter your max {sort} output in {unit} (as float).'
    max_ = 200 if out == 'VOLT' else 1
    cond = type(val) in (float, int) and 0 < val <= max_
    if val is None or not cond:
        val = general_input(prompt=prompt, type_=float, max_=max_, min_=0)
    cmd = f'SOUR:{out}:RANG {val};'
    if val is not None:
        out_rng[out] = write_visa(cmd, f':SOUR:{out}:RANG?')


def set_output_autorange(enable: Optional[bool] = None):
    """Enable or disable autorange for the instrument output."""
    global out_type
    global out_rng
    out = get_out_type(out_type)
    if out == 'ERR':
        print('Output type not specified.')
        return
    if enable is None or type(enable) is not bool:
        prompt = 'Would you like to enable autorange? Answer True or False.'
        enable = general_input(prompt=prompt, type_=bool)
    if enable is not None:
        state = 'ON' if enable else 'OFF'
        cmd = f'SOUR:{out}:RANG:AUTO {state};'
        enable = write_visa(cmd, f'SOUR:{out}:RANG:AUTO?')
        if enable is not None:
            out_rng[out] = 'AUTO' if strtobool(enable) else out_rng[out]


def set_output_val(val: Optional[Union[int, float]] = None):
    """Set fixed output level for voltage (V) or current (A) for instrument."""
    global out_val
    global out_type
    global max_out
    out = get_out_type(out_type)
    if out == 'ERR':
        print('Please specify an output type before setting an output value.')
        return
    max_ = max_out[out]
    if val is None:
        unit = f'{"V" if match(out, "volt") else "A"}'
        prompt = f"Specify the output value ({unit})."
        val = general_input(prompt=prompt, type_=float, min_=-max_, max_=max_)
    if val is not None:
        print(val)
        cmd = (f"SOUR:{out}:MODE FIX; :SOUR:{out} "
               + f"{0 if abs(val) > max_ else val};")
        out_val[out] = write_visa(cmd, f'SOUR:{out}?')


def set_measure_type(type_str: Optional[str] = None,
                     four_wire: Optional[bool] = None):
    """Set whether instrument will measure current, voltage, or resistance."""
    global meas_type
    global out_type
    choices = ['volt*', 'curr*', 'res*']
    if not test_inclusion(type_str, choices):
        prompt = ('Specify which parameter you would like to measure (current,'
                  + ' voltage, or resistance).')
        type_str = general_input(prompt=prompt, type_=str, choices=choices)
    if out_type is None:
        set_output_type()
    if test_inclusion(type_str, choices) and out_type is not None:
        meas = get_out_type(type_str)
        out = get_out_type(out_type)
        meas_type = meas
        cmd = ('SENS:FUNC:CONC ON; :SENS:FUNC:OFF:ALL; '
               + f':SENS:FUNC "{meas}", "{out}"')
        cmd += '; :SYST:RSEN ' + ('OFF;' if (four_wire is False or meas != out)
                                  else 'ON;')
        if meas == 'RES':
            # Set resistance auto-sourcing and output compensation on.
            # If doing manual resistance measurement, will need to set
            # voltage and current compliance.
            cmd += '; :SENS:RES:MODE AUTO; OCOM ON;'
        out_val[out] = write_visa(cmd, f'SOUR:{out}?')


def set_compliance(val=None):
    """Set compliance value for either a voltage or current measurement."""
    global out_type
    global meas_type
    global meas_rng
    global compl
    out = get_out_type(out_type)
    meas = get_out_type(meas_type)
    if out == 'ERR':
        print('Output type not specified.')
        return
    if out == 'VOLT':
        max_ = 1.05
        min_ = 1e-9
        if val is None or type(val) not in (float, int):
            prompt = 'Enter your current compliance value in amps (as float).'
            val = general_input(prompt=prompt, type_=float, min_=min_,
                                max_=max_)
        else:
            val = (max_ if val > max_ else min_ if val < min_ else val)
    elif out == 'CURR':
        max_ = 210
        min_ = 200e-6
        if val is None or type(val) not in (float, int):
            prompt = 'Enter your voltage compliance value in volts (as float).'
            max_ = meas_rng['VOLT']
            val = general_input(prompt=prompt, type_=float, min_=min_,
                                max_=max_)
        else:
            val = (max_ if val > max_ else min_ if val < min_ else val)
    cmd = f'SENS:{meas}:PROT {val};'
    if val is not None:
        compl[out] = write_visa(cmd, f'SENS:{meas}:PROT?')


def set_measure_range(val=None):
    """Set the measurement range for the instrument."""
    global meas_type
    global meas_rng
    meas = get_out_type(meas_type)
    if meas == 'ERR':
        print('Measurement type not specified.')
        return
    if match('auto*', str(val)):
        set_measure_autorange(True)
        return
    max_ = 200 if meas == 'VOLT' else 1 if meas == 'CURR' else 200e6
    min_ = 0 if (meas == 'VOLT' or 'CURR') else 20
    cond = type(val) in (float, int) and min_ <= val <= max_
    if val is None or not cond:
        (sort, unit) = (('voltage', 'volts') if meas == 'VOLT'
                        else ('current', 'amps') if meas == 'CURR'
                        else ('resistance', 'ohms'))
        prompt = f'Enter your {sort} measurement range in {unit} (as float).'
        val = general_input(prompt=prompt, type_=float, min_=min_, max_=max_)
    if val is not None:
        cmd = f':SENS:{meas}:RANG {val};'
        meas_rng[meas] = write_visa(cmd, f'SENS:{meas}:RANG?')


def set_measure_autorange(enable: Optional[bool] = None):
    """Enable or disable autorange for measurement."""
    global meas_type
    global meas_rng
    meas = get_out_type(meas_type)
    if meas == 'ERR':
        print('Measurement type not specified.')
        return
    if enable is None or type(enable) is not bool:
        prompt = 'Would you like to enable autorange? Answer True or False.'
        enable = general_input(prompt=prompt, type_=bool)
    if enable is not None:
        state = 'ON' if enable else 'OFF'
        cmd = f'SENS:{meas}:RANG:AUTO {state};'
        enable = write_visa(cmd, f'SENS:{meas}:RANG:AUTO?')
        if enable is not None:
            meas_rng[meas] = 'AUTO' if strtobool(enable) else meas_rng[meas]


def set_delay(val=None):
    """Set delay time between change in output value and next measurement."""
    global delay
    min_ = 0.0
    max_ = 9999.999
    cond = (match('auto*', str(val))
            or ((type(val) in (float, int)) and (min_ <= val <= max_)))
    if val is None or not cond:
        prompt = 'Enable auto source delay? Answer True or False.'
        val = bool(general_input(prompt=prompt, type_=bool))
        if not val:
            prompt = 'Enter desired source delay in seconds (as float).'
            val = general_input(prompt=prompt, type_=float, min_=min_,
                                max_=max_)
    if val is not None:
        auto = ('ON' if (str(val) == 'True' or match('auto*', str(val)))
                else 'OFF')
        cmd = (f'SOUR:DEL:AUTO {auto};'
               + (f' :SOUR:DEL {val};' if auto == 'OFF' else ''))
        delay = write_visa(cmd, f'SOUR:DEL?')
        if write_visa('', 'SOUR:DEL:AUTO?') == '1':
            #  keith.query('SOUR:DEL:AUTO?') == '1':
            delay = 'AUTO'


def set_ohm_meas_type(type_str: Optional[Union[str, int]] = None):
    """Set the type of resistance measurement to perform."""
    global ohm_meas_type
    if type(type_str) is int:
        type_str = str(type_str)
    choices = ['two*', '2*', 'four*', '4*', 'six*', '6*']
    if not test_inclusion(type_str, choices):
        prompt = ('What type of resistance measurement (two-, four-, or '
                  'six-wire) would you like to perform?')
        type_str = general_input(prompt=prompt, type_=str, choices=choices)
    if test_inclusion(type_str, choices):
        meas_type = ('Two' if test_inclusion(type_str, ['two*', '2*'])
                     else 'Four' if test_inclusion(type_str, ['fo*', '4*'])
                     else 'Six')
        mode = 'ON' if (meas_type == 'Four' or 'Six') else 'OFF'
        cmd = f'SYST:RSEN {mode};'
        if meas_type == 'Six':
            cmd += '; :SYST:GUAR OHMS;'
        result = write_visa(cmd, 'SYST:RSEN?')
        if result is not None:
            ohm_meas_type = meas_type


def set_measure_speed(val=None):
    """Set the measurement integration time for the instrument in PLC."""
    global meas_type
    global meas_speed
    meas = get_out_type(meas_type)
    max_ = 10
    min_ = 0.01
    if meas == 'ERR':
        print('Measurement type not specified.')
        return
    cond = type(val) in (float, int) and min_ <= val <= max_
    if val is None or not cond:
        prompt = 'What is your desired integration time in power line cycles?'
        val = general_input(prompt=prompt, type_=float, max_=max_, min_=min_)
    if val is not None:
        cmd = f'SENS:{meas}:NPLC {val};'
        meas_speed[meas] = write_visa(cmd, f'SENS:{meas}:NPLC?')


def set_num_points(val: Optional[int] = None):
    """Set the number of points to measure and set up buffer."""
    global num_points
    max_ = 2500
    min_ = 0
    if type(val) is not int or val not in list(range(min_, max_+1)):
        prompt = 'How many measurements would you like to take?'
        val = general_input(prompt=prompt, type_=int, min_=min_, max_=max_)
    if type(val) is int:
        cmd = (f':TRAC:FEED:CONT NEV; :TRAC:CLE; POIN {val}; FEED SENS; '
               + ':TRAC:TST:FORM ABS; :TRAC:FEED:CONT NEXT; '
               + f':ARM:SEQ:COUN 1; :TRIG:COUN {val};')
        num_points = write_visa(cmd, ':TRAC:POIN?')


def set_sweep_output(on: Optional[bool] = None, outpt: Optional[str] = None,
                     write: bool = False):
    """Enable or disable sweeping, and if enabled, specify output type."""
    global sweep_params
    if on not in (True, False):
        prompt = 'Would you like to enable a sweep?'
        on = bool(general_input(prompt=prompt, type_=bool))
    choices = ['volt*', 'curr*']
    if not test_inclusion(outpt, choices) and on:
        prompt = 'Would you like to configure the current or voltage source?'
        outpt = get_out_type(general_input(
                    prompt=prompt, type_=str, choices=choices))
    if test_inclusion(outpt, choices) and on:
        cmd = f':SOUR:{outpt}:MODE {"SWE" if on else "FIX"}'
        query = f':SOUR:{outpt}:MODE?'
        if write:
            resp = write_visa(cmd, query)
            sweep_params['Enabled'] = test_inclusion(resp, ['SWE', 'LIST'])
            sweep_params['Output'] = outpt
            return (outpt, cmd, query)
        else:
            return (outpt, cmd, query)
    else:
        print('No output mode given. Configuration terminated.')
        return None


def set_sweep_type(sw_type: Optional[str] = None, write: bool = False):
    """Set the type of sweep to perform."""
    global sweep_params
    choices = ['lin*', 'log*', 'list*']
    out = sweep_params["Output"]
    if out is None:
        print("Please specify an output type (voltage or current) before "
              + "setting a sweep type.")
        return None
    if not sweep_params["Enabled"]:
        print("Sweep is not enabled, so cannot configure sweep type.")
        return None
    if not test_inclusion(sw_type, choices):
        prompt = ('Would you like to configure a linear, logarithmic, or '
                  + 'custom sweep?')
        sw = general_input(prompt=prompt, type_=str, choices=choices)
    if test_inclusion(sw, choices):
        sw_type = ('LIST' if match(sw, 'list*') else 'LIN' if
                   match(sw, 'lin*') else 'LOG')
        cmd = (f'SOUR:{out}:MODE LIST' if sw_type == 'LIST' else
               f'SOUR:SWE:SPAC {sw_type}')
        query = (f'SOUR:{out}:MODE?' if sw_type == 'LIST'
                 else 'SOUR:SWE:SPAC?')
        if write:
            sweep_params['Type'] = write_visa(cmd, query)
            return (sw_type, cmd, query)
        else:
            return (sw_type, cmd, query)
    else:
        print('Valid sweep type not provided. Configuration terminated.')
        return None


def set_sweep_range(rang: Optional[str] = None, write: bool = False):
    """Set the output range for the sweep.

    'best' will select the lowest fixed range that will encompas the sweep;
    'auto' will change the range at any changeover points; and 'fixed' will
    choose the currently selected range.
    """
    global sweep_params
    choices = ['best*', 'auto*', 'fix*']
    if not test_inclusion(rang, choices):
        prompt = 'Would you like best, fixed, or auto ranging?'
        rang = general_input(prompt=prompt, type_=str, choices=choices)
    if test_inclusion(rang, choices):
        rang = ('BEST' if match(rang, 'best*') else 'AUTO' if
                match(rang, 'auto*') else 'FIX')
        cmd = f'SOUR:SWE:RANG {rang}'
        query = 'SOUR:SWE:RANG?'
        if write:
            sweep_params['Ranging'] = write_visa(cmd, query)
            return (rang, cmd, query)
        else:
            return (rang, cmd, query)
    else:
        print('Valid range type not provided. Configuration terminated.')
        return None


def set_sweep_start(val: Optional[Union[float, int]] = None,
                    write: bool = False):
    """Set the sweep start point."""
    global sweep_params
    output = sweep_params['Output']
    upbound = max_out.get(output, 'ERR')
    if upbound == 'ERR':
        print('Please specify a sweep output type before setting bounds.')
        return
    if type(val) not in (float, int) or not -upbound <= val <= upbound:
        prompt = f'What is the start value for the sweep in {output.lower()}s?'
        val = general_input(prompt=prompt, type_=float, min_=-upbound,
                            max_=upbound)
    if val is not None:
        cmd = f':SOUR:{output}:STAR {val};'
        query = f'SOUR:{output}:STAR?'
        if write:
            sweep_params['Start'] = write_visa(cmd, query)
            return (val, cmd, query)
        else:
            return (val, cmd, query)
    else:
        print('Valid start value not provided. Configuration terminated.')
        return None


def set_sweep_stop(val: Optional[Union[int, float]] = None,
                   min_: Optional[Union[int, float]] = None,
                   write: bool = False):
    """Set the sweep stop point."""
    global sweep_params
    output = sweep_params['Output']
    upbound = max_out.get(output, 'ERR')
    min_ = -upbound if min_ is None else min_
    if upbound == 'ERR':
        print('Please specify a sweep output type before setting bounds.')
        return
    if type(val) not in (float, int) or not min_ <= val <= upbound:
        prompt = f'What is the stop value for the swep in {output.lower()}s?'
        val = general_input(prompt=prompt, type_=float, min_=min_,
                            max_=upbound)
    if val is not None:
        cmd = f'SOUR:{output}:STOP {val};'
        query = f'SOUR:{output}:STOP?'
        if write:
            sweep_params['Stop'] = write_visa(cmd, query)
            return (val, cmd, query)
        else:
            return (val, cmd, query)
    else:
        print('Valid stop value not provided. Configuration terminated.')
        return None


def set_sweep_points(num: Optional[int] = None, write: bool = False):
    """Set the number of points in the sweep."""
    global sweep_params
    if type(num) is not int or num not in range(1, 2501):
        prompt = 'How many measurement points are there in the sweep?'
        num = general_input(prompt=prompt, type_=int, min_=1, max_=2500)
    if num is not None:
        cmd = f':SOUR:SWE:POIN {num}; :TRIG:COUN {num}'
        query = 'SOUR:SWE:POIN?'
        if write:
            sweep_params['Points'] = write_visa(cmd, query)
            set_num_points(int(sweep_params['Points']))
            return (num, cmd, query)
        else:
            return (num, cmd, query)
    else:
        print('Valid number of points not given. Configuration terminated.')
        return None


def set_sweep_list(list_: Optional[Union[list, tuple]] = None,
                   write: bool = False):
    """Set the output list for a custom sweep and update number of points."""
    global sweep_params
    if type(list_) not in (list, tuple):
        prompt = 'Enter the list of values you would like to source in V or A.'
        list_ = general_input(prompt=prompt, type_=list)
    if list_ is not None:
        text = ', '.join(str(e) for e in list_)
        cmd = f'SOUR:LIST:{sweep_params["Output"]} ' + text
        query = f':SOUR:LIST:{sweep_params["Output"]}?'
        if write:
            sweep_params['List'] = write_visa(cmd, query)
            set_sweep_points(num=len(list_), write=True)
            return (list_, cmd, query)
        else:
            return (list_, cmd, query)
    else:
        print('Valid list not given. Configuration terminated.')
        return None


def set_sweep(on=None, outpt=None, sw_type=None, rang=None, start=None,
              stop=None, points=None, list_=None, useparams: bool = False):
    """Configure all parts of the sweep in sequence.

    if useparams is True, use the sweep_params dictionary to set the values.
    """
    global sweep_params
    on = sweep_params["Enabled"] if useparams else on
    outpt = sweep_params["Output"] if useparams else outpt
    sw_type = sweep_params['Type'] if useparams else sw_type
    rang = sweep_params['Ranging'] if useparams else rang
    start = sweep_params['Start'] if useparams else start
    stop = sweep_params['Stop'] if useparams else stop
    points = sweep_params['Points'] if useparams else points
    list_ = sweep_params['List'] if useparams else list_

    out_tuple = set_sweep_output(on=on, outpt=outpt, write=True)
    if out_tuple is None or not sweep_params['Enabled']:
        return
    type_tuple = set_sweep_type(sw_type=sw_type, write=True)
    if type_tuple is None:
        return
    range_tuple = set_sweep_range(rang=rang, write=True)
    if range_tuple is None:
        return
    if not match(sw_type, 'LIST'):
        start_tuple = set_sweep_start(val=start, write=True)
        if start_tuple is None:
            return
        stop_tuple = set_sweep_stop(val=stop, min_=start_tuple[0], write=True)
        if stop_tuple is None:
            return
        points_tuple = set_sweep_points(points=points, write=True)
        if points_tuple is None:
            return
    else:
        list_tuple = set_sweep_list(list_=list_, write=True)
        if list_tuple is None:
            return


def list_params(prnt: bool = True):
    """List values of all user-defined parameters.  Useful for final check."""
    globs = globals()
    keys = list(globs.keys())
    strings = ['__', '_i', '_oh', '_dh', 'In', 'get', 'set', 'rm', 'visa',
               'unconnected', 'check', 'save', 'start', 'stop', 'exit',
               'Out', 'gui', 'match', 'general', 'make', 'quit', 'list',
               'pprint']
    remove = list(dict.fromkeys([x for x in keys for y in strings if y in x]))
    vars_ = {}
    for x, y in globs.items():
        if x not in remove:
            vars_[x] = y
    if prnt:
        pprint.pprint(vars_)
    return vars_


def check_parameters():
    """Verify that all inputs have been set within the program.

    WILL NOT catch if you change all the variables up top without calling
    set_all_to_globals(), so don't be a moron about that.
    """
    params = list_params(False)
    out = get_out_type(params['out_type'])
    meas = get_out_type(params['meas_type'])
    out_accept = (out != 'ERR' and params['out_val'][out] is not None
                  and params['out_rng'][out] is not None
                  and params['compl'][out] is not None)
    meas_accept = (meas != 'ERR' and params['meas_rng'][meas] is not None
                   and params['meas_speed'][meas] is not None
                   and (params['ohm_meas_type'] is not None if meas == 'RES'
                        else True))
    points_accept = params['num_points'] is not None
    connected = params['keith'] is not None
    accept = (out_accept and meas_accept and points_accept and connected)
    if not accept:
        error = (f'output ok = {out_accept}\n measure ok = {meas_accept}\n'
                 + f'buffer ok = {points_accept}\n '
                 + f'connection ok = {connected}.\n'
                 + 'Please ensure that all necessary parameters are set.\n')
        print(error)
    return accept


def set_format():
    """Set output format of the instrument.  Will measure its own output."""
    global out_type
    global meas_type
    global format_
    out = get_out_type(out_type)
    meas = get_out_type(meas_type)
    cmd = f'FORM:ELEM {out}, {meas}, TIME;'
    format_ = write_visa(cmd, 'FORM:ELEM?').split(',')
    make_header(format_)
    return format_


def make_header(list_: list):
    """Make a header to write to the data output file."""
    global out_type
    global header
    list_[0] = ('Voltage (V)' if match(list_[0], 'VOLT')
                else 'Current (A)' if match(list_[0], 'CURR')
                else '')
    list_[1] = ('Voltage (V)' if match(list_[1], 'VOLT')
                else 'Current (A)' if match(list_[1], 'CURR')
                else 'Resistance (ohms)' if match(list_[1], 'RES')
                else 'Time (s)' if match(list_[1], 'TIME') else '')
    header = ''
    for x in list_:
        header += (x + '\t')
    header = header[:-1]
    print(header)


def set_all_to_globals():
    """Send commands to set measurement parameters to the global variables.

    Useful if you want to load from a config file (pending) or just modify
    everything up top, run the program, and skip the prompts.
    """
    global address
    global out_type
    global meas_type
    global delay
    global out_val
    global compl
    global out_rng
    global meas_rng
    global ohm_meas_type
    global meas_speed
    global num_points
    global sweep_params
    set_gpib(address)
    set_output_type(out_type)
    set_output_range(out_rng[out_type])
    set_output_val(out_val[out_type])
    set_measure_type(meas_type)
    set_delay(delay)
    set_compliance(compl[out_type])
    set_measure_range(meas_rng[meas_type])
    if meas_type == 'RES':
        set_ohm_meas_type(ohm_meas_type)
    set_measure_speed(meas_speed[meas_type])
    if sweep_params["Enabled"]:
        set_sweep(useparams=True)
    else:
        set_num_points(num_points)
    set_format()


def save_as(name: Optional[str] = None):
    """Get a file name to save the data to.  Opens a gui window."""
    global filename
    title = 'Save data as'
    filetypes = ['*.txt', '*.csv']
    if name is not None:
        filename = name
        print(f'saved as {filename}')
    else:
        filename = gui.filesavebox(title=title, filetypes=filetypes)


def save_data(data: Union[list, str], clear_after_save: bool = True):
    """Save the data to the save file, then reset the file name if desired."""
    global filename
    global header
    if filename is None:
        save_as()
    if type(data) is list:
        data = ''.join(data)
    with open(filename, 'w+') as file:
        file.write(header + '\n')
        if data is not None:
            file.write(data)
    if clear_after_save:
        filename = None
        clear_data()


def process_data(data: Union[list, str], cols: int, indelim: str = ',',
                 outdelim: str = '\t', prnt: bool = False):
    """Take raw data from 2400 and process it into a delimited string."""
    if type(data) is str:
        data = data.split(indelim)
    items = len(data)
    data_rows = [data[j:j+cols] for j in range(0, items) if not j % cols]
    sdata_rows = [outdelim.join([str(i) for i in j]) for j in data_rows]
    data_str = '\n'.join(j for j in sdata_rows)
    data_cols = [data[j::cols] for j in range(0, cols)]
    if prnt:
        print(data_str)
    return data_str, data_cols


def clear_data(mem: int = 0):
    """Clear the data from the 2400 and recall memory settings.

    mem=0 recalls sink operation, mem=1 recalls 3.1V source operation.
    """
    if mem not in (0, 1):
        raise ValueError('mem must be 0 or 1.')
        return
    keith.write(f':outp off; abor; *cls; *RCL {mem}; :TRAC:CLE;')


def start(prnt: bool = False, cdl: bool = False):
    """Tell the instrument to begin measurement and get the data.  Maybe print.

    cdl indicates whether you would like a comma delimited file (default tab).
    """
    global data
    buff = int(keith.query(':TRAC:POIN:ACT?'))
    if buff > 0:
        print('Data points not cleared.')
        return
    accept = check_parameters()
    if accept:
        format_ = set_format()
        cols = len(format_)
        delim = ', ' if cdl else '\t'
        cmd = 'ABOR; *CLS;'
        query = ':OUTP ON; INIT:IMM; *OPC?'
        write_visa(cmd, query)
        # Wait for completeion of the sweep or user interrupt
        cmd = ':OUTP OFF; ABOR; *CLS;'
        query = ':TRAC:DATA?'
        output = write_visa(cmd, query)
        (data, data_cols) = process_data(data=output,
                                         cols=cols, outdelim=delim, prnt=False)
        save_as(filename)
        save_data(data, False)
        if prnt:
            print(data)


def stop():
    """Halt the instrument's measurement program and grab the data."""
    global data
    global format_
    cmd = 'ABOR;'
    query = ':TRAC:DATA?'
    keith.write('ABOR; *CLS;')
    # (data, data_cols) = process_data(data=write_visa(cmd, query),
    #                                  cols=len(format_, prnt=True))
    # save_data(data)


set_gpib(address)
#  Call *RCL 0 to load sink operation, speed 0.01
#  Call *RCL 1 to load source operation (3.1V), speed 0.01
# write_visa(':OUTP:SMOD HIMP', ':OUTP:SMOD?')
# keith.write('*RCL 0')  # Sink operation
# keith.write('*RCL 1')  # 3.1V source operation
set_output_type(v)
set_output_val(0)
set_output_range(a)
set_measure_type(c, False)
set_delay(0.0)
set_compliance(30e-3)
set_measure_range(a)
set_measure_speed(1)
set_num_points(2500)

filename = fc2

set_format()
