# Parrot - 基于录制和回放模式的，面向HTTP请求的自动化测试方案

## 1. 设计思路：测试 == 流量回放

软件测试的经典定义：

> 使用**人工**或**自动**的手段来运行或测定某个软件系统的过程，其目的在于检验它是否满足**规定的需求**或弄清**预期结果**与**实际结果**之间的差别
>
>   -- *来自1983年，IEEE提出的软件工程术语*

简化一些的定义：
> 按照规定的需求/步骤，运行系统或应用程序，得到实际结果，和预期结果进行比较的过程

对照来看一下流量回放的过程：

- 录制：拿到/定义**规定的需求**和**预期的结果**
- 回放：执行**录制的脚本**，得到**实际的结果**
- 验证：对比**预期的结果**和**实际的结果**

**流量回放**，就是参照**测试原本定义**，进行自动化变现的一种思路

**本项目就是基于该思路进行的接口自动化方案的设计，在第3章节会进行具体的拆解**

## 2. 使用说明

### 2.0 Install

iParrot项目已提交到PyPI，安装方式：

1. 可使用`pip install iParrot`命令进行安装
2. 也可下载源码包，使用`python setup.py`进行安装

安装完成后，会生成`parrot`可执行文件，可尝试`parrot help`

### 2.1 Usage
#### 查看Parrot支持的命令：`parrot help`

其中，两个核心命令分别是：**record - 录制**，**replay - 回放**

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

#### 录制命令的用法：`parrot help record`

该步骤的目的是将用户指定的源文件（目前为.har）解析生成为标准化的用例集

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

#### 回放命令的用法：`parrot help replay`

该步骤是执行指定的测试用例集，并生成测试报告

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
  │    ├── helper.py    : 常用方法集合，其中的Function可用于其他module，同时支持在case中以${{function(params)}}的方式使用
  │    ├── request.py   : 基于`requests`，执行HTTP(S)的请求并拿到结果
  │    ├── validator.py : 针对接口响应信息的验证引擎，支持多种验证规则，详见其中的Validator.UNIFORM_COMPARATOR
  │    ├── logger.py    : 格式化日志打印，支持输出到屏幕或日志文件
  │    └── reportor.py  : 标准化报告打印，可查看汇总结果和用例执行明细
  ├── extension
  │    └── helper.py    : 可由用户自定义的常用方法集合，其中的Function支持在case中以${{function(params)}}的方式使用
  ├── parser.py : 解析源文件，自动生成格式化的用例；解析指定的用例集，load到内存中
  ├── player.py : 回放指定的用例集，按层级执行，最终生成测试报告
  └── parrot.py : 主脚本, 可执行`python parrot.py help`来查看具体用法

```

## 3. 具体的设计思路

### 3.1.1 录制 - 如何定义需求/步骤
***

#### 模式一（推荐）：基于抓包导出的HAR（HTTP Archive Resource）文件自动生成

HAR为储存HTTP请求和响应的通用标准化格式

- 其通用性体现在：Charles、Fiddler、Chrome等均可导出且格式一致
- 其标准化体现在：JSON格式和UTF-8统一编码

基于抓包源文件，可以自动解析生成符合一定规则的测试用例，规则可以对齐到下面的模式二
	
> 大家日常进行项目测试及回归，均有机会"顺手"留存抓包记录，其中包含**完整**且**真实**的用户场景及接口调用现场，胜过手工“编造”用例
> 
> Parrot一期处理的文件为Charles trace和Fiddler txt，格式上差异较大，且纯文本的解析较为繁琐

#### 模式二：按照统一规格进行自定义

自动化用例进行分层、标准化设计，便于自动生成、手工编辑、灵活组装，（部分参考了Postman和HttpRunner，后文有提及）

```
project/
  ├── environments
  │    └── *env*.yml：项目级环境变量配置，可配置多套通用的变量，方便在step、case、suite中切换，减少修改成本
  ├── test_steps
  │    └── *case_name*.yml：最小执行单元，一个接口请求即为一个step，可独立配置变量、前置步骤、后置步骤等
  ├── test_cases
  │    └── *case_name*.yml：独立闭环单元，由一到多个step组成，可独立配置变量、前置步骤、后置步骤等
  └── test_suites
       └── *suite_name*.yml：测试用例集合，由一到多个case组成，各case之间无强依赖，可独立配置变量、前置步骤、后置步骤等
```
以上用例组织结构，在模式一的HAR文件解析中均可自动构建，也可严格按照标准化格式自行构建、人为编辑

**具体单元格式：**

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

#### 模式三：基于标准化的生产日志

日志信息中要包含足够的信息，符合统一的格式定义
> 受限于具体项目的日志规范差异和信息完备性，本项目暂不考虑该模式
> 
> 感兴趣的同学可以参考模式二的格式定义，自行实现**录制**的脚本开发

### 3.1.2 录制 - 如何定义预期结果
***

#### 模式一（推荐）：基于抓包导出的HAR（HTTP Archive Resource）文件自动生成

流量回放的一个基础思路就是：**录制的流量是可靠的**，那么当时的响应信息就可以作为我们**预期结果**的重要参考

其中我们可以作为依据的重要信息有：

```
- Status Code：最基本的可用与否验证，通常放在第一步
- Content text：核心验证的部分，通常为json格式，便于进一步分解更细致的key/value
- Headers：部分项目会将一些自定义的key放到header中返回，需要单独关注
- Timing：接口响应的耗时，不做强预期，可以用来做一定的对照
```

Parrot的录制阶段，默认从录制样本中提取全部的响应信息作为预期结果（支持`--include``--exclude`的传参筛选），格式参见下面模式二的定义

#### 模式二：按照统一规格进行自定义

在3.1.1的模式二中，test_step的定义中有关于validations的示例，用户可参照该格式进行自定义

```
validations:
- <comparator>:
    <check>: <expected result>
```

其中的`check`，按照上面模式一中的重要信息，采用统一格式：<一级前缀>.<组合KEY>

- 一级前缀有：`status`, `content`, `headers`, `cookies`，统一小写
- `status`下的key，目前有：`code`
- `headers`和`cookies`下的key，目前仅提取其外层key
- `content`下的key，目前仅支持json模式，多个层级的写法为：`content.a.b[1].c`

其中的`expected result`，自动生成时默认使用录制样本中的值，可人为编辑

其中的`comparator`，自动生成时默认为`eq`，可人为编辑，目前Parrot支持的验证方法(comparator)主要有：

- **eq(equals): 相等**
	- 示例：`1 eq 1`, `'a' eq 'a'`, `[1, 2] eq [1, 2]`, `{'a': 1 } eq {'a': 1}`, `status.code eq 200`
	- 类似的方法：`neq`, `lt`, `gt`, `le`, `ge`
- **len_eq(length equals): 长度相等**
	- 示例：`'ab' len_eq 2`, `[1, 2] len_eq 2`, `{'a': 1} len_eq 1`
	- 类似的方法：`len_neq`, `len_lt`, `len_gt`
- **contains: 包含**
	- 示例：`'abc' contain 'ab', ['a', 'b'] contain 'a', {'a': 1, 'b': 2} contain {'a': 1}`
	- 类似的方法：`not_contains`
- **in: 被包含**
	- 示例：`'a' in 'ab'`, `'a' in ['a', 'b']`, `'a' in {'a': 1, 'b': 2}`
	- 类似的方法：`not_in`
- **is_false: 空**
	- 示例：`0 is_false`, `'' is_false`, `[] is_false`, `{} is_false`
	- 类似的方法：`is_true`, `exists`, `is_instance`, `is_json`
- **re(regex): 匹配**
	- 示例：`'1900-01-01' re r'\d+-\d+-\d+'`
	- 类似的方法：`not_re`

更多具体的验证方法，可以查看`iparrot.modules.validator.Validator.UNIFORM_COMPARATOR`

### 3.2.1 回放 - 运行的顺序问题
***

Parrot的请求执行基于`requests`，目前仅支持HTTP(S)的请求

#### 执行顺序：按照*test_suite*.yaml / *test_case*.yaml中定义的case和step的次序执行，目前仅支持串行执行模式

> 自动生成用例时，step的排序默认按照录制样本中的出场顺序，可人为编辑

详细的执行流程为：

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

#### 执行间隔：优先传参`interval`，默认step的`time.start`

若回放传参指定了`interval`，则按照该间隔执行；否则，若step的request中定义了`time.start`，则默认按照各个step的`time.start`的间隔执行；否则，一个接一个连续执行

> 自动生成用例时，每个step会记录其实际出场的时间`time.start`，默认按照各个step间的录制间隔执行

### 3.2.2 回放 - 如何解决实时传参问题
***
#### 需要实时生成的传参

以查询类接口为例，接口的需求是查询明天的数据，录制所记录下来的传参是静态值，改天运行的话就不符合需求了，此时就需要实时生成该参数

Parrot支持的方式为:`${{function(params)}}`，其中的`function`，在iparrot.modules.helper中提供了很多常用的方法，可直接使用；同时，用户也可以在iparrot.extension.helper中补充自己的方法

示例:

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

#### 依赖前序接口响应的传参

以订单类接口为例，订单详情接口的订单号传参依赖订单创建接口的实时返回，如果直接回放录制时的数据，就此单非彼单了

Parrot的解决方案为：在订单创建接口的`response`中配置`extract`提取特定的key(订单号)，在订单详情接口的`request`中采用`${variable}`的格式进行引用

示例：

订单创建接口：

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

订单详情接口：

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


### 3.3.1 验证 - 如何进行对比
***

3.1.2中讲过了对`预期结果`的定义，包含`check`对象、`comparator`方法和`expected result`

3.2.1中进行请求回放的过程中，可以实时的拿到`actual result(实际结果)`，因此可以即时的进行结果的校验，依次看各个`check`对象的值是否符合`comparator`规则，**有一项失败则整个step失败**

单个step失败后，目前Parrot默认是不终止回放的执行的，但用户可以通过运行参数进行一些干预：

- --fail_stop: 若指定，则某个step验证失败后即终止运行
- --fail\_retry_times: 某个step失败后的重试次数，默认不重试
- --fail\_retry_interval: 某个step失败后重试间隔时间


## 4. 外部借鉴，感谢
### 4.1 [Postman](https://learning.getpostman.com/)

#### 4.1.1 环境管理机制

Parrot用例结构中的environment参考了该机制

```
一个项目可以配置多套环境，用来保存一些通用的环境变量，
不同环境之间，变量名保持一致，变量值可有差异，
在用例中通过${variable}的方式引用变量即可，减少手工修改
运行环境的切换，可以在replay阶段通过--env参数指定即可
```

#### 4.1.2 用例分层模式
 - Collection => test_suite
 - Folder => test_case
 - Request => test_step

#### 4.1.3 前后置动作
 - Pre-request Script => setup_hooks
 - Tests => teardown_hooks & validations
    
### 4.2 [HttpRunner](https://github.com/httprunner/httprunner)

#### 4.2.1 [HAR2Case](https://github.com/HttpRunner/har2case)


Parrot第一版录制解析的对象为Charles.trace和Fiddler.txt，解析略繁琐

后来在HttpRunner的思路借鉴下改用HAR进行了record部分的重构，同时传参方面进行了一些增改

详见`parrot help record`和`iparrot.parser`

#### 4.2.2 用例分层模式

HttpRunner的TestSuite>TestCase>TestStep的分层规则很好，采用拿来主义

Parrot在自动生成时，直接落实到目录结构上，同时对具体的用例结构有所增改

#### 4.2.3 setup hooks & teardown hooks

Parrot复用该命名方式，其中支持`set variable`, `call function`, `exec code`

#### 4.2.4 extract变量提取

Parrot第一版采用store+replace的方式，意在将所有的变化都限制在一个配置文件中，而完全不侵入用例，实际使用中发现易用性不佳，配置略繁琐

参考HttpRunner，将主动权交还给用户，可自行选取变量进行`extract`和`${variable}`引用

#### 4.2.5 comparator

Parrot第一版采用diff结合配置的方式，仅支持`eq`和简单的`re`，方法集有限

现在参考HttpRunner的方式，录制时默认生成`eq`comparator，同时支持多种comparator的自定义，结合了HttpRunner和Postman的常用验证方法，并进行了一定的增补

#### 4.2.6 report

Parrot的测试报告模板直接复用了HttpRunner的报告样式
