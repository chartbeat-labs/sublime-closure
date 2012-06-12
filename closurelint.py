import sublime, sublime_plugin
import subprocess
import re

def highlight_error(self, view, warning):
  if warning:
    warning = warning.split(':')
    line_number = int(warning[1]) - 1
    point = view.text_point(line_number, 0)
    line = view.line(point)

    ClosureLintListener.warning_messages.append({
      'region': line,
      'message': warning[2]
    })

    return line


def display_warning(warning):
  for region in ClosureLintListener.warning_messages:
    if region['region'] == warning:
      sublime.status_message(region['message'])
      break


def is_javascript_file(view):
  return bool(re.search('JavaScript', view.settings().get('syntax'), re.I))


class ClosureLintListener(sublime_plugin.EventListener):
  warning_messages = []

  def on_post_save(self, view):
    if is_javascript_file(view):
      view.erase_regions('ClosureLintWarnings')
      self.warning_messages = []

      file_name = view.file_name().replace(' ', '\ ')
      process = subprocess.Popen(['/usr/local/bin/gjslint', '--unix_mode', file_name], stdout = subprocess.PIPE)
      results, error = process.communicate()

      if results:
        regions = []
        for line in results.split('\n'):
          if line.startswith(file_name):
            region = highlight_error(self, view, line.replace(file_name, ''))
            if region:
              regions.append(region)

        view.add_regions('ClosureLintWarnings', regions, 'string', 'dot')


  def on_selection_modified(self, view):
    if is_javascript_file(view):
      warnings = view.get_regions('ClosureLintWarnings')
      for warning in warnings:
        if warning.contains(view.sel()[0]):
          display_warning(warning)
          break
