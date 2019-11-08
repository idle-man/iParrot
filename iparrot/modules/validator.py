# -*- coding: utf-8 -*-

from iparrot.modules.helper import *
from iparrot.modules.logger import logger, set_logger
from iparrot.extension.helper import *


class Validator(object):
    UNIFORM_COMPARATOR = {
        "eq": {
            "uniform": "equals",
            "sample": "1 eq 1, 'a' eq 'a', [1, 2] eq [1, 2], {'a': 1 } eq {'a': 1}"
        },
        "neq": {"uniform": "not_equals", "sample": "1 neq 2"},
        "lt": {"uniform": "less_than", "sample": "1 lt 2"},
        "gt": {"uniform": "greater_than", "sample": "2 gt 1"},
        "le": {"uniform": "less_than_or_equals", "sample": "1 le 1"},
        "ge": {"uniform": "greater_than_or_equals", "sample": "2 ge 1"},
        "str_eq": {"uniform": "string_equals", "sample": "'abc' str_eq 'abc'"},
        "len_eq": {
            "uniform": "length_equals",
            "sample": "'ab' len_eq 2, [1, 2] len_eq 2, {'a': 1} len_eq 1"
        },
        "len_neq": {"uniform": "length_not_equals", "sample": "'ab' len_neq 1"},
        "len_lt": {"uniform": "length_less_than", "sample": "{'a': 1, 'b': 2} len_lt 3"},
        "len_gt": {"uniform": "length_greater_than", "sample": "'abc' len_gt 2"},
        "len_le": {"uniform": "length_less_than_or_equals", "sample": "[1, 2] len_le 2"},
        "len_ge": {"uniform": "length_greater_than_or_equals", "sample": "{'a': 1, 'b': 2} len_ge 2"},
        "contain": {
            "uniform": "contains",
            "sample": "'abc' contain 'ab', ['a', 'b'] contain 'a', {'a': 1, 'b': 2} contain {'a': 1}"
        },
        "not_contain": {"uniform": "not_contain", "sample": "[1, 2] not_contain 3"},
        "in": {
            "uniform": "in",
            "sample": "'a' in 'ab', 'a' in ['a', 'b'], 'a' in {'a': 1, 'b': 2}"
        },
        "not_in": {"uniform": "not_in", "sample": "'c' not_in 'ab', 'c' not_in ['a', 'b'], 'c' not_in {'a': 1}"},
        "is": {"uniform": "is_instance", "sample": "1 is_instance 'int', [1, 2] is_instance ['list', 'set']"},
        "is_not": {"uniform": "is_not_instance", "sample": "'a' is_not_instance 'int'"},
        "false": {"uniform": "is_false", "sample": "0 is_false, '' is_false, [] is_false, {} is_false"},
        "true": {"uniform": "is_true", "sample": "1 is_true, 'a' is_true"},
        "exist": {"uniform": "exists", "sample": "'a.b[1].c' exists, when response={'a.b[1].c': 1, 'a.b[2].c': 2}"},
        "not_exist": {"uniform": "not_exists", "sample": ""},
        "re": {"uniform": "regex", "sample": "'1900-01-01' re r'\\d+-\\d+-\\d+'"},
        "not_re": {"uniform": "not_regex", "sample": "'abc' not_re 'ad'"},
        "json": {"uniform": "is_json", "sample": "{\"a\": 1} is_json"},
        "not_json": {"uniform": "is_not_json", "sample": ""}
    }

    def __init__(self, response=None):
        self.response = response if response else {}
        self.in_resp = None
        self.actual = None

    @staticmethod
    def _convert_comparator(comparator):
        """ convert comparator alias to uniform name and expression
        """
        comparator = comparator.lower()

        # simple assert
        if comparator in ["eq", "equal", "equals", "==", "="]:
            return ["equals",
                    "${{self._simple_assert('==', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["neq", "not_equal", "not_equals", "!=", "<>"]:
            return ["not_equals",
                    "${{self._simple_assert('!=', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["lt", "less", "less_than"]:
            return ["less_than",
                    "${{self._simple_assert('<', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["gt", "greater", "greater_than"]:
            return ["greater_than",
                    "${{self._simple_assert('>', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["le", "less_equal", "less_equals", "less_than_or_equal", "less_than_or_equals",
                            "ngt", "not_greater_than"]:
            return ["less_than_or_equals",
                    "${{self._simple_assert('<=', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["ge", "greater_equal", "greater_equals", "greater_than_or_equal", "greater_than_or_equals",
                            "nlt", "not_less_than"]:
            return ["greater_than_or_equals",
                    "${{self._simple_assert('>=', first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["str_eq", "str_equal", "str_equals", "string_equal", "string_equals"]:
            return ["string_equals",
                    "${{self._simple_assert('==', first=str(__FIRST__), second=str(__SECOND__))}}"]

        # count assert
        # 'abc' count_equals 3, ['ab', 'bc'] count_equals 2, {'ab': 1} count_equals 1
        elif comparator in ["len_eq", "len_equal", "len_equals", "length_equal", "length_equals",
                            "count_eq", "count_equal", "count_equals", "cnt_eq", "cnt_equal", "cnt_equals"]:
            return ["length_equals",
                    "${{self._length_assert('==', first=__FIRST__, second=int(__SECOND__))}}"]
        elif comparator in ["len_neq", "len_not_equal", "len_not_equals", "length_not_equal", "length_not_equals",
                            "cnt_neq", "cnt_not_equal", "cnt_not_equals", "count_not_equal", "count_not_equals"]:
            return ["length_not_equals",
                    "${{self._length_assert('!=', first=__FIRST__, second=int(__SECOND__))}}"]
        elif comparator in ["len_gt", "len_greater", "len_greater_than", "length_greater_than", "length_greater",
                            "cnt_gt", "count_gt", "cnt_greater_than", "count_greater_than", "count_greater"]:
            return ["length_greater_than",
                    "${{self._length_assert('>', first=__FIRST__, second=int(__SECOND__))}}"]
        elif comparator in ["len_lt", "len_less", "len_less_than", "length_less_than", "length_less",
                            "cnt_lt", "count_lt", "cnt_less_than", "count_less_than", "count_less"]:
            return ["length_less_than",
                    "${{self._length_assert('<', first=__FIRST__, second=int(__SECOND__))}}"]
        elif comparator in ["len_ge", "len_greater_than_or_equals", "length_greater_than_or_equals",
                            "cnt_ge", "count_ge", "cnt_greater_than_or_equals", "count_greater_than_or_equals",
                            "len_greater_or_equals", "length_greater_or_equals",
                            "cnt_greater_or_equals", "count_greater_or_equals"]:
            return ["length_greater_than_or_equals",
                    "${{self._length_assert('>=', first=__FIRST__, second=int(__SECOND__))}}"]
        elif comparator in ["len_le", "len_less_than_or_equals", "length_less_than_or_equals",
                            "cnt_le", "count_le", "cnt_less_than_or_equals", "count_less_than_or_equals",
                            "len_less_or_equals", "length_less_or_equals",
                            "cnt_less_or_equals", "count_less_or_equals"]:
            return ["length_less_than_or_equals",
                    "${{self._length_assert('<=', first=__FIRST__, second=int(__SECOND__))}}"]

        # 'abc' contains 'ab', ['ab', 'bc'] contains 'ab', {'ab': 1, 'ac': 2} contains 'ab'
        elif comparator in ["contain", "contains", "str_contain", "str_contains", "string_contain", "string_contains",
                            "list_contain", "list_contains", "dict_contain", "dict_contains"]:
            return ["contains",
                    "${{self._contain_assert(first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["not_contain", "not_contains",
                            "str_not_contain", "str_not_contains", "string_not_contain", "string_not_contains",
                            "list_not_contain", "list_not_contains", "dict_not_contain", "dict_not_contains"]:
            return ["not_contains",
                    "${{bool(1-self._contain_assert(first=__FIRST__, second=__SECOND__))}}"]

        # 'ab' in 'abc', 'ab' in ['ab', 'bc'], 'ab' in {'ab': 1, 'ac': 2}
        elif comparator in ["in", "in_str", "in_string", "in_list", "in_set", "in_tuple", "in_dict"]:
            return ["in",
                    "${{self._contain_assert(first=__FIRST__, second=__SECOND__, reverse=True)}}"]
        elif comparator in ["nin", "not_in", "not_in_str", "not_in_string",
                            "not_in_list", "not_in_tuple", "not_in_set", "not_in_dict"]:
            return ["not_in",
                    "${{bool(1-self._contain_assert(first=__FIRST__, second=__SECOND__, reverse=True))}}"]

        # 'abc' is_instance str, 1 is_instance int, [1, 2] is_instance list, {'a': 1} is_instance dict
        elif comparator in ["is", "instance", "is_instance", "type", "is_type"]:
            return ["is_instance",
                    "${{self._instance_assert(first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["is_not", "not_instance", "is_not_instance", "not_type", "is_not_type"]:
            return ["is_not_instance",
                    "${{bool(1-self._instance_assert(first=__FIRST__, second=__SECOND__))}}"]

        # '' is_null, None is_null, [] is_null, {} is_null
        elif comparator in ["em", "empty", "none", "is_none", "null", "is_null", "false", "is_false"]:
            return ["is_false",
                    "${{self._false_assert(first=__FIRST__)}}"]
        elif comparator in ["nem", "not_empty", "not_none", "not_null", "not_false", "true", "is_true"]:
            return ["is_true",
                    "${{bool(1-self._false_assert(first=__FIRST__))}}"]
        elif comparator in ["ex", "exist", "exists", "defined"]:
            return ["exists",
                    "${{bool(1-self._false_assert(first=__FIRST__))}}"]
        elif comparator in ["nex", "not_exist", "not_exists", "undefined", "not_defined"]:
            return ["not_exists",
                    "${{self._false_assert(first=__FIRST__)}}"]

        # use re.compile() and re.search()
        elif comparator in ["re", "reg", "regex"]:
            return ["regex",
                    "${{self._regex_assert(first=__FIRST__, second=__SECOND__)}}"]
        elif comparator in ["nre", "not_re", "not_reg", "not_regex"]:
            return ["not_regex",
                    "${{bool(1-self._regex_assert(first=__FIRST__, second=__SECOND__))}}"]

        elif comparator in ["json", "is_json"]:
            return ["is_json",
                    "${{self._json_assert(first=__FIRST__)}}"]
        elif comparator in ["njson", "not_json", "is_not_json"]:
            return ["is_not_json",
                    "${{bool(1-self._json_assert(first=__FIRST__))}}"]

        else:
            return [comparator, None]

    def set_response(self, response):
        self.response = response

    # assert main function
    def validate(self, comparator, actual, expected=None):
        """
        :param comparator: defined in _convert_comparator()
        :param actual: actual result, one key in response.keys()
        :param expected: expected result
        :return: True / False
        """
        comparator, expression = self._convert_comparator(comparator)
        if not expression:
            logger.warning("Unsupported comparator: {}, please refer to: {}".format(
                comparator,
                json.dumps(self.UNIFORM_COMPARATOR, ensure_ascii=False)))
            return False

        # get the actual value in response
        if actual in self.response:
            self.in_resp = 1
            actual = self.response[actual]
        else:  # otherwise, the input is already the value
            self.in_resp = 0
        self.actual = actual

        _rf = re.compile(r"\${{([^{}]+)}}")  # to match ${{Function(A)}}
        if re.match(_rf, expression):
            expression = re.findall(_rf, expression)[0]
            if isinstance(actual, (list, tuple, set, dict, int, float)):
                expression = expression.replace('__FIRST__', "{}".format(actual))
            else:
                expression = expression.replace('__FIRST__', "'{}'".format(format(actual).replace("\'", "\\\'")))
            if isinstance(expected, (list, tuple, set, dict, int, float)):
                expression = expression.replace('__SECOND__', "{}".format(expected))
            else:
                expression = expression.replace('__SECOND__', "'{}'".format(format(expected).replace("\'", "\\\'")))
        try:
            return eval(expression)
        except NameError or TypeError or SyntaxError or Exception as e:
            logger.warning("Run {} - {} failed: {}".format(comparator, expression, e))
            return False

    @staticmethod
    # first vs. second
    def _simple_assert(comparator, first, second):
        if isinstance(first, (list, tuple, set, dict, int, float)):
            expression = "{} {}".format(first, comparator)
        else:
            if isinstance(first, str):
                first = first.replace("\'", "\\\'")
            expression = "'{}' {}".format(first, comparator)
        if isinstance(second, (list, tuple, set, dict, int, float)):
            expression = "{} {}".format(expression, second)
        else:
            if isinstance(second, str):
                second = second.replace("\'", "\\\'")
            expression = "{} '{}'".format(expression, second)
        return eval(expression)

    @staticmethod
    # len(first) vs. second
    # 'abc' count_equals 3, ['ab', 'bc'] count_equals 2, {'ab': 1} count_equals 1
    def _length_assert(comparator, first, second=0):
        if isinstance(first, (list, tuple, set, dict)):
            first = len(first)
        else:
            first = len(format(first))

        second = int(second)
        return eval("{} {} {}".format(first, comparator, second))

    @staticmethod
    # isinstance(first, second)
    # 'abc' is_instance str, 1 is_instance int, [1, 2] is_instance list, {'a': 1} is_instance dict
    def _instance_assert(first, second):
        if isinstance(second, (list, tuple, set)):
            for _type in second:
                if isinstance(first, eval(_type)):
                    return True
            return False
        else:
            return isinstance(first, eval(second))

    # '' is_null, {} is_null, [] is_null
    def _false_assert(self, first):
        if self.in_resp:
            return bool(1 - bool(first))
        else:
            return True

    @staticmethod
    def _json_assert(first):
        try:
            json.loads(first)
            return True
        except json.JSONDecodeError:
            return False

    @staticmethod
    # first contains second, second in first
    # 'abc' contains 'ab', ['ab', 'bc'] contains 'ab', {'ab': 1, 'ac': 2} contains 'ab'
    # ['ab', 'bc', 'cd'] contains ['ab', 'cd'], {'ab': 1, 'ac': 2} contains {'ab': 1}
    def _contain_assert(first, second, reverse=False):
        if reverse:
            second, first = first, second
        if isinstance(first, (list, tuple, set, dict)):
            if isinstance(second, (list, tuple, set, dict)):
                _pairs1 = get_all_kv_pairs(item=first)
                _pairs2 = get_all_kv_pairs(item=second)
                for _item in _pairs2:
                    if _item not in _pairs1:
                        return False
                return True
            else:
                return second in first
        else:
            return format(second) in format(first)

    @staticmethod
    # re.search(second, first)
    def _regex_assert(first, second):
        return bool(re.search(re.compile(format(second)), format(first)))


if __name__ == '__main__':
    v = Validator(response={
        'status.code': 200,
        'content.data': {
            'a': 1,
            'b': 2,
            'c': 3
        },
        'content.date': '2019-01-01',
        'content.number': 2,
        'content.string': 'abc def'
    })

    print(json.dumps(v.UNIFORM_COMPARATOR, ensure_ascii=False, indent=4))
    assert v.validate(comparator='neq', actual='status.code', expected=500) is True
    assert v.validate(comparator='str_eq', actual='content.number', expected='2') is True
    assert v.validate(comparator='len_eq', actual='content.number', expected=1) is True
    assert v.validate(comparator='is_instance', actual='content.number', expected=['int', 'str']) is True
    assert v.validate(comparator='is_not_instance', actual='content.number', expected=['list', 'dict']) is True
    assert v.validate(comparator='is_json', actual=json.dumps(v.response)) is True
    assert v.validate(comparator='is_null', actual='content.data') is False
    assert v.validate(comparator='contains', actual='content.date', expected='2019') is True
    assert v.validate(comparator='not_contains', actual='content.date', expected='2018') is True
    assert v.validate(comparator='contains', actual='content.data', expected={'a': 1}) is True
    assert v.validate(comparator='in', actual='content.data', expected={'a': 1, 'b': 2, 'c': 3, 'd': 4}) is True
    assert v.validate(comparator='re', actual='content.date', expected=r"\d+-\d+-\d+") is True
