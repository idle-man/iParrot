# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import shutil
import random
import string
import re
import json


"""
Time Helper
"""

    
def today(form='%Y-%m-%d'):
    return datetime.datetime.now().strftime(form)


def days_ago(days=0, form='%Y-%m-%d'):
    return (datetime.datetime.now() - datetime.timedelta(days=days)).strftime(form)


def days_later(days=0, form='%Y-%m-%d'):
    return (datetime.datetime.now() + datetime.timedelta(days=days)).strftime(form)


def now(form='%Y-%m-%d %H:%M:%S'):
    return datetime.datetime.now().strftime(form)


def now_ms(form='%Y-%m-%d %H:%M:%S'):  # e.g. 2016-01-01 01:01:01.012
    _now = datetime.datetime.now()
    return _now.strftime(form) + '.' + "%03d" % round(float(_now.microsecond) / 1000)


def now_timestamp():  # e.g. 1451581261
    return int(round(time.time()))


def now_timestamp_ms():  # e.g. 1451581261339
    _now = datetime.datetime.now()
    return int(time.mktime(
        time.strptime(_now.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))) * 1000 + int(_now.microsecond / 1000)
    # return int(round(time.time())) * 1000 + int(datetime.datetime.now().microsecond / 1000)


def hours_ago(hours=0, form='%Y-%m-%d %H:%M:%S'):
    return (datetime.datetime.now() - datetime.timedelta(hours=hours)).strftime(form)


def hours_later(hours=0, form='%Y-%m-%d %H:%M:%S'):
    return (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime(form)


def har_time2timestamp(har_time, ms=0):
    try:
        _stamp = int(time.mktime(time.strptime(har_time.split('.')[0], "%Y-%m-%dT%H:%M:%S")))
        _ms = int(har_time.split('.')[1][:2])
    except ValueError:
        try:
            _stamp = int(time.mktime(time.strptime(har_time, "%a, %d %b %Y %H:%M:%S")))
            _ms = 0
        except ValueError:
            print("Unsupported startedDateTime format: {}".format(har_time))
            raise

    return _stamp*1000+_ms if ms else _stamp


"""
File Helper
"""


def get_file_name(file, ext=0):
    file = str(file).split('/')[-1].split('\\')[-1]
    return file if ext else file.replace(".{}".format(file.split('.')[-1]), '')


def get_file_path(file):
    return os.path.dirname(file)


def make_dir(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except OSError:
            return False

    return directory


def remove_dir(directory):
    if os.path.exists(directory):
        try:
            if os.path.isfile(directory):
                os.remove(directory)
            elif os.path.isdir(directory):
                shutil.rmtree(directory)
        except OSError:
            return False

    return directory


def remove_file(filename):
    if os.path.exists(filename):
        try:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                shutil.rmtree(filename)
        except OSError:
            return False

    return filename


def copy_file(source, target):
    try:
        if os.path.isdir(source):
            shutil.copytree(source, target)
        else:
            shutil.copy(source, target)
    except OSError:
        return False

    return target


def get_dir_folders(directory):
    if os.path.isdir(directory):
        return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    else:
        return []


def get_dir_files(directory):
    if os.path.isdir(directory):
        return ["{}/{}".format(directory, name) for name in os.listdir(directory) if os.path.isfile(os.path.join(directory, name))]
    else:
        return []


"""
Random Helper
"""


def get_random_integer(length=10, head=None, tail=None):
    """
    :param length: an integer
    :param head: to be started with
    :param tail: to be ended with
    :return: a random integer
    """
    my_str = random.randint(10 ** (length-1), 10 ** length - 1)
    if head:
        head = str(head)
        if len(head) >= length:
            return head
        my_str = int(head + str(str(my_str)[len(head):]))
    if tail:
        tail = str(tail)
        if len(tail) >= length:
            return tail
        my_str = int(str(str(my_str)[:-len(tail)]) + tail)

    return my_str


def get_random_string(length=10, simple=1, head=None, tail=None):
    """
    :param length: an integer
    :param simple:
    :param head: to be started with
    :param tail: to be ended with
    :return: a random string
    """
    if simple == 1:  # base: digits and letters
        src = str(string.digits) + string.ascii_letters
    elif simple == 2:  # on base, remove confusing letters: 0&O&o c&C I&l&1 k&K p&P s&S v&V w&W x&X z&Z
        src = 'abdefghijmnqrtuyABDEFGHJLMNQRTUY23456789'
    else:  # on base, add some special letters
        src = str(string.digits) + string.ascii_letters + '~!@#$%^&*,.-_=+'

    # in case the length is too high
    src = src * (length / len(src) + 1)

    my_str = ''.join(random.sample(src, length))

    if head:
        head = str(head)
        if len(head) >= length:
            return head
        my_str = head + str(my_str[len(head):])
    if tail:
        tail = str(tail)
        if len(tail) >= length:
            return tail
        my_str = str(my_str[:-len(tail)]) + tail

    return str(my_str)


def get_random_phone(head=None, tail=None):
    """
    :param head: to be started with
    :param tail: to be ended with
    :return: a random phone number in China
    """
    length = 11
    my_str = '1' + "".join(random.choice('3456789')) + "".join(random.choice(string.digits) for i in range(length-2))

    if head:
        head = str(head)
        if len(head) >= length:
            return head
        my_str = head + str(my_str[len(head):])
    if tail:
        tail = str(tail)
        if len(tail) >= length:
            return tail
        my_str = str(my_str[:-len(tail)]) + tail

    return my_str


"""
Dict Helper
"""


# Traverse the dictionary/list to get all key/value pairs with depth of 1
def get_all_kv_pairs(item, prefix=None, mode=1):
    """
    :param item: a dict or list, with any depth
    :param prefix: prefix of a key, used when recursive
    :param mode: 1: depth == 1, 0: extract keys of all levels
    :return: all key/value pairs with depth of 1
    """
    _pairs = {}
    if not mode and prefix:
        _pairs[prefix] = item
    if not item and prefix:
        _pairs[prefix] = item
    if isinstance(item, dict):  # A.B
        for _key, _val in item.items():
            _key = "{}.{}".format(prefix, _key) if prefix else _key
            if not mode:
                _pairs[_key] = _val
            _pairs.update(get_all_kv_pairs(item=_val, prefix=_key, mode=mode))
    elif isinstance(item, (list, set, tuple)):  # A[0]
        for i, _key in enumerate(item):
            _key = "{}[{}]".format(prefix, i) if prefix else "[{}]".format(i)
            if not mode:
                _pairs[_key] = item[i]
            _pairs.update(get_all_kv_pairs(item=item[i], prefix=_key, mode=mode))
    else:  # the end level
        if prefix:
            _pairs[prefix] = item
        else:
            _pairs[item] = ''
    return _pairs


def get_matched_keys(key, keys, fuzzy=1):
    """
    :param key: a node or a list of nodes, which would be matched with
    :param keys: a list of nodes, which would be matched
    :param fuzzy: 1-fuzzy match, 0-exact match
    :return: a list of matched keys
    """
    descendant_keys = []
    if not isinstance(key, (list, set, tuple)):
        key = [str(key), ]
    if not isinstance(keys, (list, set, tuple)):
        keys = [str(keys), ]
    if not key:
        return keys
    for i_key in key:
        for j_key in keys:
            if fuzzy:
                if format(i_key).strip() in j_key:
                    descendant_keys.append(j_key)
            else:
                if format(i_key).strip() == j_key:
                    descendant_keys.append(j_key)
                elif j_key.startswith("{}.".format(i_key).strip()):
                    descendant_keys.append(j_key)
                elif j_key.startswith("{}[".format(i_key).strip()):
                    descendant_keys.append(j_key)
    return descendant_keys


# parameters to dict, e.g. date=0305&tag=abcd&id=123 => {'date': '0305', 'tag': 'abcd', 'id': 123}
def param2dict(item):
    my_dict = {}
    for i_item in str(item).split('&'):
        i_arr = i_item.split('=')
        my_dict[i_arr[0]] = i_arr[1]
    return my_dict


# dict to parameters, e.g. {'date': '0305', 'tag': 'abcd', 'id': 123} => date=0305&tag=abcd&id=123
def dict2param(item):
    if not isinstance(item, dict):
        return str(item)
    my_param = ''
    for key, val in item.items():
        my_param = my_param + "&{}={}".format(key, val) if my_param else "{}={}".format(key, val)
    return my_param


if __name__ == "__main__":
    pass

