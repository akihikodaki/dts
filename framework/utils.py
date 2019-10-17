# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import json         # json format
import re
import os
import inspect
import socket
import struct
import threading
import types
from functools import wraps

DTS_ENV_PAT = r"DTS_*"

def create_parallel_locks(num_duts):
    """
    Create thread lock dictionary based on DUTs number
    """
    global locks_info
    locks_info = []
    for _ in range(num_duts):
        lock_info = dict()
        lock_info['update_lock'] = threading.RLock()
        locks_info.append(lock_info)


def parallel_lock(num=1):
    """
    Wrapper function for protect parallel threads, allow multiple threads
    share one lock. Locks are created based on function name. Thread locks are
    separated between duts according to argument 'dut_id'.
    Parameter:
        num: Number of parallel threads for the lock
    """
    global locks_info

    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'dut_id' in kwargs:
                dut_id = kwargs['dut_id']
            else:
                dut_id = 0

            # in case function arguments is not correct
            if dut_id >= len(locks_info):
                dut_id = 0

            lock_info = locks_info[dut_id]
            uplock = lock_info['update_lock']

            name = func.__name__
            uplock.acquire()

            if name not in lock_info:
                lock_info[name] = dict()
                lock_info[name]['lock'] = threading.RLock()
                lock_info[name]['current_thread'] = 1
            else:
                lock_info[name]['current_thread'] += 1

            lock = lock_info[name]['lock']

            # make sure when owned global lock, should also own update lock
            if lock_info[name]['current_thread'] >= num:
                if lock._is_owned():
                    print RED("DUT%d %s waiting for func lock %s" % (dut_id,
                              threading.current_thread().name, func.__name__))
                lock.acquire()
            else:
                uplock.release()

            try:
                ret = func(*args, **kwargs)
            except Exception as e:
                if not uplock._is_owned():
                    uplock.acquire()

                if lock._is_owned():
                    lock.release()
                    lock_info[name]['current_thread'] = 0
                uplock.release()
                raise e

            if not uplock._is_owned():
                uplock.acquire()

            if lock._is_owned():
                lock.release()
                lock_info[name]['current_thread'] = 0

            uplock.release()

            return ret
        return wrapper
    return decorate


def RED(text):
    return "\x1B[" + "31;1m" + str(text) + "\x1B[" + "0m"


def BLUE(text):
    return "\x1B[" + "36;1m" + str(text) + "\x1B[" + "0m"


def GREEN(text):
    return "\x1B[" + "32;1m" + str(text) + "\x1B[" + "0m"


def pprint(some_dict, serialzer=None):
    """
    Print JSON format dictionary object.
    """
    return json.dumps(some_dict, sort_keys=True, indent=4, default=serialzer)


def regexp(s, to_match, allString=False):
    """
    Ensure that the re `to_match' only has one group in it.
    """

    scanner = re.compile(to_match, re.DOTALL)
    if allString:
        return scanner.findall(s)
    m = scanner.search(s)
    if m is None:
        print RED("Failed to match " + to_match + " in the string " + s)
        return None
    return m.group(1)


def get_obj_funcs(obj, func_name_regex):
    """
    Return function list which name matched regex.
    """
    for func_name in dir(obj):
        func = getattr(obj, func_name)
        if callable(func) and re.match(func_name_regex, func.__name__):
            yield func


@parallel_lock()
def remove_old_rsa_key(crb, ip):
    """
    Remove the old RSA key of specified IP on crb.
    """
    rsa_key_path = "~/.ssh/known_hosts"
    remove_rsa_key_cmd = "sed -i '/%s/d' %s" % (ip, rsa_key_path)
    crb.send_expect(remove_rsa_key_cmd, "# ")


def human_read_number(num):
    if num > 1000000:
        num /= 1000000
        return str(num) + "M"
    elif num > 1000:
        num /= 1000
        return str(num) + "K"
    else:
        return str(num)


def get_subclasses(module, clazz):
    """
    Get module attribute name and attribute.
    """
    for subclazz_name, subclazz in inspect.getmembers(module):
        if hasattr(subclazz, '__bases__') and subclazz.__bases__ and clazz in subclazz.__bases__:
            yield (subclazz_name, subclazz)


def copy_instance_attr(from_inst, to_inst):
    for key in from_inst.__dict__.keys():
        to_inst.__dict__[key] = from_inst.__dict__[key]


def create_mask(indexes):
    """
    Convert index to hex mask.
    """
    val = 0
    for index in indexes:
        val |= 1 << int(index)

    return hex(val).rstrip("L")

def convert_int2ip(value, ip_type=4):
    '''
    @change:
    2019.0403 set default value
    '''
    if ip_type == 4:
        ip_str = socket.inet_ntop(socket.AF_INET, struct.pack('!I', value))
    else:
        h = value >> 64
        l = value & ((1 << 64) - 1)
        ip_str = socket.inet_ntop(socket.AF_INET6, struct.pack('!QQ', h, l))

    return ip_str

def convert_ip2int(ip_str, ip_type=4):
    '''
    @change:
    2019.0403 set default value
    '''
    if ip_type == 4:
        ip_val = struct.unpack("!I", socket.inet_aton(ip_str))[0]
    else:
        _hex = socket.inet_pton(socket.AF_INET6, ip_str)
        h, l = struct.unpack('!QQ', _hex)
        ip_val = (h << 64) | l

    return ip_val

def convert_mac2long(mac_str):
    """
    convert the MAC type from the string into the int.
    """
    mac_hex = '0x'
    for mac_part in mac_str.lower().split(':'):
        mac_hex += mac_part
    ret  = long(mac_hex, 16)
    return ret

def convert_mac2str(mac_long):
    """
    convert the MAC type from the int into the string.
    """
    mac = hex(mac_long)[2:-1].zfill(12)
    b = []
    [b.append(mac[n:n+2]) for n in range(len(mac)) if n % 2 == 0 ]
    new_mac = ":".join(b)
    return new_mac

def get_backtrace_object(file_name, obj_name):
    import inspect
    frame = inspect.currentframe()
    obj = None
    found = False
    while frame:
        file_path = inspect.getsourcefile(frame)
        call_file = file_path.split(os.sep)[-1]
        if file_name == call_file:
            found = True
            break

        frame = frame.f_back

    if found:
        obj = getattr(frame.f_locals['self'], obj_name, None)

    return obj
