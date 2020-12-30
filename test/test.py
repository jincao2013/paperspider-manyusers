# Copyright Jin Cao
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
#
# The paperspider-manyusers code is hosted on GitHub:
#
# https://github.com/jincao2013/paperspider-manyusers

import json
import os

if __name__ == "__main__":
    wdir = r'../'
    os.chdir(wdir)

    with open(r'config.json', 'r') as f:
        data = json.load(f)
