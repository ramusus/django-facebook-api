# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 ramusus
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
from django.dispatch import Signal

#facebook_api_pre_fetch = Signal(providing_args=["instance"])#, "raw", "using", "fetch_fields"])
facebook_api_post_fetch = Signal(providing_args=["instance", "created"])#, "raw", "using", "fetch_fields"])
