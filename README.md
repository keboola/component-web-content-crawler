# KBC Selenium Web Robot

A Keboola Connection component allowing to perform variety of web browser operations on any web-site and download web
content into the Storage. It is useful for instance for navigating through a legacy system web interface and downloading
a generated report that would be impossible to export in an automated manner otherwise.

The robot emulates in docker mode emulates display with resolution set by default to `1920X1080`, this can be overriden
by configuration parameter. It runs `Chrome` browser version `73.0.3683.20` operating with window size of `1024x980`, it
is possible to maximize the window on the startup to match the screen. The browser is run with configuration
parameter `--no-sandbox` and driver option `"safebrowsing.enabled": False`.

**Table of contents:**

[TOC]

# Configuration

The robot is configurable via JSON, where you define each `Action` as an object. These `Action` objects define a real
web browser action a user would make, e.g. click an object, fill in a form, etc.

## Configuration Structure

```json
{
  "start_url": "https://www.example.com/",
  "random_wait_range": [
    1,
    5
  ],
  "user_parameters": {
    "username": "user@gmail.com",
    "#password": "XXX"
  },
  "store_cookies": false,
  "docker_mode": false,
  "steps": [
    {
      "description": "Step description, useful for debugging.",
      "actions": [
        {
          "description": "Action description, useful for debugging",
          "action_name": "ACTION_NAME",
          "action_parameters": {
          }
        }
      ]
    }
  ]
}
```

**Parameters**

- **start_url** – An URL of the page where the crawler starts off.
- **random_wait_range** - A time range in seconds defining how long should the crawler wait between each action. The
  interval is defined by boundaries in seconds, e.g. [1, 5] means that the crawler will wait between each action
  anywhere between 1s and 5s, the actual wait time is chosen randomly within these boundaries.
- **resolution** - (OPT) resolution of the screen as a string, e.g. `1024x980`. The default value is `1920x1080`.
- **maximize_window** - (OPT) Boolean value flagging whether to maximize the window to match the max resolution. Default
  is `false`.
- **page_load_timeout** - (OPT) Numeric value (seconds) of how long the renderer should wait before timing out for page load or script execution (e.g. clicking a button "generate report"). Default value is 1000s
- **user_parameters** – A list of user parameters that is are accessible from within actions. This is useful for storing
  for example user credentials that are to be filled in a login form. Appending `#` sign before the attribute name will
  hash the value and store it securely within the configuration (recommended for passwords). The value may be scalar or
  a supported function.
- **store_cookies** – If set to true the crawler will store cookies from the last time and use it every consecutive run.
  This is useful for storing credentials and also making the browser legit for the target system, e.g. logging in with
  Google.
- **docker_mode** - Set to `true` for run in KBC. This option enables display emulation so it can be run in Docker
  container without a `headless` mode. Set to `false` for local development, so you can see the actual browser on your
  local machine.
- **Steps** – An array of `Step` objects that are grouping a set of `Actions`. More information in sections below.

## "Step" objects

Steps are groups of actions. It is used to logically structure steps taken on the web site and also to divide different
branches of execution. For instance: Logging, Navigating, Download file.

Future version will support iterations on a particular step.

```json
{
  "description": "Step description, useful for debugging.",
  "Actions": [
    {
      "description": "Action description, useful for debugging",
      "action_name": "ACTION_NAME",
      "action_parameters": {
      }
    }
  ]
}
```

## Actions

Action define a user action in the browser, e.g. click, fill in a form, wait, navigate to pop-up window, etc.

**Action object structure**

```json
{
  "description": "Action description, useful for debugging",
  "action_name": "ACTION_NAME",
  "action_parameters": {
  }
}
```

**Parameters**

- **description** - An Action description, useful for debugging. This description is also populated in the Job log
  during execution.
- **action_name** - Name of the particular supported action
- **action_parameters** - List of action parameters that are applicable for that particular action.

## **Actions on element**

- The element is defined by an [XPATH](https://www.w3schools.com/xml/xpath_intro.asp) expression.
- Either special actions or generic (
  any [action on WebElement](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html)
  supported by Selenium library)

### **ClickElementToDownload**w

This action clicks an element that leads to a file that should be stored in the Storage. It performs the click and waits
until the file is downloaded.

**Parameters**

- **xpath** - [REQ] XPATH defining the target element
- **delay** - [OPT] Wait time in seconds before the action is executed. Default value is `30`s.
- **timeout** - [OPT] Time in seconds that define the maximum time the action waits for the download. Default value
  is `60`s

```json
{
  "description": "Click Download",
  "action_name": "ClickElementToDownload",
  "action_parameters": {
    "xpath": "//a//span[contains(text(),'Download')]",
    "delay": 10,
    "timeout": 120
  }
}
```

### **WaitForElement**

This action waits for an element before it becomes available in the DOM. Useful to make sure the page is fully loaded -
e.g. all JS code is executed.

**Parameters**

- **xpath** - [REQ] XPATH defining the target element
- **delay** - [OPT] Timeout of the action in case the element is never available. Default value is `10`s.

```json
{
  "description": "Waiting until doc is loaded.",
  "action_name": "WaitForElement",
  "action_parameters": {
    "xpath": "//a[@href='/login']",
    "delay": 10
  }
}
```

### **MoveToElement**

This action waits moves mouse to the specified element. 

Executes the ActionChain method [move_to_element](https://selenium-python.readthedocs.io/api.html?highlight=mouse#selenium.webdriver.common.action_chains.ActionChains.move_to_element)

**Parameters**

- **xpath** - [REQ] XPATH defining the target element

```json
{
  "description": "Waiting until doc is loaded.",
  "action_name": "MoveToElement",
  "action_parameters": {
    "xpath": "//a[@href='/login']"
  }
}
```

### **GenericElementAction**

A generic action performed on the specified element. This action is a wrapper allowing execution of any method defined
for [`selenium.webdriver.remote.webelement`](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html)
. To see the list of all supported actions and its parameters see
the [selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html)

**Parameters**

- **xpath** - [REQ] XPATH defining the target element.
- **action_name** - [REQ] Any method name available in the `selenium.webdriver.remote.webelement` interface.
  e.g. `click`.
- **positional_arguments** - List of values as defined by the `webelement` method. e.g. ['My text']
  for `send_keys(value)` method
- **[other_parameters]** - any other parameters supported by the `selenium.webdriver.remote.webelement` interface. Note
  that the parameters must be specified exactly as they are defined on the method and all required parameters are
  needed.
- **description** - description of the action. Useful for debugging, the message is included in the job log on
  execution. Example below triggers
  the [send_keys](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webelement.html#selenium.webdriver.remote.webelement.WebElement.send_keys)
  method.

```json
{
  "description": "Fill in username",
  "action_name": "GenericElementAction",
  "action_parameters": {
    "xpath": "//input[@type='email']",
    "positional_arguments": {
      "attr": "username"
    },
    "method_name": "send_keys"
  }
}
```

## **System actions**

These actions are not related to web elements. They usually define actions on the Selenium driver itself. These include
for instance navigation between pop-up windows, explicit waiting, etc.

### **GenericDriverAction**

This action is a wrapper allowing execution of any method defined
for [`selenium.webdriver.remote.webdriver`](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#module-selenium.webdriver.remote.webdriver)
. To see the list of all supported actions and its parameters see
the [selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#module-selenium.webdriver.remote.webdriver)

**Parameters**

- **action_parameters** - any other parameters supported by
  the [webdriver](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#module-selenium.webdriver.remote.webdriver)
  interface. Note that the parameters must be specified exactly as they are defined on the method and all required
  parameters are needed.
- **action_name** - [REQ] Any method name available in the `selenium.webdriver` interface. e.g. `implicitly_wait`.
- **positional_arguments** - List of positional arguments as defined by the `webdriver` method.
- **description** - description of the action. Useful for debugging, the message is included in the job log on
  execution.

Example below triggers
the [implicitly_wait](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#selenium.webdriver.remote.webdriver.WebDriver.implicitly_wait)
method.

```json
{
  "description": "Wait",
  "action_name": "GenericDriverAction",
  "action_parameters": {
    "positional_arguments": [
      60
    ],
    "method_name": "implicitly_wait"
  }
}
```

### **DriverSwitchToAction**

This action is a wrapper allowing execution of any method defined
for [`selenium.webdriver.remote.webdriver`](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#module-selenium.webdriver.remote.webdriver)
. To see the list of all supported actions and its parameters see
the [selenium documentation](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html#module-selenium.webdriver.remote.webdriver)

**Parameters**

- **action_parameters** - any other parameters supported by
  the [webdriver.switch_to](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html?highlight=switch_to#selenium.webdriver.remote.webdriver.WebDriver.switch_to)
  interface. Note that the parameters must be specified exactly as they are defined on the method and all required
  parameters are needed.
- **action_name** - [REQ] Any method name available in the `selenium.webdriver.switch_to` interface. e.g. `frame`.
- **positional_arguments** - List of positional arguments as defined by the `webdriver.switch_to` method.
- **description** - description of the action. Useful for debugging, the message is included in the job log on
  execution.

**Supported methods examples**

- `default_content()`
- `frame(‘frame_name’)`
- `frame(1)`
- `parent_frame()`
- `window(‘main’)`

Example below triggers
the [frame](https://seleniumhq.github.io/selenium/docs/api/py/webdriver_remote/selenium.webdriver.remote.webdriver.html?highlight=switch_to#selenium.webdriver.remote.webdriver.WebDriver.switch_to_frame)
method. Switching to iframe with index 1.

```json
{
  "description": "Switch to frame",
  "action_name": "DriverSwitchToAction",
  "action_parameters": {
    "positional_arguments": [
      1
    ],
    "method_name": "frame"
  }
}
```

### **PrintHtmlPage**

This action is useful for debugging purposes, it allows to print out the full HTML code of a current page into the out
stream on a defined level.

Supported levels are:
CRITICAL = 50 ERROR = 40 WARNING = 30 INFO = 20 DEBUG = 10 NOTSET = 0

**Parameters**

- **log_level** - [OPT] Int number specifying the output log level.

```json
{
  "description": "Print whole page",
  "action_name": "PrintHtmlPage",
  "action_parameters": {
    "log_level": 10
  }
}
```

### **DownloadPageContent**

This action allows you to download whatever content is on the current or specified URL. The usecase may be downloading a
JSON, CSV or any arbitrary file that is on specified URL. The response is streamed, so it supports large files.

All context of the browser such as cookies is maintained.

Typical usecase would be to login in previous steps and then call this method to download.

**Parameters**

- **result_file_name** - [REQUIRED] Result file name, e.g. 'report.json' it will be stored in 'out/tables/report.json'
  location
- **url** - [OPT] Optional URL of the resource. If left empty the current url of the browser is downloaded.

```json
{
  "action_name": "DownloadPageContent",
  "description": "Download report JSON",
  "action_parameters": {
    "url": "https://example.com/finance/report",
    "result_file_name": "report.json"
  }
}
```

### **SaveCookieFile**

This action allows you to store current cookies in a file storage.

The cookies file will be stored in json format `out/files/cookies.json`. With the following structure:

```json
{
  "cookies": [
    {
      "domain": "xxx"
    }
  ]
}
```

**Parameters**

- **tags** - [REQUIRED] List of tags the file will be stored with
- **is_permanent** - [OPT] Optional flag If true the cookies.json file will be stored permanently. DEFAULT: False

```json
{
  "description": "Save Cookie",
  "action_name": "SaveCookieFile",
  "action_parameters": {
    "tags": [
      "test_tag"
    ],
    "is_permanent": true
  }
}
```

### **SwitchToPopup**

This action navigates to a newly opened pop-up window. This is useful for instance for navigating into a new window
populated on login button. After the work is done action `SwitchToMainWindow` should be used to navigate back to the
main window.

```json
{
  "description": "Navigating to login popup window",
  "action_name": "SwitchToPopup",
  "action_parameters": {}
}
```

### **SwitchToMainWindow**

This action navigates back to the main window. After the work is done action `SwitchToMainWindow` should be used to
navigate back to the main window.

```json
{
  "description": "Switch focus back to main window",
  "action_name": "SwitchToMainWindow",
  "action_parameters": {}
}
```

### **TakeScreenshot**

This action takes a screenshot of current state and stores it in specified location and optionally
in [ImgBB](https://imgbb.com/) repository.

**Parameters**

- **name** - [REQ] The name parameter must be specified and defines the name of the resulting png file.
  E.g. `"name": "main_page"` results in
  `data/screens/main_page.png` file.
- **folder** - [OPT] Specifies the screenshot folder name in the `/data` folder. By default set to `screens`
- **imgbb_token** - [OPT] Your personal [imgbb token](https://api.imgbb.com/). The resulting files are stored in
  form `[KBC_RUNID]_[name].png`

```json
{
  "description": "Take screenshot of a main page",
  "action_name": "TakeScreenshot",
  "action_parameters": {
    "name": "main_page",
    "folder": "out/files",
    "#imgbb_token": "sasdasdasd"
  }
}
```

### **Wait**

This action pauses execution for specified amount of time (in seconds).

```json
{
  "description": "Pause execution for 10s",
  "action_name": "Wait",
  "action_parameters": {
    "seconds": 10
  }
}
```

### **ConditionalAction**

Allows to define an action that is executed based on result of some other action. This is useful for navigation between
different execution branches, for instance when using the stored cookies first run might require login credentials and
the other may not because the token is already saved in the cookie file. This action allows skipping the whole `login`
execution step, when some defined condition fails.

**Parameters**

- **test_action** - Testing action object, if the action passes the result_action will be executed.
- **result_action** - The action executed if the entry action passes.
- **fail_action** - [OPT] The action executed if the entry action fails. If not specified, excution continues on
  failure.

```json
{
  "description": "Look for modal form in case of second login and try to close it and refresh.",
  "action_name": "ConditionalAction",
  "action_parameters": {
    "test_action": {
      "action_name": "GenericElementAction",
      "action_parameters": {
        "xpath": "//div[@role='dialog' and @aria-labelledby='dls-modal__Login']//button[@type='button']",
        "method_name": "click"
      }
    },
    "result_action": {
      "action_name": "GenericDriverAction",
      "action_parameters": {
        "method_name": "refresh"
      }
    }
  }
}
```

### **BreakBlockExecution**

This action allows breaking the current `Step` execution and skipping to the next step.

```json
{
  "description": "Already logged in, skipping the login branch.",
  "action_name": "BreakBlockExecution"
}
```
### **ExitAction**

This action allows you to stop the execution any time with specified status and message

Supported levels are:
CRITICAL = 50 ERROR = 40 WARNING = 30 INFO = 20 DEBUG = 10 NOTSET = 0

**Parameters**

- **status** - Int number specifying the exit status. Anything `>=1` will result in error. `0` is success.
- **message** - Message that will be printed in the log.

```json
{
  "description": "Stop execution",
  "action_name": "ExitAction",
  "action_parameters": {
    "status": 1,
    "message": "Failed execution because user wanted to!"
  }
}
```


## User parameters

The component support specifying user parameters. These are values that can be accesses from each
`Action` instead of hardcoded parameters. This is very useful when need of hashed values (keys prefixed with `#` get
encrypted automatically in Keboola Connection.

These parameters also support use of dynamic functions.

In configuration the user parameters are defined in `user_parameters` object. For example:

```json
"user_parameters": {
"username": "myUser",
"#password": "xxx",
"report_format": "CSV",
"url": {
"function": "concat",
"args":[
"http://example.com",
"/test?date=",
{"function": "string_to_date",
"args": [
"yesterday",
"%Y-%m-%d"
]
}
]
}
}
```

The above parameters may be accessed from within `Actions` like that:

**Get URL with dynamic date**

```json
{
  "description": "Get file from url",
  "action_name": "GenericDriverAction",
  "action_parameters": {
    "positional_arguments": [
      {
        "attr": "url"
      }
    ],
    "method_name": "get"
  }
}
```

**Fill in password from hashed user value**

```json
{
  "description": "Input password.",
  "action_name": "GenericElementAction",
  "action_parameters": {
    "xpath": "//*[@id=\"password\"]",
    "positional_arguments": [
      {
        "attr": "#password"
      }
    ],
    "method_name": "send_keys"
  }
}
```

## Dynamic Functions

The application support functions that may be applied on parameters in the configuration to get dynamic values.

Currently these functions work only in the `user_parameters` scope. Place the required function object instead of the
user parameter value.

**Function object**

```json
{
  "function": "string_to_date",
  "args": [
    "yesterday",
    "%Y-%m-%d"
  ]
}
```

**Function Nesting**

Nesting of functions is supported:

```json
{
  "user_parameters": {
    "url": {
      "function": "concat",
      "args": [
        "http://example.com",
        "/test?date=",
        {
          "function": "string_to_date",
          "args": [
            "yesterday",
            "%Y-%m-%d"
          ]
        }
      ]
    }
  }
}

```

### string_to_date

Function converting string value into a datestring in specified format. The value may be either date in `YYYY-MM-DD`
format, or a relative period e.g. `5 hours ago`, `yesterday`,`3 days ago`, `4 months ago`, `2 years ago`, `today`.

The result is returned as a date string in the specified format, by default `%Y-%m-%d`

The function takes two arguments:

1. [REQ] Date string
2. [OPT] result date format. The format should be defined as in http://strftime.org/

**Example**

```json
{
  "user_parameters": {
    "yesterday_date": {
      "function": "string_to_date",
      "args": [
        "yesterday",
        "%Y-%m-%d"
      ]
    }
  }
}
```

The above value is then available in step contexts as:

```json
"to_date": {"attr": "yesterday_date"}
```

### concat

Concat an array of strings.

The function takes an array of strings to concat as an argument

**Example**

```json
{
  "user_parameters": {
    "url": {
      "function": "concat",
      "args": [
        "http://example.com",
        "/test"
      ]
    }
  }
}
```

The above value is then available in step contexts as:

```json
"url": {"attr": "url"}
```

## Sample configuration

```json
{
  "user_parameters": {},
  "driver": "Chrome",
  "start_url": "https://support.spatialkey.com/spatialkey-sample-csv-data",
  "random_wait_range": [
    1,
    10
  ],
  "store_cookies": false,
  "docker_mode": true,
  "steps": [
    {
      "description": "Test if should continue",
      "actions": [
        {
          "description": "Continue if search field exists.",
          "action_name": "ConditionalAction",
          "action_parameters": {
            "test_action": {
              "action_name": "GenericElementAction",
              "action_parameters": {
                "xpath": "//div[@id='livesearch']",
                "method_name": "click"
              }
            },
            "fail_action": {
              "action_name": "BreakBlockExecution"
            }
          }
        },
        {
          "description": "live-search found, continue in block",
          "action_name": "GenericBrowserAction",
          "action_parameters": {
            "positional_arguments": [
              2
            ],
            "method_name": "implicitly_wait"
          }
        }
      ]
    },
    {
      "description": "Choose and download report.",
      "actions": [
        {
          "description": "Click Download",
          "action_name": "GenericElementAction",
          "action_parameters": {
            "xpath": "//a[@href='http://spatialkeydocs.s3.amazonaws.com/FL_insurance_sample.csv.zip']",
            "method_name": "click"
          }
        },
        {
          "description": "Wait",
          "action_name": "GenericBrowserAction",
          "action_parameters": {
            "positional_arguments": [
              30
            ],
            "method_name": "implicitly_wait"
          }
        }
      ]
    }
  ],
  "debug": false
}
```

# Configuration creation

To configure the web crawler it is needed to know the expected DOM structure of the website crawled. For that it is
recommended to run the component locally, executing the `component.py` `run` method. This can be done either using your
favourite IDE such as PyCharm or manually from the command line by running:

```
python -u /code/src/component.py
```

from the root folder.

Please note that you should set up the `KBC_DATADIR` environment variable pointing to your configuration folder in case
you do not have the `data` folder present in the root.

For the local development it is also necessary to have Chrome browser and the
corresponding [Chrome Driver](https://chromedriver.chromium.org/downloads)  installed and set the `dokcer_mode`
configuration parameter to `false`. This way it is possible to see the actual effects of each steps defined directly in
the browser and develop the configuration step-by-step. For inspecting the DOM structure it is recommended to use some
Chrome extension that allows you to retrieve xPath of selected elements for
instance  [`xpath-finder`](https://github.com/trembacz/xpath-finder)
or using the [Chrome Dev Console](https://developers.google.com/web/tools/chrome-devtools/console/) available by
pressing `F12` or right click -> explore element.

## Development

For local testing it is useful to include `data` folder in the root and use docker-compose commands to run the container
or execute tests.

If required, change the local data folder path in the `docker-composer` file to your custom one:

```yaml
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
```

Clone this repository and init the workspace with following command:

```
git clone https://bitbucket.org:kds_consulting_team/kbc-python-template.git my-new-component
cd my-new-component
docker-compose build
docker-compose run --rm dev
```

Run the test suite and lint check using this command:

```
docker-compose run --rm test
```

# Integration

For information about deployment and integration with KBC, please refer to
the [deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)