# -*- coding: utf-8 -*-

import sys
import html
import json
import time

from iparrot import __version__, __description__


# ----------------------------------------------------------------------
# Template
class ReportTemplate(object):
    """
    Define a HTML template for report generation.
    Overall structure of an HTML report
    HTML
    +------------------------+
    |<html>                  |
    |  <head>                |
    |                        |
    |   STYLESHEET           |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </head>               |
    |                        |
    |  <body>                |
    |                        |
    |   HEADING              |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   REPORT               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |   ENDING               |
    |   +----------------+   |
    |   |                |   |
    |   +----------------+   |
    |                        |
    |  </body>               |
    |</html>                 |
    +------------------------+
    """

    DEFAULT_TITLE = 'Parrot Test Report'
    DEFAULT_DESCRIPTION = __description__
    # ------------------------------------------------------------------------
    # HTML Template
    #
    HTML_TPL = r"""<!DOCTYPE html>
  <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>%(title)s</title>
    %(stylesheet)s
  </head>
  <body>
    <div class="container">
      %(heading)s
      %(report)s
      %(ending)s
    </div>
  </body>
</html>
"""
    # ------------------------------------------------------------------------
    # Stylesheet
    #
    STYLE_TPL = """
    <style>
        body {
          background-color: #f2f2f2;
          color: #333;
          margin: 0 auto;
          width: 960px;
        }
        #summary {
          width: 960px;
          margin-bottom: 20px;
        }
        #summary th {
          background-color: skyblue;
          padding: 5px 12px;
        }
        #summary td {
          background-color: lightblue;
          text-align: center;
          padding: 4px 8px;
        }
        .details {
          width: 960px;
          margin-bottom: 20px;
        }
        .details th {
          background-color: skyblue;
          padding: 5px 12px;
        }
        .details td .pass {
          background-color: lightgreen;
        }
        .details td .fail {
          background-color: lightsalmon;
        }
        .details td {
          background-color: lightblue;
          padding: 5px 12px;
        }
        .details .detail {
          background-color: lightgrey;
          font-size: smaller;
          padding: 5px 10px;
          line-height: 20px;
          text-align: left;
        }
        .details .pass {
          background-color: greenyellow;
        }
        .details .fail {
          background-color: orangered;
        }
    
        .button {
          font-size: 1em;
          padding: 6px;
          width: 4em;
          text-align: center;
          background-color: #06d85f;
          border-radius: 20px/50px;
          cursor: pointer;
          transition: all 0.3s ease-out;
        }
        a.button{
          color: gray;
          text-decoration: none;
          display: inline-block;
        }
        .button:hover {
          background: #2cffbd;
        }
    
        .overlay {
          position: fixed;
          top: 0;
          bottom: 0;
          left: 0;
          right: 0;
          background: rgba(0, 0, 0, 0.7);
          transition: opacity 500ms;
          visibility: hidden;
          opacity: 0;
          line-height: 25px;
          overflow: auto;
        }
        .overlay:target {
          visibility: visible;
          opacity: 1;
        }
    
        .popup {
          margin: 70px auto;
          padding: 20px;
          background: #fff;
          border-radius: 10px;
          width: 50%;
          position: relative;
          transition: all 3s ease-in-out;
        }
    
        .popup h2 {
          margin-top: 0;
          color: #333;
          font-family: Tahoma, Arial, sans-serif;
        }
        .popup .close {
          position: absolute;
          top: 20px;
          right: 30px;
          transition: all 200ms;
          font-size: 30px;
          font-weight: bold;
          text-decoration: none;
          color: #333;
        }
        .popup .close:hover {
          color: #06d85f;
        }
        .popup .content {
          max-height: 80%;
          overflow: auto;
          text-align: left;
        }
        .popup .separator {
          color:royalblue
        }
    
        @media screen and (max-width: 700px) {
          .box {
            width: 70%;
          }
          .popup {
            width: 70%;
          }
        }
    </style>
"""

    # ------------------------------------------------------------------------
    # Heading
    #
    HEADING_TPL = """<h1>Test Report for: %(title)s</h1>

      <h2>Summary</h2>
      <table id="summary">
        <tr>
          <th>Start Time</th>
          <td colspan="6">%(time_start)s</td>
        </tr>
        <tr>
          <th>End Time</th>
          <td colspan="6">%(time_end)s</td>
        </tr>
        <tr>
          <th>Status</th>
          <th colspan="2">TestSuites (pass/fail)</th>
          <th colspan="2">TestCases (pass/fail)</th>
          <th colspan="2">TestSteps (pass/fail)</th>
        </tr>
        <tr>
          <td>Total (Details) =></td>
          <td colspan="2">%(suite_total)s (%(suite_pass)s/%(suite_fail)s)</td>
          <td colspan="2">%(case_total)s (%(case_pass)s/%(case_fail)s)</td>
          <td colspan="2">%(step_total)s (%(step_pass)s/%(step_fail)s)</td>
        </tr>
      </table>
  
      <h2>Details</h2>
"""

    # ------------------------------------------------------------------------
    # Report
    #
    REPORT_TPL = """
      %(case_list)s
"""

    CASE_SUMMARY_TPL = r"""
      <h3>%(case_name)s</h3>
      <table id="case_%(case_id)s" class="details">
        <tr>
          <td colspan="2">Total: %(step_total)s</td>
          <td colspan="2">Pass: %(step_pass)s</td>
          <td colspan="2">Fail: %(step_fail)s</td>
        </tr>
        <tr>
          <th>Status</th>
          <th colspan="2">Name</th>
          <th>Start Time</th>
          <th>Duration</th>
          <th>Detail</th>
        </tr>
        %(case_detail)s
      </table>
    """

    CASE_DETAIL_TPL = r"""
        <tr id="step_%(step_id)s">
          <th class="%(step_status)s" style="width:5em;">%(step_status)s</th>
          <td colspan="2">%(step_name)s</td>
          <td style="text-align:center">%(step_time_start)s</td>
          <td style="text-align:center;width:6em;">%(step_time_spent)s ms</td>
          <td class="detail">
            <a class="button" href="#popup_%(step_id)s">detail</a>
    
            <div id="popup_%(step_id)s" class="overlay">
              <div class="popup">
                <h2>TestStep Detail Info</h2>
                <a class="close" href="#step_%(step_id)s">&times;</a>
    
                <div class="content">
                  <h3>Name: %(step_name)s</h3>
    
                  %(step_detail_request)s
                  
                  %(step_detail_response)s
                  
                  %(step_detail_validation)s
                </div>
              </div>
            </div>
          </td>
        </tr>
    """

    STEP_DETAIL_REQUEST_TPL = r"""
            <h3>Request:</h3>
              <div style="overflow: auto">
                <table>
                  <tr>
                    <th>Method</th>
                    <td>%(method)s</td>
                  </tr>
                  <tr>
                    <th>URL</th>
                    <td>%(url)s</td>
                  </tr>
                  <tr>
                    <th>QueryString</th>
                    <td>%(params)s</td>
                  </tr>
                  <tr>
                    <th>PostData</th>
                    <td>%(data)s</td>
                  </tr>
                  <tr>
                    <th>Headers</th>
                    <td>%(headers)s</td>
                  </tr>
                  <tr>
                    <th>Cookies</th>
                    <td>%(cookies)s</td>
                  </tr>
                </table>
              </div>
    """

    STEP_DETAIL_RESPONSE_TPL = r"""
            <h3>Response:</h3>
              <div style="overflow: auto">
                <table>
                  <tr>
                    <th>Status</th>
                    <td>%(status)s</td>
                  </tr>
                  <tr>
                    <th>Duration</th>
                    <td>%(duration)s ms</td>
                  </tr>
                  <tr>
                    <th>Content</th>
                    <td>%(content)s</td>
                  </tr>
                  <tr>
                    <th>Headers</th>
                    <td>%(headers)s</td>
                  </tr>
                  <tr>
                    <th>Cookies</th>
                    <td>%(cookies)s</td>
                  </tr>
                </table>
              </div>
    """

    STEP_DETAIL_VALIDATION_TPL = r"""
            <h3>Validation:</h3>
              <div style="overflow: auto">
                <table>
                  <tr>
                    <th>check</th>
                    <th>comparator</th>
                    <th>expect value</th>
                    <th>actual value</th>
                  </tr>
                  %(validation_list)s
                </table>
              </div>
    """
    STEP_DETAIL_VALIDATION_ONE_TPL = r"""
                  <tr>
                    <td class="%(status)s">%(check)s</td>
                    <td>%(comparator)s</td>
                    <td>%(expect)s</td>
                    <td>%(actual)s</td>
                  </tr>
    """

    # ------------------------------------------------------------------------
    # ENDING
    #
    ENDING_TPL = """<div></div>"""
# -------------------- The end of the Template class -------------------


class Report(ReportTemplate):
    """
    """
    def __init__(self, stream=sys.stdout):
        self.stream = stream
        self.title = self.DEFAULT_TITLE
        self.description = self.DEFAULT_DESCRIPTION
        self.start_time = self.end_time = 0

    def generate_report(self, result):
        if 'title' in result:
            self.title = result['title']
        if 'time' in result and result['time']:
            if 'start' in result['time']:
                self.start_time = result['time']['start']
            if 'end' in result['time']:
                self.end_time = result['time']['end']

        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(result['summary'])
        report = self._generate_report(result['detail'])
        ending = self._generate_ending()
        output = self.HTML_TPL % dict(
            title=self.DEFAULT_TITLE,
            stylesheet=stylesheet,
            heading=heading,
            report=report,
            ending=ending,
        )
        self.stream.write(output)

    def _generate_stylesheet(self):
        return self.STYLE_TPL

    def _generate_heading(self, summary):
        return self.HEADING_TPL % dict(
            title=html.escape(self.title, quote=True),
            time_start=self.start_time,
            time_end=self.end_time,
            suite_total=summary['suite']['total'],
            suite_pass=summary['suite']['pass'],
            suite_fail=summary['suite']['fail'],
            case_total=summary['case']['total'],
            case_pass=summary['case']['pass'],
            case_fail=summary['case']['fail'],
            step_total=summary['step']['total'],
            step_pass=summary['step']['pass'],
            step_fail=summary['step']['fail']
        )

    def _generate_report(self, record):
        _detail = ''
        for _suite in record:
            s_name = _suite['_report_']['name']
            _suite_detail = ''
            for _case in _suite['test_cases']:
                c_id = _case['_report_']['id']
                c_name = _case['_report_']['name']
                t_total = _case['_report_']['steps']['total']
                t_pass = _case['_report_']['steps']['pass']
                t_fail = _case['_report_']['steps']['fail']
                _case_detail = ''
                for _step in _case['test_steps']:
                    if '_report_' not in _step:  # caused by fail-stop
                        continue
                    t_id = _step['_report_']['id']
                    t_name = _step['_report_']['name']
                    t_status = 'pass' if _step['_report_']['status'] else 'fail'
                    t_request = _step['_report_']['request']
                    t_response = _step['_report_']['response']
                    t_validation = _step['_report_']['validation']

                    _request = self.STEP_DETAIL_REQUEST_TPL % dict(
                        method=t_request['method'],
                        url=t_request['url'],
                        params=t_request['params'],
                        data=t_request['data'],
                        headers=t_request['headers'],
                        cookies=t_request['cookies']
                    )
                    _response = self.STEP_DETAIL_RESPONSE_TPL % dict(
                        status=t_response['status.code'],
                        duration=_step['_report_']['time']['spent'],
                        content=t_response['content'],
                        headers=t_response['headers'],
                        cookies=t_response['cookies']
                    )
                    _validation = ''
                    for _validate in t_validation['detail']:
                        _one = self.STEP_DETAIL_VALIDATION_ONE_TPL % dict(
                            status='pass' if _validate['status'] else 'fail',
                            check=_validate['check'],
                            comparator=_validate['comparator'],
                            expect=_validate['expect'],
                            actual=_validate['actual']
                        )
                        _validation += "{}\n".format(_one)
                    _validation = self.STEP_DETAIL_VALIDATION_TPL % dict(
                        validation_list=_validation
                    )
                    _case_detail += self.CASE_DETAIL_TPL % dict(
                        step_id=t_id,
                        step_name=t_name,
                        step_status=t_status,
                        step_time_start="{}, {}".format(
                            time.strftime("%Y-%m-%d %H:%M:%S",
                                          time.localtime(int(str(_step['_report_']['time']['start'])[:-3]))),
                            str(_step['_report_']['time']['start'])[-3:]),
                        step_time_spent=_step['_report_']['time']['spent'],
                        step_detail_request=_request,
                        step_detail_response=_response,
                        step_detail_validation=_validation.replace("__break_line__", "\n")
                    ) + "\n"
                _case_summary = self.CASE_SUMMARY_TPL % dict(
                    case_id=c_id,
                    case_name="{} - {}".format(s_name, c_name) if s_name else c_name,
                    step_total=t_total,
                    step_pass=t_pass,
                    step_fail=t_fail,
                    case_detail=_case_detail
                )

                _suite_detail += "{}\n".format(_case_summary)

            _detail += "{}\n".format(_suite_detail)

        report = self.REPORT_TPL % dict(
            case_list=_detail
        )
        return report

    def _generate_ending(self):
        return self.ENDING_TPL


if __name__ == "__main__":
    pass
