#!/usr/bin/env python

import argparse
import collections
import json
import re
import types

from absl import app
from absl import flags
from absl import logging
import requests
import yaml

FLAGS = flags.FLAGS

flags.DEFINE_string('student_notebook', None,
    'The path to the student notebook file to use as a template for submission upload.')
flags.DEFINE_string('master_notebook', None,
    'The path to the master notebook file to extract submissions from.')
flags.DEFINE_string('upload_url', 'http://localhost:8000/upload.txt',
    'The URL of the upload server.')
flags.DEFINE_bool('solution_only', False,
    'If true, only checks canonical solutions (%%solution) and skips the other snippets'
    ' (%%submission).')


def LoadNotebook(filename):
  """Read a IPython notebook (.ipynb).

  Reads the file and parses it as JSON.

  Args:
    filename: The path to the .ipynb file.

  Returns:
    A parsed JSON object (dictionary).
  """
  with open(filename) as f:
    return json.load(f)


def CellStartsWith(regex, cell):
  """Checks if the first line of the cell matches the regexp with re.match.

  Args:
    regex (str): A regexp string.
    cell (dict): A JSON object representing a cell in the IPython notebook

  Returns:
    None if the regexp does not match.
    The match object if the first line of the cell source matches regex with re.match().
  """
  if len(cell['source']) == 0:
    return False
  return re.match(regex, cell['source'][0])


# A regexp that detects and extracts assignment metadata.
ASSIGNMENT_METADATA_REGEX = re.compile(r"^```[ \t\n]*# ASSIGNMENT METADATA[^\n]*([^`]*)```", re.MULTILINE)
# A regexp that detects and extracts exercise metadata.
EXERCISE_METADATA_REGEX = re.compile(r"^```[ \t\n]*# EXERCISE METADATA[^\n]*([^`]*)```", re.MULTILINE)

def ExtractSubmissionSnippets(notebook):
  """Iterates and yields %%solution and %%submission snippets from a master notebook.

  A submission snippet is a cell that starts with either %%solution
  or %%submission magic.

  Args:
    notebook: A parsed IPython notebook as a JSON dictionary.

  Yields:
    a cell with the %%solution, or %%submission that is followed by a code cell.
    The type of the magic (either "solution" or "submission") is stored into ['magic_type'].
    If the target cell had %%submission magic, the next cell stored into ['next_cell'].
    If an `# EXERCISE METADATA` block has been detected, it is copied into the metadata
    of the target cell.
  """
  target_cell = None
  assignment_metadata = {}
  exercise_metadata = {}
  for cell in notebook['cells']:
    # Detect the metadata in markdown cell.s
    if cell['cell_type'] == 'markdown':
      source = "\n".join(cell['source'])
      m = re.search(EXERCISE_METADATA_REGEX, source)
      if m:
        exercise_metadata = yaml.load(m.group(1), Loader=yaml.SafeLoader)
      m = re.search(ASSIGNMENT_METADATA_REGEX, source)
      if m:
        assignment_metadata = yaml.load(m.group(1), Loader=yaml.SafeLoader)
    # If handling a code cell immediately after the target cell, report it.
    if target_cell is not None and cell['cell_type'] == 'code':
      target_cell['next_cell'] = cell
      yield target_cell
      target_cell = None
      continue
    # Detect the target cell.
    m = CellStartsWith('%%(submission|solution)', cell)
    if cell['cell_type'] == 'code' and m:
      magic_type = m.group(1)
      # Create a shallow copy.
      target_cell = cell.copy()
      # Populate exercise and assignment metadata.
      if 'metadata' not in target_cell:
        target_cell['metadata'] = {}
      for k, v in exercise_metadata.items():
        target_cell['metadata'][k] = v
      # Note: We assume that assignment metadata and exercise metadata have disjoint keys.
      for k, v in assignment_metadata.items():
        target_cell['metadata'][k] = v
      target_cell['magic_type'] = magic_type
      if magic_type == 'solution':
        # Yield immediately
        yield target_cell
        target_cell = None
      # Otherwise delay until the next code cell, which is supposed to contain
      # an %autotest magic.
    else:
      target_cell = None


def DummyReport(test, **kwargs):
  """A dummy report function that accepts any arguments."""
  pass


def main(argv):
  st = LoadNotebook(FLAGS.student_notebook)
  ma = LoadNotebook(FLAGS.master_notebook)
  for snippet in ExtractSubmissionSnippets(ma):
    metadata = snippet.get('metadata')
    if metadata is None or metadata.get('exercise_id') is None:
      continue
    exercise_id = metadata['exercise_id']
    submission_source = "".join(snippet['source'])
    logging.vlog(1, f"=== Submission source ===\n{submission_source}\n")
    # Make a semi-shallow copy of student notebook
    submission = st.copy()
    submission['cells'] = [cell for cell in submission['cells']]
    for cell_index, cell in enumerate(submission['cells']):
      if cell.get('metadata') and cell['metadata'].get('exercise_id') == exercise_id:
        submission_cell = cell.copy()
        # Drop the first line with %%submission or %%solution magic.
        submission_cell['source'] = snippet['source'][1:]
        submission['cells'][cell_index] = submission_cell

    submission_data = json.dumps(submission)
    logging.vlog(3, f'==== Submission notebook ====\n{submission_data}\n')
    response = requests.post(FLAGS.upload_url,
        files={'notebook': submission_data},
        data={'exercise_id': exercise_id})
    logging.vlog(3, f'==== Autograder response ====\n{response.text}\n')
    try:
      result = json.loads(response.text)
    except Exception as e:
      logging.info("Exercise %s failed", exercise_id)
      raise e
    assignment_id = snippet['metadata'].get('assignment_id')
    if assignment_id is None:
      logging.error('Snippet does not have an assignment ID!')
      continue
    exercise_result = result.get(exercise_id)
    if exercise_result is None:
      logging.error(f'Result does not have result for exercise {exercise_id}, '
                    f'but has {result.keys()}')
      continue
    # Assume that the next code snippet starts with 'result, logs = %autotest ...'
    if snippet['magic_type'] == 'solution':
      # %%solution should always pass.
      for autotest_name, autotest_result in exercise_result['results'].items():
        if not autotest_result.get('passed'):
          logging.error(f'FAIL: Autotest {autotest_name} failed. Logs:\n{exercise_result["logs"]}')
        else:
          logging.info(f"Autotest {autotest_name} for {exercise_id} passed for canonical solution.")
    elif snippet['magic_type'] == 'submission' and not FLAGS.solution_only:
      if 'next_cell' not in snippet:
        logging.error(f'INTERNAL ERROR: %%submission snippet does not have next_cell')
        continue
      check_source = snippet['next_cell'].get('source')
      if not check_source or len(check_source) < 2:
        logging.error(f'Invalid check snippet: {snippet["next_cell"]}')
        continue
      autotest_lines = [(l, line) for l, line in enumerate(check_source) if re.search(r'%autotest', line)]
      if len(autotest_lines) != 1:
        logging.error(f'Found none or too many %autotest lines:\n{check_source}')
        continue
      autotest_line_index, autotest_line = autotest_lines[0]
      m = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*),[ \t]*([a-zA-Z_][a-zA-Z0-9_]*)[ \t]*=[ \t]*%autotest[ \t]*([a-zA-Z_0-9]*)', autotest_line)
      if not m:
        logging.error(f'Check snippet has invalid %autotest line: {autotest_line}\n')
        continue
      result_var_name = m.group(1)
      logs_var_name = m.group(2)
      autotest_name = m.group(3)
      if 'results' not in exercise_result or autotest_name not in exercise_result['results']:
        logging.error(f'Did not find autotest {autotest_name} in results:\n{exercise_result}')
        continue
      if 'logs' not in exercise_result or autotest_name not in exercise_result['logs']:
        logging.error(f'Did not find autotest {autotest_name} in logs:\n{exercise_result}')
        continue
      check_env = {
          result_var_name: types.SimpleNamespace(results=exercise_result['results'][autotest_name]),
          logs_var_name: exercise_result['logs'][autotest_name],
          autotest_name: None,
          'submission_source': types.SimpleNamespace(source=submission_source),
          'report': DummyReport,
      }
      check_snippet = "\n".join(check_source[:autotest_line_index] + check_source[autotest_line_index+1:])
      logging.vlog(3, f'===== Autotest check snippet =====\n{check_snippet}\n===== Check env =====\n{check_env}')
      try:
        exec(check_snippet, check_env)
        logging.info(f"Autotest snippet for {autotest_name} passed for non-canonical submission.")
      except Exception as e:
        logging.error(f'Error in eval check snippet: {e}')
        raise e
      print(f'Autotest {autotest_name} passed.')


if __name__ == '__main__':
  app.run(main)
  args = parser.parse_args()
  main(args)
