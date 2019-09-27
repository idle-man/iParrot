# Parrot - Automated test solution for http requests based on recording and playback

## 1. Design Idea: Test == Traffic Playback

Classic definition of software testing: 

> The process of using a **manual** or **automated** means to run or measure a software system, the purpose of which is to verify that it meets **specified requirements** or to clarify the difference between **expected** and **actual** results.
>
>   -- *Software engineering terminology from IEEE in 1983*

A simplified definition: 
> The process of running a system or application in accordance with defined requirements/steps, obtaining actual result, and comparing with the expected result

Look at the process of traffic playback:

- Recording: Get/Define specified requirement and **expected result**
- Playback: Perform the recorded script to get the **actual result**
- Verify: Compare the **expected** and **actual** results

**Traffic playback** is a way to automate the realization of the **original definition of the test**.

**This project is based on this idea to automatically test api, in Chapter 3 there will be a specific disassembly.**

## 2. Instruction for use

### 2.0 Install

The iParrot project has been submitted to PyPI, installation way:

1. Run `pip install iParrot` command.
2. Or download the source code pkg, and run `python setup.py` command.

After installation, the `parrot` executable is generated, you could try `parrot help`.

### 2.1 Usage
#### View commands supported by Parrot: `parrot help`

Among them, the two core commands are: **record**，**replay**

```
$ parrot help
Automated test solution for http requests based on recording and playback
Version: 1.0.0

Usage: parrot [-h] [-v] [command] [<args>]

command:
  record - parse source file and generate test cases
      see detail usage: parrot help record
  replay - run the recorded test cases and do validations
      see detail usage: parrot help replay

optional arguments:
  -h, --help         show this help message and exit
  -v, -V, --version  show version
```

#### View the usage of `record` command: `parrot help record`

The purpose of this step is to parse the user-specified source file (currently .har) into a standardized set of use cases.

```
$ parrot help record
Automated test solution for http requests based on recording and playback
Version: 1.0.1

Usage: parrot record [<args>]

Arguments:
  -s, --source SOURCE   source file with path, *.har [required]
  -t, --target TARGET   target output path, 'ParrotProject' as default
  -i, --include INCLUDE include filter on url, separated by ',' if multiple
  -e, --exclude EXCLUDE exclude filter on url, separated by ',' if multiple
  -vi, --validation-include V_INCLUDE
                        include filter on response validation, separated by ',' if multiple
  -ve, --validation-exclude V_EXCLUDE  
                        exclude filter on response validation, separated by ',' if multiple
  
  --log-level LOG_LEVEL log level: debug, info, warn, error, info as default
  --log-mode  LOG_MODE  log mode : 1-on screen, 2-in log file, 3-1&2, 1 as default
  --log-path  LOG_PATH  log path : <project path> as default
  --log-name  LOG_NAME  log name : parrot.log as default

```

#### View the usage of `replay` command: `parrot help replay`

This step is to execute the specified set of test cases and generate a test report.

```
$ parrot help replay
Automated test solution for http requests based on recording and playback
Version: 1.0.1

Usage: parrot replay [<args>]

Arguments:
  -s, --suite, -c, --case SUITE_OR_CASE
                        test suite or case with path, *.yml or folder [required]
  -o, --output OUTPUT   output path for report and log, 'ParrotProject' as default
  -i, --interval INTERVAL
                        interval time(ms) between each step, use the recorded interval as default
  -env, --environment ENVIRONMENT
                        environment tag, defined in project/environments/*.yml
  -reset, --reset-after-case
                        exclude filter on url, separated by ',' if multiple

  --fail-stop FAIL_STOP stop or not when a test step failed on validation, False as default
  --fail-retry-times FAIL_RETRY_TIMES
                        max retry times when a test step failed on validation, 0 as default
  --fail-retry-interval FAIL_RETRY_INTERVAL 
                        retry interval(ms) when a test step failed on validation, 100 as default
                        
  --log-level LOG_LEVEL log level: debug, info, warn, error, info as default
  --log-mode  LOG_MODE  log mode : 1-on screen, 2-in log file, 3-1&2, 1 as default
  --log-path  LOG_PATH  log path : <project path> as default
  --log-name  LOG_NAME  log name : parrot.log as default

```

### 2.2 Framework Structure
```
parrot/
  ├── modules
  │    ├── helper.py    : A collection of commonly used methods in which the Function can be used in other modules, also supporting the use of ${{function(params)}} in the cases.
  │    ├── request.py   : Execute HTTP(S) request based on `requests` and get the result
  │    ├── validator.py : The verification engine for request's response information, which supports multiple verification rules, as detailed in Validator.UNIFORM_COMPARATOR
  │    ├── logger.py    : Formatted log printing, support for output to screen or log files
  │    └── reportor.py  : Standardized report printing, support for views of summary results and use case execution details
  ├── extension
  │    └── helper.py    : A collection of common methods that can be customized by the user, where the Function supports use as ${{function(params)}} in the cases
  ├── parser.py : Parse the source file, and automatically generate formatted use cases; parse the specified use case set, load into memory
  ├── player.py : Play back the specified set of use cases, execute them in levels, and finally generate a test report
  └── parrot.py : The main script, you can run `python parrot.py help` to see the specific usage

```

## 3. Specific design ideas

### 3.1.1 Recording - How to define the requirement/steps
***

#### Mode One(recommended): Automatic generation of HAR(HTTP Archive Resource) files exported from packet capture tools

HAR is a common standardized format for storing HTTP requests and responses

- Its versatility: can be exported with consistent format from Charles, Fiddler, Chrome, etc
- Its standardization: JSON format and UTF-8 coding

Based on the capture source file, you can automatically parse and generate test cases that meet certain formats. The formats can be aligned to the following Mode Two.
	
> In daily project testing and regression, people all have the opportunity to "save" the capture record, which includes complete and real user scenarios and interface call scenes, better than manual "draw up" use cases. 
> 
> The files processed by Parrot in the first phase are Charles trace and Fiddler txt. The format is quite different, and the parsing of plain text is cumbersome.


#### Mode Two: Customize according to uniform specifications

Automated use cases are layered and standardized, for easy automatic generation, manual editing, and flexible assembly (partial reference to Postman and HttpRunner, mentioned later)

```
project/
  ├── environments
  │    └── *env*.yml: Project-level environment variable configuration, can configure multiple sets of common variables, easy to switch in step, case, suite, reduce modification cost
  ├── test_steps
  │    └── *case_name*.yml: The minimum execution unit, a http request is a step, which can be independently configured with variables, pre-steps, post-steps, etc.
  ├── test_cases
  │    └── *case_name*.yml: Independent closed-loop unit,  consisting of one or more steps, which can be independently configured with variables, pre-steps, post-steps, etc.
  └── test_suites
       └── *suite_name*.yml: Test case set, consisting of one or more cases, no strong dependencies between cases, independent configuration variables, pre-steps, post-steps, etc.
```
The above use case organization structure can be automatically constructed in the HAR file parsing of Mode One, or it can be constructed and edited in strict accordance with the standardized format.

**Specific format:**

- **environment**

	```yaml
	global: {}
	production: {}
	development: {}
	test: {}
	```
- **test_step**

	```yaml
	config:
	  environment: <environment flag>
	  import: <environment file>
	  name: step name
	  variables:
	    p1: ABC
	    p2: 123
	request:
	  method: POST
	  protocol: http
	  host: x.x.x.x:8000
	  url: /path/of/api
	  params: {}
	  data:
	    param1: ${p1}
	    param2: ${p2}
	  headers:
	    Content-Type: application/json; charset=UTF-8
	  cookies: {}
	  time.start: 1568757525027
	response:
	  extract: {}
	setup_hooks: []
	teardown_hooks: []
	validations:
	- eq:
	    status.code: 200
	- exists:
	    headers.token
	- is_json:
	    content
	- eq:
	    content.code: 100
	```
- **test_case**

	```yaml
	config:
	  environment: <environment flag>
	  import: <environment file>
	  name: case name
	  variables: {}
	setup_hooks: []
	teardown_hooks: []
	test_steps:
	  - <fullname of step1>
	  - <fullname of step2>
	```
- **test_suite**

	```yaml
	config:
	  environment: <evnironment flag>
	  import: <environment file>
	  name: suite name
	  variables: {}
	setup_hooks: []
	teardown_hooks: []
	test_cases: 
	  - <fullname of case1>
	  - <fullname of case2>
	```

#### Mode Three: Based on standardized production logs
The log information should contain enough information and be defined in a uniform format.

> Limited by the log specification differences and information completeness of specific projects, this project will not consider this mode for the time being.
> 
> Interested users can refer to the format definition of Mode Two, and implement the script development of **recording**.

### 3.1.2 Recording - How to define the expected result
***

#### Mode One(Recommended): Automatic generation of HAR(HTTP Archive Resource) files exported from packet capture tools

A basic idea of ​​traffic playback is that the recorded traffic is reliable, then the response information at that time can be used as an important reference for our expected results.

The important information we can use:

```
- Status Code: The most basic availability verification, usually placed in the first step
- Content text: The core verification part, usually in json format, to further break down the more detailed key/value
- Headers: Some projects will return some custom keys in the header, which requires separate verification
- Timing: The time-consuming of the request, which is not needed to strongly verify, but can be used to make certain comparisons
```

During the recording phase of Parrot, the default response information is extracted from the recorded samples as the expected result (supporting the filtering of `--include``--exclude`). 

For the format, see the definition of Mode Two below.

#### Mode Two: Customize according to uniform specifications

In Mode Two of Chapter 3.1.1, there are examples of validations in the definition of test_step, which users can customize with reference to this format:

```
validations:
- <comparator>:
    <check>: <expected result>
```

The `check`: According to the important information in the above Mode One, the unified format is: \<PREFIX>.\<KEYS>

- Available PREFIX: `status`, `content`, `headers`, `cookies`, in lower case
- KEYS in `status`: `code`
- KEYS in `headers` and `cookies`: Currently only extracting the outer keys
- KEYS in `content`(json format): `content.a.b[1].c`

The `expected result`: The value in the recorded sample is used by default when automatically generated, which can be edited manually.

The `comparator`: The default is `eq` when it is automatically generated, which can be edited manually. 

Currently, Parrot supports below comparators:

- **eq(equals)**
	- Example: `1 eq 1`, `'a' eq 'a'`, `[1, 2] eq [1, 2]`, `{'a': 1 } eq {'a': 1}`, `status.code eq 200`
	- Related comparators: `neq`, `lt`, `gt`, `le`, `ge`
- **len_eq(length equals)**
	- Example: `'ab' len_eq 2`, `[1, 2] len_eq 2`, `{'a': 1} len_eq 1`
	- Related comparators: `len_neq`, `len_lt`, `len_gt`
- **contains**
	- Example: `'abc' contain 'ab', ['a', 'b'] contain 'a', {'a': 1, 'b': 2} contain {'a': 1}`
	- Related comparators: `not_contains`
- **in**
	- Example: `'a' in 'ab'`, `'a' in ['a', 'b']`, `'a' in {'a': 1, 'b': 2}`
	- Related comparators: `not_in`
- **is_false**
	- Example: `0 is_false`, `'' is_false`, `[] is_false`, `{} is_false`
	- Related comparators: `is_true`, `exists`, `is_instance`, `is_json`
- **re(regex)**
	- Example: `'1900-01-01' re r'\d+-\d+-\d+'`
	- Related comparators: `not_re`

For more comparators, please refer to `iparrot.modules.validator.Validator.UNIFORM_COMPARATOR`

### 3.2.1 Playback - The order of execution
***
Parrot's request execution is based on `requests` module and currently only supports HTTP(S) requests.

#### Execution order: executed in the order of cases and steps defined in *test_suite*.yaml / *test_case*.yaml, currently only supports serial execution mode

> When the use case is automatically generated, the order of the steps defaults to the order of appearance in the recorded sample, which can be edited manually.

The detailed execution process:

```
test_suite1
 |-> suite1.setup
 |-> test_case1
   |-> case1.setup
   |-> test_step1
     |-> step1.setup
     |-> request
     |-> validation
     |-> extract
     |-> step1.teardown
   |-> test_step2
     ...
   |-> case1.teardown
 |-> test_case2
   ...
 |-> suite1.teardown
test_suite2
  ...
```

#### Execution interval: The value of `interval` argument is firstly used, otherwise the value `time.start` in step defination

If the playback parameter `interval` is specified, it will be executed according to the interval; otherwise, if the `time.start` is defined in the steps, it will be executed according to the interval of each step's `time.start`; otherwise, execute the steps one by one

> When the use case is automatically generated, the actual execution time would be recorded as `time.start` in the step defination.

### 3.2.2 Playback - How to support real-time parameters
***

#### Some parameters need to be generated in real time

Take the query request as an example. The requirement of the interface is to query the data of tomorrow. The recorded parameters are kept with static values. If the script is runned in the next day, it will not meet the requirements. In this case, the parameter needs to be generated in real time.

The Parrot solution is: use `${{function(params)}}` to generate real time value, where `function` is provided by  iparrot.modules.helper or self-defined iparrot.extension.helper.

Example:

```yaml
config:
  ...
  variables:
    p1: ABC
    p2: 123
    p3: ${{days_later(1)}}
request:
  method: GET
  ...
  params:
    param1: ${p1}
    param2: ${p2}
    date: ${p3}
  ...
```

#### Some parameters depend on the response of pre-order request

Taking the order type interface as an example, the order id of the order detail interface depends on the real-time return of the order creation interface. 

The Parrot solution is: Configure `extract` in the `response` defination of order creation interface step to extract specific order id, and use `${variable}` format to call the order id in order detail interface step.

Example:

Definition of order creation step:

```yaml
config:
  ...
request:
  ...
response:
  extract:
    oid: content.data.orderId
...
```

Defination of order detail step:

```yaml
config:
  ...
  variables:
    p1: ABC
    p2: 123
request:
  method: GET
  ...
  params:
    param1: ${p1}
    param2: ${p2}
    orderId: ${oid}
  ...
```


### 3.3.1 Validation - How to compate the expected and actual results
***

The definition of `expected result` is mentioned in chapter 3.1.2, including the `check` object, the `comparator` method, and the `expected result`.

In the process of request playback in chapter 3.2.1, you can get the `actual result` in real time, which you can check and see if the value of each `check` object conforms to the `comparator` rule. **If there is a failure, the entire step fails**

After a single step fails, the current Parrot does not terminate the execution of the playback by default, but the user can perform some intervention by running the parameters:

- --fail_stop: If specified, the operation will be terminated after a step verification fails
- --fail\_retry_times: The number of retries after a step failed, 0 as default
- --fail\_retry_interval: retry interval after a step failure


## 4. External reference, thanks
### 4.1 [Postman](https://learning.getpostman.com/)

#### 4.1.1 Environments management
The mechanism is referenced in the `environment` of the Parrot use case structure.

```
A project can be configured with multiple sets of environments to hold some common environment variables.

Variable names are consistent between different environments, and values ​​can vary.

In the use case, you can refer to the variable by means of ${variable}, reducing manual modification.

The switching of the operating environment can be specified in the replay phase by the --env parameter.
```

#### 4.1.2 Use case layering mode
 - Collection => test_suite
 - Folder => test_case
 - Request => test_step

#### 4.1.3 Pre and post actions
 - Pre-request Script => setup_hooks
 - Tests => teardown_hooks & validations
    
### 4.2 [HttpRunner](https://github.com/httprunner/httprunner)

#### 4.2.1 [HAR2Case](https://github.com/HttpRunner/har2case)

The files processed by Parrot in the first phase are Charles trace and Fiddler txt. The format is quite different, and the parsing of plain text is cumbersome.

Later, in the course of HttpRunner's ideas, I used HAR to reconstruct the record part. At the same time, I made some changes in the parameters.

Inspired by HttpRunner's ideas, the record part is rebuilt, and some paramters are updated.

For details, to see `parrot help record` and `iparrot.parser`

#### 4.2.2 Use case layering mode

The use case layering mode of HttpRunner, TestSuite>TestCase>TestStep, is clear and a good reference.

When Parrot automatically generates use cases, it directly implements the layering mode on the directory structure and changes the specific use case structure.

#### 4.2.3 setup hooks & teardown hooks

Parrot reuses this naming scheme, which supports `set variable`, `call function`, `exec code`.

#### 4.2.4 extract variable

Parrot in the first phase uses the mode of `store` and `replace`, which is intended to keep all changes in a configuration file, and does not invade the use case at all. 

In actual use, it is found that the usability is not good and the configuration is slightly cumbersome.

Refer to HttpRunner, return the initiative to the user, and the variable can be extracted according to `extract` defination and used as `${variable}`.

#### 4.2.5 comparator

The first version of Parrot diffs results refer to a  configuration file, only supports `eq` and simple `re`, and the method set is limited.

Now refer to the HttpRunner, automatically generate `eq` comparator when recording, and support a variety of comparator customization.

Comparators in Parrot combines with the common verification methods of HttpRunner and Postman, and a certain supplement.

#### 4.2.6 report

Parrot's test report template directly reuses HttpRunner's report style.

