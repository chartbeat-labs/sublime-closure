import sublime, sublime_plugin
import subprocess
import re

LINE_LENGTH_REGEX = re.compile(r'Line too long \((\d+)')

def highlight_error(self, view, warning, ignorelist, max_line_length):
  if warning:
    warning = warning.split(':')
    # Ignore the lint warning if it matches one of our ignores from prefs
    if ignorelist:
      for ignore in ignorelist:
        if ignore in warning[2]:
          return None
    # If this is a line length warning, test against preferred max line length
    if max_line_length:
      match = re.search(LINE_LENGTH_REGEX, warning[2])
      if match:
        length = int(match.group(1))
        if length <= max_line_length:
          return None

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
        ignorelist = view.settings().get("closurelint_ignore")
        max_line_length = view.settings().get("closurelint_max_line_length")

        for line in results.split('\n'):
          if line.startswith(file_name):
            region = highlight_error(self, view, line.replace(file_name, ''), ignorelist, max_line_length)
            if region:
              regions.append(region)

        view.add_regions('ClosureLintWarnings', regions, 'string', 'dot', sublime.DRAW_OUTLINED)


  def on_selection_modified(self, view):
    if is_javascript_file(view):
      warnings = view.get_regions('ClosureLintWarnings')
      for warning in warnings:
        if warning.contains(view.sel()[0]):
          display_warning(warning)
          break
