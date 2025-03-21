# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
run this script from within IDA to test the IDA feature extractor.
you must have loaded a file referenced by a test case in order
for this to do anything meaningful. for example, mimikatz.exe from testfiles.

you can invoke from the command line like this:

    & 'C:\\Program Files\\IDA Pro 8.2\\idat.exe' \
        -S"C:\\Exclusions\\code\\capa\\tests\\test_ida_features.py --CAPA_AUTOEXIT=true" \
        -A \
        -Lidalog \
        'C:\\Exclusions\\code\\capa\\tests\\data\\mimikatz.exe_'

if you invoke from the command line, and provide the script argument `--CAPA_AUTOEXIT=true`,
then the script will exit IDA after running the tests.

the output (in idalog) will look like this:

```
Loading processor module C:\\Program Files\\IDA Pro 8.2\\procs\\pc.dll for metapc...Initializing processor module metapc...OK
Loading type libraries...
Autoanalysis subsystem has been initialized.
Database for file 'mimikatz.exe_' has been loaded.
--------------------------------------------------------------------------------
PASS: test_ida_feature_counts/mimikatz-function=0x40E5C2-basic block-7
PASS: test_ida_feature_counts/mimikatz-function=0x4702FD-characteristic(calls from)-0
SKIP: test_ida_features/294b8d...-function=0x404970,bb=0x404970,insn=0x40499F-string(\r\n\x00:ht)-False
SKIP: test_ida_features/64d9f-function=0x10001510,bb=0x100015B0-offset(0x4000)-True
...
SKIP: test_ida_features/pma16-01-function=0x404356,bb=0x4043B9-arch(i386)-True
PASS: test_ida_features/mimikatz-file-import(cabinet.FCIAddFile)-True
DONE
C:\\Exclusions\\code\\capa\\tests\\test_ida_features.py: Traceback (most recent call last):
  File "C:\\Program Files\\IDA Pro 8.2\\python\\3\\ida_idaapi.py", line 588, in IDAPython_ExecScript
    exec(code, g)
  File "C:/Exclusions/code/capa/tests/test_ida_features.py", line 120, in <module>
    sys.exit(0)
SystemExit: 0
 -> OK
Flushing buffers, please wait...ok
```

Look for lines that start with "FAIL" to identify test failures.
"""

import sys
import logging
import binascii
import traceback
from pathlib import Path

import pytest

try:
    sys.path.append(str(Path(__file__).parent))
    import fixtures
finally:
    sys.path.pop()

logger = logging.getLogger("test_ida_features")

def check_input_file(wanted):
    import idautils

    try:
        found = idautils.GetInputFileMD5()[:31].decode("ascii").lower()
    except UnicodeDecodeError:
        found = binascii.hexlify(idautils.GetInputFileMD5()[:15]).decode("ascii").lower()

    if not wanted.startswith(found):
        raise RuntimeError(f"Please run the tests against sample with MD5: `{wanted}`")

def get_ida_extractor(_path):
    import capa.features.extractors.ida.extractor

    return capa.features.extractors.ida.extractor.IdaFeatureExtractor()

@pytest.mark.parametrize(
    "sample, scope, feature, expected",
    fixtures.FEATURE_PRESENCE_TESTS + fixtures.FEATURE_PRESENCE_TESTS_IDA,
)
def test_ida_features(sample, scope, feature, expected):
    try:
        check_input_file(fixtures.get_sample_md5_by_name(sample))
    except RuntimeError:
        pytest.skip("Sample MD5 mismatch. Skipping test.")

    scope = fixtures.resolve_scope(scope)
    sample = fixtures.resolve_sample(sample)

    try:
        fixtures.do_test_feature_presence(get_ida_extractor, sample, scope, feature, expected)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}\n{traceback.format_exc()}")

@pytest.mark.parametrize(
    "sample, scope, feature, expected",
    fixtures.FEATURE_COUNT_TESTS,
)
def test_ida_feature_counts(sample, scope, feature, expected):
    try:
        check_input_file(fixtures.get_sample_md5_by_name(sample))
    except RuntimeError:
        pytest.skip("Sample MD5 mismatch. Skipping test.")

    scope = fixtures.resolve_scope(scope)
    sample = fixtures.resolve_sample(sample)

    try:
        fixtures.do_test_feature_count(get_ida_extractor, sample, scope, feature, expected)
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    import idc
    import ida_auto

    ida_auto.auto_wait()
    print("-" * 80)

    pytest.main([__file__])

    print("DONE")

    if "--CAPA_AUTOEXIT=true" in idc.ARGV:
        sys.exit(0)
