# -*- coding: utf-8 -*-

import sys
from argparse import ArgumentParser

from iparrot import __version__, __description__


usage = """{}
Version: {}

Usage: parrot [-h] [-v] [command] [<args>]

command:
  record - parse source file and generate test cases
      see detail usage: `parrot help record`
  replay - run the recorded test cases and do validations
      see detail usage: `parrot help replay`

optional arguments:
  -h, --help         show this help message and exit
  -v, -V, --version  show version
""".format(__description__, __version__)

record_usage = """{}
Version: {}

Usage: parrot record [<args>]

Arguments:
  -s, --source SOURCE   source file with path, *.har or directory[required]
  -t, --target TARGET   target output path, 'ParrotProject' as default
  -i, --include INCLUDE include filter on url, separated by ',' if multiple
  -e, --exclude EXCLUDE exclude filter on url, separated by ',' if multiple
  -vi, --validation-include V_INCLUDE
                        include filter on response validation, separated by ',' if multiple
  -ve, --validation-exclude V_EXCLUDE  
                        exclude filter on response validation, separated by ',' if multiple
  -ae, --auto-extract   automatic identification of interface dependencies or not, False as default
  
  --log-level LOG_LEVEL log level: debug, info, warn, error, info as default
  --log-mode  LOG_MODE  log mode : 1-on screen, 2-in log file, 3-1&2, 1 as default
  --log-path  LOG_PATH  log path : <project path> as default
  --log-name  LOG_NAME  log name : parrot.log as default
""".format(__description__, __version__)

replay_usage = """{}
Version: {}

Usage: parrot replay [<args>]

Arguments:
  -s, --suite, -c, --case SUITE_OR_CASE
                        test suite or case with path, *.yml or directory [required]
  -t, --target TARGET   output path for report and log, 'ParrotProject' as default
  -i, --interval INTERVAL
                        interval time(ms) between each step, use the recorded interval as default
  -env, --environment ENVIRONMENT
                        environment tag, defined in project/environments/*.yml
  -reset, --reset-after-case
                        reset runtime environment or not, False as default

  --fail-stop           stop or not when a test step failed on validation, False as default
  --fail-retry-times FAIL_RETRY_TIMES
                        max retry times when a test step failed on validation, 0 as default
  --fail-retry-interval FAIL_RETRY_INTERVAL 
                        retry interval(ms) when a test step failed on validation, 100 as default
                        
  --log-level LOG_LEVEL log level: debug, info, warn, error, info as default
  --log-mode  LOG_MODE  log mode : 1-on screen, 2-in log file, 3-1&2, 1 as default
  --log-path  LOG_PATH  log path : <project path> as default
  --log-name  LOG_NAME  log name : parrot.log as default
""".format(__description__, __version__)


def main_help():
    opt = ArgumentParser(usage=usage)
    opt.add_argument("command", action="store", default=None, nargs="*",
                     help="record / replay")
    opt.add_argument('-v', '-V', '--version', dest="version", action="store_true", default=False,
                     help="show version")
    args = opt.parse_args()

    if args.version:
        print(__version__)
        opt.exit()

    if not args.command:
        print(usage)
        opt.exit()
    command = args.command[0].lower()
    if command not in ('help', 'record', 'replay', 'playback', 'run', 'listen', 'talk'):
        print(usage)
        opt.exit()
    elif command == 'help' and len(args.command) > 1:
        action = args.command[1].lower()
        if action in ('record', 'listen'):
            print(record_usage)
        elif action in ('replay', 'playback', 'run', 'talk'):
            print(replay_usage)
        else:
            print(usage)
        opt.exit()
    else:
        print(usage)
        opt.exit()


def main_record():
    from iparrot.parser import CaseParser
    from iparrot.modules.logger import logger, set_logger

    opt = ArgumentParser(usage=usage)
    opt.add_argument('-s', '-S', '--source', dest="source", action="store", default=None,
                     help="source file with path, *.har or directory")
    opt.add_argument('-t', '-T', '--target', '-o', '-O', '--output', dest="target", action="store", default='ParrotProject',
                     help="target output path, 'ParrotProject' as default")
    opt.add_argument('-i', '-I', '--include', dest="include", action="store", default=None,
                     help="include filter on url, separated by ',' if multiple")
    opt.add_argument('-e', '-E', '--exclude', dest="exclude", action="store", default=None,
                     help="exclude filter on url, separated by ',' if multiple")
    opt.add_argument('-vi', '-VI', '--validation-include', dest="v_include", action="store", default=None,
                     help="include filter on response validation, separated by ',' if multiple")
    opt.add_argument('-ve', '-VE', '--validation-exclude', dest="v_exclude", action="store", default=None,
                     help="exclude filter on response validation, separated by ',' if multiple")
    opt.add_argument('-ae', '-AE', '--auto-extract', dest="auto_extract", action="store_true", default=False,
                     help="automatic identification of interface dependencies or not")

    opt.add_argument('--log-level', dest="log_level", action="store", default="info",
                     help="log level: debug, info, warn, error, info as default")
    opt.add_argument('--log-mode', dest="log_mode", action="store", default=1,
                     help="log mode: 1-on screen, 2-in log file, 3-1&2, 1 as default")
    opt.add_argument('--log-path', dest="log_path", action="store", default=None,
                     help="log path: <project path> as default")
    opt.add_argument('--log-name', dest="log_name", action="store", default="parrot.log",
                     help="log name: parrot.log as default")
    args = opt.parse_args()
    if not args.source:
        print(record_usage)
        opt.exit()

    set_logger(
        mode=int(args.log_mode),
        level=args.log_level,
        path=args.log_path if args.log_path else args.target,
        name=args.log_name
    )
    parser = CaseParser()
    parser.source_to_case(
        source=args.source,
        target=args.target,
        include=args.include.split(',') if args.include else [],
        exclude=args.exclude.split(',') if args.exclude else [],
        validate_include=args.v_include.split(',') if args.v_include else [],
        validate_exclude=args.v_exclude.split(',') if args.v_exclude else [],
        auto_extract=args.auto_extract
    )


def main_replay():
    from iparrot.player import Player
    from iparrot.modules.logger import logger, set_logger

    opt = ArgumentParser(usage=usage)
    opt.add_argument('-s', '-S', '--suite', '-c', '-C', '--case', dest="suite_or_case", action="store", default=None,
                     help="test suite or case with path, *.yml or directory")
    opt.add_argument('-t', '-T', '--target', '-o', '-O', '--output', dest="target", action="store", default='ParrotProject',
                     help="output path for report and log, 'ParrotProject' as default")
    opt.add_argument('-i', '-I', '--interval', dest="interval", action="store", default='ms',
                     help="interval time(ms) between each step, use the recorded interval as default")
    opt.add_argument('-env', '--environment', dest="environment", action="store", default=None,
                     help="environment tag, defined in project/environments/*.yml")
    opt.add_argument('-reset', '--reset-after-case', dest="reset_after_case", action="store_true", default=False,
                     help="reset runtime environment or not, False as default")

    opt.add_argument('--fail-stop', dest="fail_stop", action="store_true", default=False,
                     help="stop or not when a test step failed on validation, False as default")
    opt.add_argument('--fail-retry-times', dest="fail_retry_times", action="store", default=0,
                     help="max retry times when a test step failed on validation, 0 as default")
    opt.add_argument('--fail-retry-interval', dest="fail_retry_interval", action="store", default=100,
                     help="retry interval(ms) when a test step failed on validation, 100 as default")

    opt.add_argument('--log-level', dest="log_level", action="store", default="info",
                     help="log level: debug, info, warn, error, info as default")
    opt.add_argument('--log-mode', dest="log_mode", action="store", default=1,
                     help="log mode: 1-on screen, 2-in log file, 3-1&2, 1 as default")
    opt.add_argument('--log-path', dest="log_path", action="store", default=None,
                     help="log path: <project path> as default")
    opt.add_argument('--log-name', dest="log_name", action="store", default="parrot.log",
                     help="log name: parrot.log as default")
    args = opt.parse_args()
    if not args.suite_or_case:
        print(replay_usage)
        opt.exit()

    set_logger(
        mode=int(args.log_mode),
        level=args.log_level,
        path=args.log_path if args.log_path else args.target,
        name=args.log_name
    )
    player = Player()
    player.run_cases(
        suite_or_case=args.suite_or_case,
        environment=args.environment,
        interval=args.interval,
        reset_after_case=args.reset_after_case,
        fail_stop=args.fail_stop,
        retry_times=args.fail_retry_times,
        retry_interval=args.fail_retry_interval,
        output=args.target
    )


def main():
    if len(sys.argv) == 1:
        sys.argv.append('help')
        main_help()
    elif sys.argv[1].lower() in ('help', '-h', '--help'):
        sys.argv[1] = 'help'
        main_help()
    elif sys.argv[1].lower() in ('version', '-v', '--version'):
        sys.argv[1] = '-v'
        main_help()
    elif sys.argv[1].lower() in ('record', '--record', 'listen', '--listen'):
        del sys.argv[1]
        main_record()
    elif sys.argv[1].lower() in ('replay', '--replay', 'playback', '--playback', 'run', '--run', 'talk', '--talk'):
        del sys.argv[1]
        main_replay()
    else:
        sys.argv[1] = 'help'
        main_help()

