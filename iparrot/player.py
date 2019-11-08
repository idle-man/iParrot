# -*- coding: utf-8 -*-

from iparrot.modules.helper import *
from iparrot.modules.request import HttpRequest
from iparrot.modules.validator import Validator
from iparrot.modules.logger import logger, set_logger
from iparrot.modules.reportor import Report
from iparrot.extension.helper import *
from iparrot.parser import CaseParser


MINOR_INTERVAL_MS = 10
MAX_INTERVAL_MS = 60000


class Player(object):
    def __init__(self):
        self.parser = CaseParser()
        self.session = HttpRequest()
        self.variables = {}
        self.req_span = 0
        self.validator = Validator()
        self.report = {
            'time': {
                'start': 0,
                'end': 0
            },
            'summary': {
                'suite': {
                    'total': 0,
                    'pass': 0,
                    'fail': 0
                },
                'case': {
                    'total': 0,
                    'pass': 0,
                    'fail': 0
                },
                'step': {
                    'total': 0,
                    'pass': 0,
                    'fail': 0
                }
            },
            'detail': []
        }

    def __reset_env(self):
        self.variables = {}
        self.req_span = 0
        if self.session:
            self.session.close()
        self.session = HttpRequest()

    def run_cases(self, suite_or_case, environment=None, interval='ms', reset_after_case=False,
                  fail_stop=False, retry_times=0, retry_interval=100, output='.'):
        """
        :param suite_or_case: file or directory of test suites / cases / steps
        :param environment: environment flag defined in test data, 'None' - only load 'global' data
        :param interval: interval time(ms) between each step, use the recorded interval as default
        :param reset_after_case: reset runtime environment after each case or not, 'no' as default
        :param fail_stop: stop or not when a test step failed on validation, False as default
        :param retry_times: max retry times when a test step failed on validation, 0 as default
        :param retry_interval: retry interval(ms) when a test step failed on validation, 100 as default
        :param output: output path for report, '.' as default
        :return:
        """
        try:
            interval = float(interval)
        except ValueError:
            interval = 'ms'
        try:
            retry_times = int(retry_times)
        except ValueError:
            retry_times = 0
        try:
            retry_interval = int(retry_interval)
        except ValueError:
            retry_interval = 100

        # parse specified cases into dict
        items = self.parser.load_test_case(suite_or_case=suite_or_case, environment=environment)
        self.report['title'] = suite_or_case
        self.report['detail'] = items
        self.report['time']['start'] = now_ms()
        if not items:
            logger.error("Parsed {}, but get nothing.".format(suite_or_case))
            return -1
        for _sid, _suite in enumerate(items):
            self.report['summary']['suite']['total'] += 1
            _suite['_report_'] = {
                'id': _sid,
                'name': _suite['config']['name'],
                'status': True,
                'cases': {
                    'total': 0,
                    'pass': 0,
                    'fail': 0
                }
            }
            logger.info("Run test suite: {}".format(json.dumps(_suite, ensure_ascii=False)))

            # do hook actions before a suite
            logger.info(" - Do setup hook actions of the suite: {}".format(_suite['setup_hooks']))
            self.do_hook_actions(_suite['setup_hooks'])

            for _cid, _case in enumerate(_suite['test_cases']):
                self.report['summary']['case']['total'] += 1
                _suite['_report_']['cases']['total'] += 1
                _case['_report_'] = {
                    'id': _cid,
                    'name': _case['config']['name'],
                    'status': True,
                    'steps': {
                        'total': 0,
                        'pass': 0,
                        'fail': 0
                    }
                }
                logger.info("Run test case: {}".format(json.dumps(_case, ensure_ascii=False)))

                # do hook actions before a case
                logger.info(" - Do setup hook actions of the case: {}".format(_case['setup_hooks']))
                self.do_hook_actions(_case['setup_hooks'])

                for _tid, _step in enumerate(_case['test_steps']):
                    self.report['summary']['step']['total'] += 1
                    _case['_report_']['steps']['total'] += 1
                    _step['_report_'] = {
                        'id': _tid,
                        'name': _step['config']['name'],
                        'status': True
                    }
                    logger.info("Run test step: {}".format(json.dumps(_step, ensure_ascii=False)))

                    # do hook actions before a request
                    logger.info(" - Do setup hook actions of the step: {}".format(_step['setup_hooks']))
                    self.do_hook_actions(_step['setup_hooks'])

                    # handle variables, priority: suite > case > step
                    self.__set_variables(_step['config']['variables'])
                    self.__set_variables(_case['config']['variables'])
                    self.__set_variables(_suite['config']['variables'])
                    logger.info(" - Config variables of the step: {}".format(json.dumps(self.variables, ensure_ascii=False)))

                    # handle request interval
                    if not isinstance(interval, (int, float)):
                        if 'time.start' in _step['request']:  # use the recorded interval
                            _span = now_timestamp_ms() - int(_step['request']['time.start'])
                            if not self.req_span:
                                self.req_span = _span
                            _sleep = self.req_span - _span if self.req_span > _span else MINOR_INTERVAL_MS
                            # higher than MAX, treat it as request of another batch
                            if _sleep > MAX_INTERVAL_MS:
                                _sleep = MINOR_INTERVAL_MS
                                self.req_span = _span  # reset span
                        else:  # no recorded interval, use default
                            _sleep = MINOR_INTERVAL_MS
                    else:  # use specified interval
                        _sleep = interval
                    if _sleep != MINOR_INTERVAL_MS:
                        logger.info(" - Break time, sleep for {} ms.".format(_sleep))
                    time.sleep(_sleep/1000.0)

                    try_flag = True
                    while try_flag:
                        # run this request
                        response = self.run_one_request(_step['request'])
                        _step['_report_']['request'] = response['request']
                        _step['_report_']['response'] = response['response']
                        _step['_report_']['time'] = response['time']

                        # extract specified variables
                        if 'extract' in _step['response'] and _step['response']['extract']:
                            logger.info(" - Extract variables: {}".format(_step['response']['extract']))
                            self.__extract_variable(extract=_step['response']['extract'], response=response['response'])
                            logger.debug(" - Variables after extract: {}".format(json.dumps(self.variables, ensure_ascii=False)))

                        # do response validation
                        _validate = self.do_validation(response=response['response'], rules=_step['validations'])
                        _step['_report_']['validation'] = _validate
                        if not _validate['status']:  # failed
                            logger.info(" - Test step validation failed")
                            if fail_stop:
                                try_flag = False
                                break
                            elif retry_times:
                                logger.info("Sleep {} ms and Run this test step again..".format(retry_interval))
                                retry_times -= 1
                                time.sleep(retry_interval*1.0/1000)
                            else:
                                break
                        else:
                            break
                    if _step['_report_']['validation']['status']:  # step pass
                        self.report['summary']['step']['pass'] += 1
                        _case['_report_']['steps']['pass'] += 1
                    else:
                        self.report['summary']['step']['fail'] += 1
                        _case['_report_']['steps']['fail'] += 1
                        _suite['_report_']['status'] = _case['_report_']['status'] = _step['_report_']['status'] = False

                    if not try_flag:  # need to stop
                        _suite['_report_']['cases']['fail'] += 1
                        self.report['summary']['case']['fail'] += 1
                        self.report['summary']['case']['pass'] = self.report['summary']['case']['total'] - \
                                                                 self.report['summary']['case']['fail']
                        self.report['summary']['suite']['fail'] += 1
                        self.report['summary']['suite']['pass'] = self.report['summary']['suite']['total'] - \
                                                                  self.report['summary']['suite']['fail']
                        self.report['time']['end'] = now_ms()
                        logger.info("Stop according to your --fail-stop argument")
                        return self.generate_report(output=output)

                    # do hook actions after a request
                    logger.info(" - Do teardown hook actions of the step: {}".format(_step['teardown_hooks']))
                    self.do_hook_actions(_step['teardown_hooks'])

                # do hook actions after a case
                logger.info(" - Do teardown hook actions of the case: {}".format(_case['teardown_hooks']))
                self.do_hook_actions(_case['teardown_hooks'])

                if reset_after_case:  # reset runtime environment after each case
                    logger.info("Reset runtime environment after the case")
                    self.__reset_env()

                if _case['_report_']['status']:  # case pass
                    _suite['_report_']['cases']['pass'] += 1
                    self.report['summary']['case']['pass'] += 1
                else:
                    _suite['_report_']['cases']['fail'] += 1
                    self.report['summary']['case']['fail'] += 1
                    _suite['_report_']['status'] = False

            # do hook actions after a suite
            logger.info(" - Do teardown hook actions of the suite: {}".format(_suite['teardown_hooks']))
            self.do_hook_actions(_suite['teardown_hooks'])

            # reset runtime environment after each suite
            logger.info("Reset runtime environment after the suite")
            self.__reset_env()

            if _suite['_report_']['status']:  # suite pass
                self.report['summary']['suite']['pass'] += 1
            else:
                self.report['summary']['suite']['fail'] += 1
            self.report['time']['end'] = now_ms()

        # generate report
        self.generate_report(output=output)

    def run_one_request(self, request):
        logger.debug("Run request: {}".format(json.dumps(request, ensure_ascii=False)))
        ret = self.session.request(
            url=self.__get_variables("{}://{}{}".format(request['protocol'], request['host'], request['url'])),
            method=request['method'],
            params=self.__get_variables(request['params']),
            data=self.__get_variables(request['data']),
            headers=self.__get_variables(request['headers']),
            cookies=self.__get_variables(request['cookies'])
        )
        logger.debug("Get response: {}".format(json.dumps(ret, ensure_ascii=False)))
        return ret

    def __set_variables(self, variables):
        logger.debug(" - To set variables: {}".format(json.dumps(variables, ensure_ascii=False)))
        self.variables.update(variables)
        logger.debug(" - Variables after update: {}".format(json.dumps(self.variables, ensure_ascii=False)))

    def __extract_variable(self, extract, response):
        if not extract:
            return
        # extract status
        _all_ = {
            'status.code': response['status.code']
        }
        # extract content
        try:
            _all_.update(get_all_kv_pairs(item=json.loads(response['content']), prefix='content', mode=0))
        except json.decoder.JSONDecodeError:
            _all_['content'] = response['content']
        # extract headers
        for _key, _val in response['headers'].items():
            _all_["headers.{}".format(_key)] = _val
        # extract cookies
        for _key, _val in response['cookies'].items():
            _all_["cookies.{}".format(_key)] = _val
        logger.debug(" - All optional variables: {}".format(json.dumps(_all_, ensure_ascii=False)))

        # extract specified element, and set in self.variables
        if isinstance(extract, dict):
            for _key, _val in extract.items():
                self.variables[_key] = _all_[_val] if _val in _all_ else _val
        elif isinstance(extract, (list, set, tuple)):
            for _key in extract:
                self.variables[_key] = _all_[_key] if _key in _all_ else ""
        else:
            self.variables[format(extract)] = _all_[format(extract)] if format(extract) in _all_ else ""

    def __get_variables(self, source):
        """
        :param source: source string or dict
            - abc => abc
            - when self.variables['B'] = b, a{B}c => abc
            - when lower('B') = 'b', a{{lower('B')}}c => abc
        :return: string or dict with precise values
        """
        if isinstance(source, str):
            if source.startswith('{') and source.endswith('}'):
                try:
                    _source = json.loads(source)
                    _new = {}
                    for _key, _val in _source.items():
                        _new[self.__get_real_value(_key)] = self.__get_real_value(_val)
                    return json.dumps(_new, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
            return self.__get_real_value(source)
        elif isinstance(source, dict):
            for _key in source.keys():
                source[_key] = self.__get_variables(source[_key])
        return source

    def __get_real_value(self, variable):
        _rs = re.compile(r"(\${([^{}]+)})")  # to match ${VariableA}
        _rf = re.compile(r"(\${{([^{}]+)}})")  # to match ${{Function(A)}}

        while re.search(_rs, format(variable)):
            for _pair in re.findall(_rs, format(variable)):
                _pair = list(_pair)
                if _pair[1] in self.variables:
                    _pair[1] = self.variables[_pair[1]]
                else:
                    logger.warning("Undefined variable: {}, set to ''".format(_pair[1]))
                    _pair[1] = ''
                if variable == _pair[0]:
                    variable = _pair[1]
                    break
                variable = variable.replace(_pair[0], str(_pair[1]))
        while re.search(_rf, format(variable)):
            for _pair in re.findall(_rf, format(variable)):
                _pair = list(_pair)
                try:
                    _pair[1] = eval(_pair[1])
                except SyntaxError or Exception as e:
                    logger.warning("Invalid function: {}: {}, set to ''".format(_pair[0], e))
                    _pair[1] = ''
                if variable == _pair[0]:
                    variable = _pair[1]
                    break
                variable = variable.replace(_pair[0], str(_pair[1]))
        return variable

    def do_validation(self, response, rules):
        logger.info(" - Do response validations: {}".format(rules))
        _content = None
        if 'Content-Type' in response['headers'] and response['headers']['Content-Type'].startswith('application/json'):
            _content = response['content'].replace("\n", "")
            response['content'] = json.loads(response['content'])
        _response = get_all_kv_pairs(item=response, mode=0)
        response = {}
        for _k, _v in _response.items():
            if isinstance(_v, str):
                _v = "__break_line__".join(_v.split("\n"))
            response[_k] = _v
        if _content:
            response['content'] = _content
        result = {'status': True, 'detail': []}
        self.validator.set_response(response)
        for _rule in rules:
            for _com, _item in _rule.items():
                if isinstance(_item, dict):
                    for _key, _val in _item.items():
                        _status = self.validator.validate(
                            comparator=_com, actual=self.__get_variables(_key), expected=_val)
                        result['detail'].append({
                            'check': _key,
                            'comparator': _com,
                            'expect': _val,
                            'actual': self.validator.actual,
                            'status': _status
                        })
                        if not _status:
                            result['status'] = False
                elif isinstance(_item, (list, tuple, set)):
                    for __item in _item:
                        if isinstance(__item, dict):
                            for _key, _val in __item.items():
                                _status = self.validator.validate(
                                    comparator=_com, actual=self.__get_variables(_key), expected=_val)
                                result['detail'].append({
                                    'check': _key,
                                    'comparator': _com,
                                    'expect': _val,
                                    'actual': self.validator.actual,
                                    'status': _status
                                })
                                if not _status:
                                    result['status'] = False
                        else:
                            _status = self.validator.validate(
                                comparator=_com, actual=self.__get_variables(format(__item)))
                            result['detail'].append({
                                'check': __item,
                                'comparator': _com,
                                'expect': "<{}>".format(_com),
                                'actual': self.validator.actual,
                                'status': _status
                            })
                            if not _status:
                                result['status'] = False
                else:
                    _status = self.validator.validate(comparator=_com, actual=self.__get_variables(format(_item)))
                    result['detail'].append({
                        'check': _item,
                        'comparator': _com,
                        'expect': "<{}>".format(_com),
                        'actual': self.validator.actual,
                        'status': _status
                    })
                    if not _status:
                        result['status'] = False
        logger.info(" - Validation result: {}".format(json.dumps(result, ensure_ascii=False)))
        return result

    def do_hook_actions(self, actions):
        """
        :param actions: actions list
            - {key: value} : set variable
            - ${{function(params)}} : exec function
            - else : exec code or print message
        :return:
        """
        if not actions:
            return
        for _action in actions:
            if isinstance(_action, dict):  # set variables
                self.__set_variables(variables=_action)
            elif re.search(re.compile(r"(\${{([^{}]+)}})"), _action):  # exec function
                # in __get_variables, ${{function(params)}} will be executed via eval()
                self.__get_variables(source=_action)
            else:  # exec code or print message
                try:
                    eval(_action)
                except SyntaxError or Exception:
                    print(_action)
                    continue

    def generate_report(self, output):
        report_file = "{}/parrot_{}.html".format(output, now_timestamp())
        make_dir(output)
        Report(stream=open(report_file, 'w', encoding='utf-8')).generate_report(result=self.report)
        logger.info("You could check the report: {}".format(report_file))


if __name__ == '__main__':
    set_logger(level='info')
    player = Player()
    player.run_cases(suite_or_case='../demo/test_cases')
