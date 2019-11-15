# -*- coding: utf-8 -*-

import base64
import copy
import json
import yaml

from yaml.scanner import ScannerError

from iparrot.modules.helper import *
from iparrot.modules.logger import logger, set_logger

# refer to https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
PUBLIC_HEADERS = [
    'accept',
    'accept-charset',
    'accept-encoding',
    'accept-language',
    'accept-patch',
    'accept-ranges',
    'access-control-allow-credentials',
    'access-control-allow-headers',
    'access-control-allow-methods',
    'access-control-allow-origin',
    'access-control-expose-headers',
    'access-control-max-age',
    'access-control-request-headers',
    'access-control-request-method',
    'age',
    'allow',
    'alt-svc',
    'authorization',
    'cache-control',
    'clear-site-data',
    'connection',
    'content-disposition',
    'content-encoding',
    'content-language',
    'content-length',
    'content-location',
    'content-range',
    'content-security-policy',
    'content-security-policy-report-only',
    'content-type',
    'cookie',
    'cookie2',
    'cross-origin-resource-policy',
    'dnt',
    'date',
    'etag',
    'early-data',
    'expect',
    'expect-ct',
    'expires',
    'feature-policy',
    'forwarded',
    'from',
    'host',
    'if-match',
    'if-modified-since',
    'if-none-match',
    'if-range',
    'if-unmodified-since',
    'index',
    'keep-alive',
    'large-allocation',
    'last-modified',
    'link',
    'location',
    'origin',
    'pragma',
    'proxy-authenticate',
    'proxy-authorization',
    'public-key-pins',
    'public-key-pins-report-only',
    'range',
    'referer',
    'referrer-policy',
    'retry-after',
    'save-data',
    'sec-websocket-accept',
    'server',
    'server-timing',
    'set-cookie',
    'set-cookie2',
    'sourcemap',
    'strict-transport-security',
    'te',
    'timing-allow-origin',
    'tk',
    'trailer',
    'transfer-encoding',
    'upgrade-insecure-requests',
    'user-agent',
    'vary',
    'via',
    'www-authenticate',
    'warning',
    'x-content-type-options',
    'x-dns-prefetch-control',
    'x-forwarded-for',
    'x-forwarded-host',
    'x-forwarded-proto',
    'x-frame-options',
    'x-xss-protection'
]

RECORD_HEADERS = [
    'user-agent',
    'content-type',
    'content-encoding'
]

VALIDATE_HEADERS = [
    'content-type'
]

# Length condition set to prevent accidental injury
IDENTIFY_LEN = 6


class CaseParser(object):

    def __init__(self):
        # define templates
        self.env_tpl = {
            'global': {},
            'production': {},
            'development': {},
            'test': {}
        }
        self.step_tpl = {
            'config': {
                'name': '',
                'environment': 'global',
                'import': '',
                'variables': {},
            },
            'setup_hooks': [],
            'request': {},
            'response': {
                'extract': {}
            },
            'validations': [],
            'teardown_hooks': []
        }
        self.case_tpl = {
            'config': {
                'name': "",
                'environment': 'global',
                'import': '',
                'variables': {},
            },
            'setup_hooks': [],
            'test_steps': [],
            'teardown_hooks': []
        }
        self.suite_tpl = {
            'config': {
                'name': "",
                'environment': 'global',
                'import': '',
                'variables': {},
            },
            'setup_hooks': [],
            'test_cases': [],
            'teardown_hooks': []
        }
        self.environment = None

        # to store temporary variables for automatic identification of interface dependencies
        self.variables = {}

    # read and parse test cases into dict for replay
    def load_test_case(self, suite_or_case, environment=None):
        """
        :param suite_or_case: file or directory of test suites/cases/steps
        :param environment: environment defined in test data, None - use defined in suites/cases/steps
        :return: items of test suites/cases/steps
        """
        logger.info("Start to load test suite or case: {}".format(suite_or_case))
        self.environment = environment
        items = []
        if os.path.isdir(suite_or_case):
            files = get_dir_files(suite_or_case)
        else:
            files = [suite_or_case, ]
        for _file in files:
            logger.info("Load case from file: {}".format(_file))
            if not (_file.endswith('yml') or _file.endswith('yaml')):
                logger.warning("Not a yaml file, ignore: {}".format(_file))
                continue
            try:
                _dict = yaml.full_load(stream=self.__read_file(_file))
            except ScannerError as e:
                logger.warning("Invalid yaml file: {}".format(e))
                continue
            logger.debug(" - yaml dict: {}".format(json.dumps(_dict, ensure_ascii=False)))
            _tmp_suite = copy.deepcopy(self.suite_tpl)
            _tmp_case = copy.deepcopy(self.case_tpl)
            _tmp_step = copy.deepcopy(self.step_tpl)
            if 'test_cases' in _dict:  # it's a test suite
                _tmp_suite.update(_dict)
                self.__parse_test_suite(the_dict=_tmp_suite, base_path=get_file_path(_file))
            elif 'test_steps' in _dict:  # it's a test case
                _tmp_case.update(_dict)
                self.__parse_test_case(the_dict=_tmp_case, base_path=get_file_path(_file))
                _tmp_suite['test_cases'].append(_tmp_case)
            else:  # it's a test step
                _tmp_step.update(_dict)
                self.__parse_test_step(the_dict=_tmp_step, base_path=get_file_path(_file))
                _tmp_case['test_steps'].append(_tmp_step)
                _tmp_suite['test_cases'].append(_tmp_case)
            logger.debug(" - one suite: {}".format(json.dumps(_tmp_suite, ensure_ascii=False)))
            items.append(_tmp_suite)
        logger.info("Done.")
        logger.debug("The test suites are: {}".format(json.dumps(items, ensure_ascii=False)))
        return items

    def __parse_test_step(self, the_dict, base_path):
        self.__parse_environments(the_dict, base_path)
        logger.debug(" - test step: {}".format(json.dumps(the_dict, ensure_ascii=False)))

    def __parse_test_case(self, the_dict, base_path):
        self.__parse_environments(the_dict, base_path)
        for _idx, _step in enumerate(the_dict['test_steps']):
            logger.debug(" - step {} in case: {}".format(_idx, _step))
            if _step.startswith('..'):
                _step = "{}/{}".format(base_path, _step)
            try:
                the_dict['test_steps'][_idx] = copy.deepcopy(self.step_tpl)
                the_dict['test_steps'][_idx].update(yaml.full_load(self.__read_file(_step)))
                logger.debug(" - step info: {}".format(json.dumps(the_dict['test_steps'][_idx], ensure_ascii=False)))
            except ScannerError as e:
                logger.warning("Invalid yaml file: {}".format(e))
                continue
            self.__parse_test_step(
                the_dict=the_dict['test_steps'][_idx],
                base_path=get_file_path(_step))
        logger.debug(" - test case: {}".format(json.dumps(the_dict, ensure_ascii=False)))

    def __parse_test_suite(self, the_dict, base_path):
        self.__parse_environments(the_dict, base_path)
        for _idx, _case in enumerate(the_dict['test_cases']):
            logger.debug(" - case {} in suite: {}".format(_idx, _case))
            if _case.startswith('..'):
                _case = "{}/{}".format(base_path, _case)
            try:
                the_dict['test_cases'][_idx] = copy.deepcopy(self.case_tpl)
                the_dict['test_cases'][_idx].update(yaml.full_load(self.__read_file(_case)))
                logger.debug(" - case info: {}".format(json.dumps(the_dict['test_cases'][_idx], ensure_ascii=False)))
            except ScannerError as e:
                logger.warning("Invalid yaml file: {}".format(e))
                continue
            self.__parse_test_case(
                the_dict=the_dict['test_cases'][_idx],
                base_path=get_file_path(_case))

    def __parse_environments(self, the_dict, base_path):
        if 'import' in the_dict['config'] and the_dict['config']['import']:
            if the_dict['config']['import'].startswith('..'):
                the_dict['config']['import'] = "{}/{}".format(base_path, the_dict['config']['import'])
            try:
                _tmp_env = yaml.full_load(stream=self.__read_file(the_dict['config']['import']))
                the_dict['config']['import'] = _tmp_env
                _variables = copy.deepcopy(_tmp_env['global']) if 'global' in _tmp_env else {}
                # env priority: argument > config
                _env = self.environment if self.environment else the_dict['config']['environment']
                if _env in _tmp_env:
                    _variables.update(_tmp_env[_env])
                _variables.update(the_dict['config']['variables'])
                the_dict['config']['variables'] = _variables
            except ScannerError as e:
                logger.warning("Invalid yaml file: {}".format(e))
        logger.debug(" - config variables: {}".format(json.dumps(the_dict['config']['variables'], ensure_ascii=False)))

    def case_replace(self, suite_or_case, rules, target="ParrotProjectNew"):
        """
        :param suite_or_case: file or directory of test suites/cases/steps
        :param rules: replace rule list, key=>value or value1=>value2
        :param target: target directory for case output
        :return: suite dict
        """
        logger.info("Start to load test suite or case: {}".format(suite_or_case))
        files = []
        if isinstance(suite_or_case, (list, tuple, set)):
            items = suite_or_case
        else:
            items = [format(suite_or_case), ]
        for item in items:
            if not os.path.exists(item):
                logger.warning("File {} does not exist, ignore.".format(item))
                continue
            if os.path.isdir(item):
                files.extend(get_dir_files(item))
            else:
                files.append(item)
        total = {}
        for _file in files:
            logger.info("Load case from file: {}".format(_file))
            if not (_file.endswith('yml') or _file.endswith('yaml')):
                logger.warning("Not a yaml file, ignore: {}".format(_file))
                continue
            try:
                _dict = yaml.full_load(stream=self.__read_file(_file))
            except ScannerError as e:
                logger.warning("Invalid yaml file: {}".format(e))
                continue
            logger.debug(" - yaml dict: {}".format(json.dumps(_dict, ensure_ascii=False)))

            if 'test_cases' in _dict:  # it's a test suite
                _tmp_suite = copy.deepcopy(self.suite_tpl)
                _tmp_suite.update(_dict)
                self.__match_rule(_yaml=_file, _dict=_tmp_suite, rules=rules)
                _path = re.findall(r"(.+)test_suites(.+)", get_file_path(_file))
                if _path:
                    total["{}/test_suites/{}/{}".format(target, _path[0][1], get_file_name(_file, ext=1))] = _tmp_suite
                else:
                    total["{}/test_suites/{}".format(target, get_file_name(_file, ext=1))] = _tmp_suite
                _cases = []
                for _case in _tmp_suite['test_cases']:
                    _cases.append("{}/{}".format(get_file_path(_file), _case))
                if _tmp_suite['config']['import']:
                    _cases.append("{}/{}".format(get_file_path(_file), _tmp_suite['config']['import']))
                if _cases:
                    self.case_replace(suite_or_case=_cases, target=target, rules=rules)
            elif 'test_steps' in _dict:  # it's a test case
                _tmp_case = copy.deepcopy(self.case_tpl)
                _tmp_case.update(_dict)
                self.__match_rule(_yaml=_file, _dict=_tmp_case, rules=rules)
                _path = re.findall(r"(.+)test_cases(.+)", get_file_path(_file))
                if _path:
                    total["{}/test_cases/{}/{}".format(target, _path[0][1], get_file_name(_file, ext=1))] = _tmp_case
                else:
                    total["{}/test_cases/{}".format(target, get_file_name(_file, ext=1))] = _tmp_case
                _steps = []
                for _step in _tmp_case['test_steps']:
                    _steps.append("{}/{}".format(get_file_path(_file), _step))
                if _tmp_case['config']['import']:
                    _steps.append("{}/{}".format(get_file_path(_file), _tmp_case['config']['import']))
                if _steps:
                    self.case_replace(suite_or_case=_steps, target=target, rules=rules)
            elif 'request' in _dict:  # it's a test step
                _tmp_step = copy.deepcopy(self.step_tpl)
                _tmp_step.update(_dict)
                self.__match_rule(_yaml=_file, _dict=_tmp_step, rules=rules)
                _path = re.findall(r"(.+)test_steps(.+)", get_file_path(_file))
                if _path:
                    total["{}/test_steps/{}/{}".format(target, _path[0][1], get_file_name(_file, ext=1))] = _tmp_step
                else:
                    total["{}/test_steps/{}".format(target, get_file_name(_file, ext=1))] = _tmp_step
                if _tmp_step['config']['import']:
                    self.case_replace(suite_or_case="{}/{}".format(get_file_path(_file), _tmp_step['config']['import']),
                                      target=target, rules=None)
            else:  # it's environment file
                _path = re.findall(r"(.+)environments(.+)", get_file_path(_file))
                if _path:
                    total["{}/environments/{}/{}".format(target, _path[0][1], get_file_name(_file, ext=1))] = _dict
                else:
                    total["{}/environments/{}".format(target, get_file_name(_file, ext=1))] = _dict
        for _k, _v in total.items():
            make_dir(get_file_path(_k))
            with open(file=format(_k), mode='w', encoding='utf-8') as f:
                yaml.dump(data=_v, stream=f, encoding='utf-8', allow_unicode=True)
            logger.info("Write file after replace: {}".format(_k))
        logger.info("Done. You could get them in {}".format(target))

    def __match_rule(self, _yaml, _dict, rules):
        _k2v = re.compile(r"(.+)=>(.+)")  # key to value, e.g. host=www.example.com
        _pre = re.compile(r"(.+)::(.+)")  # only to speicified api, e.g. /path/to/api::variable1=1234
        logger.info("Do replace actions in {}.".format(_yaml))
        for rule in rules:
            _match = re.findall(_pre, rule)
            if _match:  # only to specified api, fuzzy match with file name
                if format(_match[0][0]).strip() not in _yaml:
                    continue
                _match = re.findall(_k2v, format(_match[0][1]).strip())
            else:
                _match = re.findall(_k2v, rule)
            if _match:
                logger.info("Math rule: {}".format(rule))
                _from = format(_match[0][0]).strip()
                _to = format(_match[0][1]).strip()
                # config.variables => request => request.headers => request.cookies
                _dict['config']['variables'] = self.__do_replace(_dict=_dict['config']['variables'], _from=_from, _to=_to)
                if 'request' in _dict.keys():
                    _dict['request'] = self.__do_replace(_dict=_dict['request'], _from=_from, _to=_to)
                    if 'headers' in _dict['request'].keys():
                        _dict['request']['headers'] = self.__do_replace(_dict=_dict['request']['headers'], _from=_from, _to=_to)
                    if 'cookies' in _dict['request'].keys():
                        _dict['request']['cookies'] = self.__do_replace(_dict=_dict['request']['cookies'], _from=_from, _to=_to)
                if 'validations' in _dict.keys():
                    for _idx, _validate in enumerate(_dict['validations']):
                        for _com, _exp in _validate.items():
                            _dict['validations'][_idx][_com] = self.__do_replace(_dict=_exp, _from=_from, _to=_to)

    @staticmethod
    def __do_replace(_dict, _from, _to):
        if _from in _dict.keys():  # match key first
            logger.info("Replace value of {} from {} to {}.".format(_from, _dict[_from], _to))
            _dict[_from] = _to  # do replace
        else:  # otherwise, match value
            for _k, _v in _dict.items():
                if _from == format(_v):
                    logger.info("Replace value of {} from {} to {}.".format(_k, _from, _to))
                    _dict[_k] = _to  # do replace
        return _dict

    def auto_template(self, target="ParrotProject"):
        """
        :param target: target directory for case output
        :return: suite dict
        """
        suite_dict = copy.deepcopy(self.suite_tpl)
        case_dict = copy.deepcopy(self.case_tpl)
        step_dict = copy.deepcopy(self.step_tpl)
        suite_dict['config']['name'] = case_dict['config']['name'] = 'template'
        step_dict['config'].update({
            'name': 'step',
            'variables': {
                'variable1': 123
            }
        })
        step_dict['request'] = {
            'protocol': "http",
            'method': 'GET',
            'host': "www.example.com",
            'url': "/demo",
            'params': {
                'param1': 'abc',
                'param2': '${variable1}',
                'param3': '${{today()}}'
            },
            'cookies': {},
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36',
                'Content-Type': 'application/json; charset=utf-8'
            },
            'data': {}
        }

        case_dict['test_steps'].append(step_dict)
        suite_dict['test_cases'].append(case_dict)
        self.__generate_case(suite_dict, target)
        return suite_dict

    # parse source file and generate test cases
    def source_to_case(self, source, target="ParrotProject",
                       include=None, exclude=None, validate_include=None, validate_exclude=None,
                       auto_extract=False):
        """
        :param source: source file or direcotry
        :param target: target directory for case output
        :param include: list, not matched url would be ignored in recording
        :param exclude: list, matched url would be ignored in recording
        :param validate_include: list, not matched response would be ignored in validating
        :param validate_exclude: list, matched response would be ignored in validating
        :param auto_extract: bool, for automatic identification of interface dependencies
        :return suite dict
        """
        source = format(source).strip()
        if not (source and os.path.exists(source)):
            logger.error("Source file or directory does not exist: {}".format(source))
            sys.exit(-1)

        if source.endswith("/") or source.endswith("\\"):
            suite_name = get_file_name(get_file_path(source))
        else:
            suite_name = get_file_name(source)

        if os.path.isdir(source):
            files = get_dir_files(source)
        else:
            files = [source, ]

        suite_dict = copy.deepcopy(self.suite_tpl)
        suite_dict['config']['name'] = suite_name

        logger.info("Start to parse cases from source files: {}".format(source))

        for _file in files:
            if _file.lower().endswith('.har'):
                one_case = self.har_to_case(_file, target, include, exclude, validate_include, validate_exclude,
                                            auto_extract, suite_name)
            # elif _file.lower().endswith('.trace'):
            #     self.charles_trace_to_case()
            # elif _file.lower().endswith('.txt'):
            #     self.fiddler_txt_to_case()
            else:
                logger.warning("Unsupported file extension: {}, ignore".format(_file))
                continue

            # add case into suite
            suite_dict['test_cases'].append(one_case)
            logger.info("Parse finished.")

        self.__generate_case(suite_dict, target)
        return suite_dict

    # parse har file and generate test cases
    def har_to_case(self, source, target="ParrotProject",
                    include=None, exclude=None, validate_include=None, validate_exclude=None,
                    auto_extract=False, suite_name=None):
        """parse source har file and generate test cases
        :param source: source file
        :param target: target directory for case output
        :param include: list, not matched url would be ignored in recording
        :param exclude: list, matched url would be ignored in recording
        :param validate_include: list, not matched response would be ignored in validating
        :param validate_exclude: list, matched response would be ignored in validating
        :param auto_extract: bool, for automatic identification of interface dependencies
        :param suite_name: specified suite, new a suite as default
        :return suite dict
        """
        if not (source and os.path.exists(source)):
            logger.error("Source file does not exist: {}".format(source))
            return False
        if not source.lower().endswith('.har'):
            logger.error("The source is not a har file: {}".format(source))
            return False
        logger.info("Start to parse source file: {}".format(source))

        content = self.__read_file(source)
        try:
            har_dict = json.loads(content)['log']['entries']
        except (TypeError or KeyError):
            logger.error("HAR file content error: {}".format(source))
            return False

        case_dict = copy.deepcopy(self.case_tpl)
        case_dict['config']['name'] = get_file_name(file=source)
        for entry_dict in har_dict:
            step_dict = copy.deepcopy(self.step_tpl)
            self.__har_times(entry=entry_dict, step_dict=step_dict)
            if not self.__har_request(entry=entry_dict, step_dict=step_dict,
                                      include=include, exclude=exclude, auto_extract=auto_extract):
                continue
            if not self.__har_response(entry=entry_dict, step_dict=step_dict,
                                       include=validate_include, exclude=validate_exclude,
                                       auto_extract=auto_extract):
                continue
            logger.debug("test_step: {}".format(json.dumps(step_dict, ensure_ascii=False)))

            # add step into case
            case_dict['test_steps'].append(step_dict)
        if suite_name:
            return case_dict
        else:
            suite_dict = copy.deepcopy(self.suite_tpl)
            # add case into suite
            suite_dict['test_cases'].append(case_dict)
            suite_dict['config']['name'] = get_file_name(file=source)
            logger.info("Parse finished.")

            self.__generate_case(suite_dict, target)
            return suite_dict

    @staticmethod
    def __read_file(name):
        try:
            with open(file=name, mode="r", encoding='utf-8') as f:
                content = f.read()
                # solve problem caused by BOM head
                if content.startswith(u'\ufeff'):
                    content = content.encode('utf-8')[3:].decode('utf-8')
                return content
        except IOError:
            logger.error("Failed to open file: {}".format(name))
            sys.exit(-1)

    def __generate_case(self, suite, target="ParrotProject"):
        logger.info("Start to generate test yamls")

        # generate test data
        _d_path = "{}/environments".format(target)
        _d_yaml = "{}/{}_env.yml".format(_d_path, suite['config']['name'])
        r_d_yaml = "../environments/{}_env.yml".format(suite['config']['name'])
        make_dir(_d_path)
        with open(file=_d_yaml, mode='w', encoding='utf-8') as f:
            yaml.dump(data=self.env_tpl, stream=f, encoding='utf-8', allow_unicode=True)
        logger.debug(" - environments: {}".format(_d_yaml))

        _e_path = "{}/test_suites".format(target)
        _e_yaml = "{}/{}.yml".format(_e_path, suite['config']['name'])
        make_dir(_e_path)
        suite['config']['import'] = r_d_yaml
        _t_sid = 0  # count total steps in a suite
        for _cid, _case in enumerate(suite['test_cases']):
            # generate test steps
            for _sid, _step in enumerate(_case['test_steps']):
                _t_sid += 1
                # remove 'response' for a clear view
                # _step['response'] = {'extract': {}}
                _s_resp = copy.deepcopy(_step['response'])
                for _k, _v in _s_resp.items():
                    if _k == 'extract':
                        for _ex_k, _ex_v in _s_resp['extract'].items():
                            if _ex_k in self.variables.keys() and self.variables[_ex_k]['flag']:
                                _step['response']['extract'][_ex_v] = _ex_v
                            del _step['response']['extract'][_ex_k]
                    elif _k != 'time.spent':
                        del _step['response'][_k]
                _s_id = "{}{}".format('0'*(4-len(str(_t_sid))), _t_sid)  # step id
                _s_path = "{}/test_steps/{}".format(target, '/'.join(_step['config']['name'].split('/')[1:-1]))
                _s_yaml = "{}/{}_{}.yml".format(_s_path, _s_id, _step['config']['name'].split('/')[-1])
                r_s_yaml = "../test_steps/{}/{}_{}.yml".format(
                    '/'.join(_step['config']['name'].split('/')[1:-1]),
                    _s_id,
                    _step['config']['name'].split('/')[-1])
                if len(_step['config']['name'].split('/')) > 1:
                    _step['config']['import'] = "{}environments/{}_env.yml".format('../'*(len(_step['config']['name'].split('/'))-1), suite['config']['name'])
                else:
                    _step['config']['import'] = "../environments/{}_env.yml".format(suite['config']['name'])
                make_dir(_s_path)
                with open(file=_s_yaml, mode='w', encoding='utf-8') as f:
                    # use allow_unicode=True to solve Chinese display problem
                    yaml.dump(data=_step, stream=f, encoding='utf-8', allow_unicode=True)
                _case['test_steps'][_sid] = r_s_yaml
                logger.debug(" - test step: {}".format(_s_yaml))

            # generate test cases
            _c_path = "{}/test_cases".format(target)
            _c_yaml = "{}/{}.yml".format(_c_path, _case['config']['name'])
            r_c_yaml = "../test_cases/{}.yml".format(_case['config']['name'])
            _case['config']['import'] = r_d_yaml
            make_dir(_c_path)
            with open(file=_c_yaml, mode='w', encoding='utf-8') as f:
                yaml.dump(data=_case, stream=f, encoding='utf-8', allow_unicode=True)
            logger.debug(" - test case: {}".format(_c_yaml))
            suite['test_cases'][_cid] = r_c_yaml

        # generate test suite
        with open(file=_e_yaml, mode='w', encoding='utf-8') as f:
            yaml.dump(data=suite, stream=f, encoding='utf-8', allow_unicode=True)
        logger.debug(" - test suite: {}".format(_e_yaml))
        logger.info("Done. You could get them in {}".format(target))

    # parse request block and filter unneeded urls
    def __har_request(self, entry, step_dict, include, exclude, auto_extract=False):
        if not ('request' in entry.keys() and entry['request']):
            logger.warning(" * There is no request in this entry: {}".format(json.dumps(entry, ensure_ascii=False)))
            return False
        _req = entry['request']

        # get method
        step_dict['request']['method'] = _req.get('method', 'GET')

        # get url: protocol, host, url path
        _url = _req.get('url', "")
        # logger.info(" Get a {} request: {}".format(step_dict['request']['method'], _url))

        try:
            (
                _whole_url,
                step_dict['request']['protocol'],
                step_dict['request']['host'],
                step_dict['request']['url'],
                _
            ) = re.findall(r"((http\w*)://([\w.:]+)([^?]+))\??(.*)", _url)[0]
            step_dict['config']['name'] = step_dict['request']['url']
            logger.debug(" - protocol: {} host: {} url: {}".format(
                step_dict['request']['protocol'],
                step_dict['request']['host'],
                step_dict['request']['url']))
            logger.info(" Get a {} request: {}".format(step_dict['request']['method'], step_dict['request']['url']))
        except IndexError:
            logger.warning(" * Invalid url: {}".format(_url))
            return False

        # filter with include and exclude options
        logger.debug(" - include: {} exclude: {}".format(include, exclude))
        if not self.__if_include(_whole_url, include) or self.__if_exclude(_whole_url, exclude):
            logger.info(" According to include/exclude options, ignore it")
            return False

        # get parameters
        # it may have both queryString and postData in an unusual post request
        step_dict['request']['params'] = {}
        step_dict['request']['data'] = {}
        _param = _req.get('queryString', [])
        _data = _req.get('postData', [])
        if _data:
            if 'params' in _req.get('postData'):
                _data = _req.get('postData').get('params')
            else:
                _data = _req.get('postData').get('text')
            # if 'mimeType' in _req.get('postData') and _req.get('postData').get('mimeType') == 'application/json':
            #     _tmp = json.loads(_data)
            #     _data = []
            #     for _tk, _tv in _tmp.items():
            #         _data.append({'name': _tk, 'value': _tv})
        logger.debug(" - params: {}".format(_param))
        logger.debug(" - data: {}".format(_data))

        # extract all parameter values into variables, and keep {value} in parameters
        if isinstance(_param, (list, tuple, set)):
            for _item in _param:
                self.__har_extract(step_dict, _item['name'], _item['value'], 'params', auto_extract)
        else:
            # step_dict['request']['params'] = _param
            self.__har_extract(step_dict, '', _param, 'params', auto_extract)
        if isinstance(_data, (list, tuple, set)):
            for _item in _data:
                self.__har_extract(step_dict, _item['name'], _item['value'], 'data', auto_extract)
        else:
            # step_dict['request']['data'] = _data
            self.__har_extract(step_dict, '', _data, 'data', auto_extract)
        logger.debug(" - self.variables: {}".format(json.dumps(self.variables, ensure_ascii=False)))

        # get headers
        step_dict['request']['headers'] = {}
        self.__har_headers(_req.get('headers'), step_dict['request']['headers'], RECORD_HEADERS, auto_extract)
        logger.debug(" - headers: {}".format(json.dumps(step_dict['request']['headers'], ensure_ascii=False)))

        # get cookies
        step_dict['request']['cookies'] = {}
        self.__har_cookies(_req.get('cookies'), step_dict['request']['cookies'], auto_extract)
        logger.debug(" - cookies: {}".format(json.dumps(step_dict['request']['cookies'], ensure_ascii=False)))

        return True

    def __har_extract(self, step_dict, i_name, i_value, i_type, auto_extract=False):
        _value = i_value
        if format(_value) == _value and _value.startswith('{') and _value.endswith('}'):
            try:
                _value = json.loads(_value)
                if not isinstance(_value, dict):
                    _value = i_value
            except json.decoder.JSONDecodeError:
                pass

        if isinstance(_value, dict):
            for _k, _v in _value.items():
                if auto_extract and format(_v) in self.variables.keys():
                    if i_name:
                        step_dict['config']['variables']["{}.{}".format(i_name, _k)] = '${' + self.variables[_v]['key'] + '}'
                    else:
                        step_dict['config']['variables']["{}".format(_k)] = '${' + self.variables[_v]['key'] + '}'
                    self.variables[format(_v)]['flag'] = 1
                else:
                    if i_name:
                        step_dict['config']['variables']["{}.{}".format(i_name, _k)] = _v
                    else:
                        step_dict['config']['variables']["{}".format(_k)] = _v
                if i_name:
                    _value[_k] = '${' + "{}.{}".format(i_name, _k) + '}'
                else:
                    _value[_k] = '${' + "{}".format(_k) + '}'
            if i_name:
                step_dict['request'][i_type][i_name] = json.dumps(_value, ensure_ascii=False)
            else:
                step_dict['request'][i_type] = json.dumps(_value, ensure_ascii=False)
        else:
            if auto_extract and format(_value) in self.variables.keys():
                if i_name:
                    step_dict['config']['variables'][i_name] = '${' + self.variables[_value]['key'] + '}'
                    self.variables[_value]['flag'] = 1
            else:
                if i_name:
                    step_dict['config']['variables'][i_name] = _value
            if i_name:
                step_dict['request'][i_type][i_name] = '${' + "{}".format(i_name) + '}'

    # parse response block and make validations
    def __har_response(self, entry, step_dict, include, exclude, auto_extract=False):
        if not ('response' in entry.keys() and entry['response']):
            logger.warning(" * There is no response in this entry: {}".format(json.dumps(entry, ensure_ascii=False)))
            return False
        _rsp = entry['response']

        # get status
        step_dict['response']['status'] = _rsp.get('status', 200)
        step_dict['validations'].append({"eq": {'status.code': step_dict['response']['status']}})

        # get headers
        step_dict['response']['headers'] = {}
        self.__har_headers(_rsp.get('headers'), step_dict['response']['headers'], VALIDATE_HEADERS)
        _vin = get_matched_keys(key=include, keys=list(step_dict['response']['headers'].keys()), fuzzy=1)
        _vex = get_matched_keys(key=exclude, keys=list(step_dict['response']['headers'].keys()), fuzzy=1) if exclude else []
        for _k, _v in step_dict['response']['headers'].items():
            # Extracting temporary variables for automatic identification of interface dependencies
            if auto_extract and isinstance(_v, str) and len(_v) >= IDENTIFY_LEN:
                if _v not in self.variables.keys():
                    self.variables[_v] = {
                        'key': _k,
                        'flag': 0
                    }
                    step_dict['response']['extract'][_v] = _k
            if _k in _vin and _k not in _vex:
                step_dict['validations'].append({"eq": {_k: _v}})

        logger.debug(" - self.variables: {}".format(json.dumps(self.variables, ensure_ascii=False)))

        # get cookies
        step_dict['response']['cookies'] = {}
        self.__har_cookies(_rsp.get('cookies'), step_dict['response']['cookies'])

        # get content
        try:
            _text = _rsp.get('content').get('text', '')
            _mime = _rsp.get('content').get('mimeType')
            _code = _rsp.get('content').get('encoding')
        except AttributeError:
            logger.warning(" * Invalid response content: {}".format(_rsp.get('content')))
            return False
        if _code and _code == 'base64':
            try:
                _text = base64.b64decode(_text).decode('utf-8')
            except UnicodeDecodeError as e:
                logger.warning(" * Decode error: {}".format(e))
        elif _code:
            logger.warning(" * Unsupported encoding method: {}".format(_code))
            return False
        logger.debug(" - mimeType: {}, encoding: {}".format(_mime, _code))
        logger.debug(" - content text: {}".format(_text))
        if _mime.startswith('application/json'):  # json => dict
            try:
                step_dict['response']['content'] = json.loads(_text)
                # extract all content values into validations
                logger.debug(" - validation include: {}, exclude: {}".format(include, exclude))
                _pairs = get_all_kv_pairs(item=json.loads(_text), prefix='content')
                _vin = get_matched_keys(key=include, keys=list(_pairs.keys()), fuzzy=1)
                _vex = get_matched_keys(key=exclude, keys=list(_pairs.keys()), fuzzy=1) if exclude else []
                for _k, _v in _pairs.items():
                    if isinstance(_v, str):
                        _v = _v.replace("\r\n", '__break_line__').replace("\n", '__break_line__')
                    # Extracting temporary variables for automatic identification of interface dependencies
                    if auto_extract and isinstance(_v, str) and len(_v) >= IDENTIFY_LEN:
                        if _v not in self.variables.keys():
                            self.variables[_v] = {
                                'key': _k,
                                'flag': 0
                            }
                            step_dict['response']['extract'][_v] = _k
                    if _k in _vin and _k not in _vex:
                        step_dict['validations'].append({"eq": {_k: _v}})

            except json.decoder.JSONDecodeError:
                logger.warning(" * Invalid response content in json: {}".format(_text))
                # sys.exit(-1)
        elif _mime.startswith('text/html'):  # TODO: html => dom tree, xpath
            pass
        else:
            logger.warning(" * Unsupported mimeType: {}".format(_mime))
            # step_dict['validations'].append({"eq": {'content': _text}})
        logger.debug(" - validations: {}".format(json.dumps(step_dict['validations'], ensure_ascii=False)))
        logger.debug(" - self.variables: {}".format(json.dumps(self.variables, ensure_ascii=False)))

        return True

    @staticmethod
    def __har_times(entry, step_dict):
        # startedDateTime:
        #   Chrome: 2019-07-24T03:42:07.867Z
        #   Fiddler: 2019-07-24T18:52:38.4367088+08:00
        #   Charles: 2019-07-31T14:21:35.033+08:00
        #   Other: Wed, 30 Jan 2019 07:56:42
        if not ('startedDateTime' in entry.keys() and entry['startedDateTime']):
            logger.warning(" * There is no startedDateTime in this entry: {}".format(json.dumps(entry, ensure_ascii=False)))
            return False
        s_time = entry['startedDateTime']

        if not ('time' in entry.keys() and entry['time']):
            if not ('times' in entry.keys() and entry['times']):
                logger.warning(" * There is no time in this entry: {}".format(json.dumps(entry, ensure_ascii=False)))
                return False
            else:
                i_time = int(round(entry['times']))
        else:
            i_time = int(round(entry['time']))

        # convert startedDateTime to timestamp
        step_dict['request']['time.start'] = har_time2timestamp(har_time=s_time, ms=1)
        step_dict['response']['time.spent'] = i_time

    def __har_headers(self, headers, the_dict, the_needed, auto_extract=False):
        for _item in headers:
            if _item['name'].lower() in the_needed or _item['name'].lower() not in PUBLIC_HEADERS:
                if auto_extract and format(_item['value']) in self.variables.keys():
                    self.variables[_item['value']]['flag'] = 1
                    the_dict["headers.{}".format(_item['name'])] = '${' + "{}".format(self.variables[_item['value']]['key']) + '}'
                else:
                    the_dict["headers.{}".format(_item['name'])] = _item['value']

    def __har_cookies(self, cookies, the_dict, auto_extract=False):
        # requests module only supports name and value, not expires / httpOnly / secure
        for _item in cookies:
            if auto_extract and format(_item['value']) in self.variables.keys():
                self.variables[_item['value']]['flag'] = 1
                the_dict["cookies.{}".format(_item['name'])] = '${' + "{}".format(self.variables[_item['value']]['key']) + '}'
            else:
                the_dict["cookies.{}".format(_item['name'])] = _item['value']

    # check if the url matches include option
    @staticmethod
    def __if_include(url, include):
        if not include:
            return True
        if not isinstance(include, (list, tuple, set)):
            include = [include, ]
        for _in in include:
            if format(_in).strip() in url:
                return True
        return False

    # check if the url matches exclude option
    @staticmethod
    def __if_exclude(url, exclude):
        if not exclude:
            return False
        if not isinstance(exclude, (list, tuple, set)):
            exclude = [exclude, ]
        for _ex in exclude:
            if format(_ex).strip() in url:
                return True
        return False


if __name__ == '__main__':
    set_logger(mode=1, level='debug')
    cp = CaseParser()
    cp.auto_template(target='../demo')
    cp.case_replace(suite_or_case='../demo/test_cases',
                    target='../demoNew',
                    rules=['xxxId=>abcedjlsje', 'apiX::ABCD=>HAHAHA', 'date=>${{today}}'])
    
    case = cp.source_to_case(source='../demo/parrot-demo.har',
                             target='../demo',
                             include=[], exclude=['.js', '.css'],
                             validate_include=[], validate_exclude=['timestamp', 'tag', 'token'],
                             auto_extract=False)
    print(json.dumps(case, ensure_ascii=False))
    case = cp.load_test_case(suite_or_case='../demo/test_suites', environment='production')
    print(json.dumps(case, ensure_ascii=False))
