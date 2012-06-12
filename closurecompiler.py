import sublime, sublime_plugin
import subprocess
import re
import functools
import thread
import os

def highlight_error(self, view, warning):
  if warning:
    warning = warning.split(':')
    line_number = int(warning[1]) - 1
    point = view.text_point(line_number, 0)
    line = view.line(point)

    ClosureCompilerListener.warning_messages.append({
      'region': line,
      'message': ':'.join(warning[2:])
    })

    return line


def display_warning(warning):
  for region in ClosureCompilerListener.warning_messages:
    if region['region'] == warning:
      sublime.status_message(region['message'])
      break


def is_javascript_file(view):
  return bool(re.search('JavaScript', view.settings().get('syntax'), re.I))


class ClosureCompilerListener(sublime_plugin.EventListener):
  warning_messages = []
  closurebuilder_script = '/Users/jmoy/chartbeat/frontend/js/closure-library-read-only/closure/bin/build/closurebuilder.py'
  compiler_jar = '/usr/bin/compiler.jar'
  compiler_flags = ['--compilation_level=ADVANCED_OPTIMIZATIONS',
                    '--warning_level=VERBOSE',
                    '--jscomp_warning=visibility',
                    '--jscomp_warning=checkTypes',
                    '--jscomp_warning=accessControls']
  roots = ['/Users/jmoy/chartbeat/frontend/js']


  def on_post_save(self, view):
    self.warning_messages = []
    view.erase_regions('ClosureCompilerWarnings')
    if is_javascript_file(view):
      self.view = view
      self.doCompileAndHighlight()


  def doCompileAndHighlight(self):
    self.file_name = self.view.file_name().replace(' ', '\ ')

    command = ['python', 
               self.closurebuilder_script,
               '--output_mode=compiled',
               '--compiler_jar=' + self.compiler_jar,
               '--input=' + self.file_name]

    for root in self.roots:
      command.append('--root=' + root)

    for flag in self.compiler_flags:
      command.append('--compiler_flags=' + flag)

    self.raw_error = ''
    self.process = subprocess.Popen(command, 
                                    stdout=subprocess.PIPE,
                                    stderr = subprocess.PIPE)

    if self.process.stdout:
      thread.start_new_thread(self.read_stdout, ())

    if self.process.stderr:
      thread.start_new_thread(self.read_stderr, ())

  def read_stdout(self):
    while True:
      data = os.read(self.process.stdout.fileno(), 2**15)

      if data != "":
        pass
      else:
        self.process.stdout.close()
        sublime.set_timeout(self.process_finished, 0)
        break

  def read_stderr(self):
    while True:
      data = os.read(self.process.stderr.fileno(), 2**15)

      if data != "":
        self.raw_error += data
      else:
        self.process.stderr.close()
        break

  def process_finished(self):
    if self.raw_error != '':
      regions = []
      for line in self.raw_error.split('\n'):
        if line.startswith(self.file_name):
          region = highlight_error(self, self.view, line.replace(self.file_name, ''))
          if region:
            regions.append(region)

      self.view.add_regions('ClosureCompilerWarnings', 
                            regions, 
                            'string', 
                            'dot')


  def on_selection_modified(self, view):
    if is_javascript_file(view):
      warnings = view.get_regions('ClosureCompilerWarnings')
      for warning in warnings:
        if warning.contains(view.sel()[0]):
          display_warning(warning)
          break
