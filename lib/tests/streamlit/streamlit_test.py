# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
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

"""Streamlit Unit test."""

import datetime
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from google.protobuf import json_format
from parameterized import parameterized

import streamlit as st
from streamlit import __version__
from streamlit.errors import StreamlitAPIException
from tests import testutil
from tests.delta_generator_test_case import DeltaGeneratorTestCase


def get_version():
    """Get version by parsing out setup.py."""
    dirname = os.path.dirname(__file__)
    base_dir = os.path.abspath(os.path.join(dirname, "../.."))
    pattern = re.compile(r"(?:.*VERSION = \")(?P<version>.*)(?:\"  # PEP-440$)")
    for line in open(os.path.join(base_dir, "setup.py")).readlines():
        m = pattern.match(line)
        if m:
            return m.group("version")


class StreamlitTest(unittest.TestCase):
    """Test Streamlit.__init__.py."""

    def test_streamlit_version(self):
        """Test streamlit.__version__."""
        self.assertEqual(__version__, get_version())

    def test_get_option(self):
        """Test streamlit.get_option."""
        # This is set in lib/tests/conftest.py to False
        self.assertEqual(False, st.get_option("browser.gatherUsageStats"))

    def test_public_api(self):
        """Test that we don't accidentally remove (or add) symbols
        to the public `st` API.
        """
        api = {
            k
            for k, v in st.__dict__.items()
            if not k.startswith("_") and not isinstance(v, type(st))
        }
        self.assertEqual(
            api,
            {
                # DeltaGenerator methods:
                "altair_chart",
                "area_chart",
                "audio",
                "balloons",
                "bar_chart",
                "bokeh_chart",
                "button",
                "caption",
                "camera_input",
                "checkbox",
                "code",
                "columns",
                "tabs",
                "container",
                "dataframe",
                "date_input",
                "divider",
                "download_button",
                "expander",
                "pydeck_chart",
                "empty",
                "error",
                "exception",
                "file_uploader",
                "form",
                "form_submit_button",
                "graphviz_chart",
                "header",
                "help",
                "image",
                "info",
                "json",
                "latex",
                "line_chart",
                "map",
                "markdown",
                "metric",
                "multiselect",
                "number_input",
                "plotly_chart",
                "progress",
                "pyplot",
                "radio",
                "selectbox",
                "select_slider",
                "slider",
                "snow",
                "subheader",
                "success",
                "table",
                "text",
                "text_area",
                "text_input",
                "time_input",
                "title",
                "vega_lite_chart",
                "video",
                "warning",
                "write",
                "color_picker",
                "sidebar",
                # Other modules the user should have access to:
                "echo",
                "spinner",
                "set_page_config",
                "stop",
                "cache",
                "secrets",
                "session_state",
                "cache_data",
                "cache_resource",
                # Beta APIs:
                "beta_container",
                "beta_expander",
                "beta_columns",
                # Experimental APIs:
                "experimental_user",
                "experimental_singleton",
                "experimental_memo",
                "experimental_get_query_params",
                "experimental_set_query_params",
                "experimental_rerun",
                "experimental_show",
                "experimental_data_editor",
                "get_option",
                "set_option",
            },
        )

    def test_pydoc(self):
        """Test that we can run pydoc on the streamlit package"""
        cwd = os.getcwd()
        try:
            os.chdir(tempfile.mkdtemp())
            # Run the script as a separate process to make sure that
            # the currently loaded modules do not affect the test result.
            output = subprocess.check_output(
                [sys.executable, "-m", "pydoc", "streamlit"]
            ).decode()
            self.assertIn("Help on package streamlit:", output)
        finally:
            os.chdir(cwd)


class StreamlitAPITest(DeltaGeneratorTestCase):
    """Test Public Streamlit Public APIs."""

    def test_st_legacy_line_chart(self):
        """Test st._legacy_line_chart."""
        df = pd.DataFrame([[10, 20, 30]], columns=["a", "b", "c"])
        st._legacy_line_chart(df, width=640, height=480)

        el = self.get_delta_from_queue().new_element.vega_lite_chart
        chart_spec = json.loads(el.spec)
        self.assertEqual(chart_spec["mark"], "line")
        self.assertEqual(chart_spec["width"], 640)
        self.assertEqual(chart_spec["height"], 480)

        self.assertEqual(
            el.datasets[0].data.columns.plain_index.data.strings.data,
            ["index", "variable", "value"],
        )

        data = json.loads(json_format.MessageToJson(el.datasets[0].data.data))
        result = [x["int64s"]["data"] for x in data["cols"] if "int64s" in x]

        self.assertEqual(result[1], ["10", "20", "30"])

    def test_st_arrow_line_chart(self):
        """Test st._arrow_line_chart."""
        from streamlit.type_util import bytes_to_data_frame

        df = pd.DataFrame([[10, 20, 30]], columns=["a", "b", "c"])
        EXPECTED_DATAFRAME = pd.DataFrame(
            [[0, "a", 10], [0, "b", 20], [0, "c", 30]],
            index=[0, 1, 2],
            columns=["index", "variable", "value"],
        )
        st._arrow_line_chart(df, width=640, height=480)

        proto = self.get_delta_from_queue().new_element.arrow_vega_lite_chart
        chart_spec = json.loads(proto.spec)

        self.assertEqual(chart_spec["mark"], "line")
        self.assertEqual(chart_spec["width"], 640)
        self.assertEqual(chart_spec["height"], 480)
        pd.testing.assert_frame_equal(
            bytes_to_data_frame(proto.datasets[0].data.data),
            EXPECTED_DATAFRAME,
        )

    def test_st_markdown(self):
        """Test st.markdown."""
        st.markdown("    some markdown  ")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, "some markdown")

        # test the unsafe_allow_html keyword
        st.markdown("    some markdown  ", unsafe_allow_html=True)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, "some markdown")
        self.assertTrue(el.markdown.allow_html)

        # test the help keyword
        st.markdown("    some markdown  ", help="help text")
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.body, "some markdown")
        self.assertEqual(el.markdown.help, "help text")

    def test_st_plotly_chart_simple(self):
        """Test st.plotly_chart."""
        import plotly.graph_objs as go

        trace0 = go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17])

        data = [trace0]

        st.plotly_chart(data)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.plotly_chart.HasField("url"), False)
        self.assertNotEqual(el.plotly_chart.figure.spec, "")
        self.assertNotEqual(el.plotly_chart.figure.config, "")
        self.assertEqual(el.plotly_chart.use_container_width, False)

    def test_st_plotly_chart_use_container_width_true(self):
        """Test st.plotly_chart."""
        import plotly.graph_objs as go

        trace0 = go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17])

        data = [trace0]

        st.plotly_chart(data, use_container_width=True)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.plotly_chart.HasField("url"), False)
        self.assertNotEqual(el.plotly_chart.figure.spec, "")
        self.assertNotEqual(el.plotly_chart.figure.config, "")
        self.assertEqual(el.plotly_chart.use_container_width, True)

    def test_st_plotly_chart_sharing(self):
        """Test st.plotly_chart when sending data to Plotly's service."""
        import plotly.graph_objs as go

        trace0 = go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17])

        data = [trace0]

        with patch(
            "streamlit.elements.plotly_chart." "_plot_to_url_or_load_cached_url"
        ) as plot_patch:
            plot_patch.return_value = "the_url"
            st.plotly_chart(data, sharing="public")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.plotly_chart.HasField("figure"), False)
        self.assertNotEqual(el.plotly_chart.url, "the_url")
        self.assertEqual(el.plotly_chart.use_container_width, False)

    def test_st_legacy_table(self):
        """Test st._legacy_table."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=["col1", "col2"])

        st._legacy_table(df)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.table.data.cols[0].int64s.data, [1, 3])
        self.assertEqual(el.table.data.cols[1].int64s.data, [2, 4])
        self.assertEqual(
            el.table.columns.plain_index.data.strings.data, ["col1", "col2"]
        )

    def test_st_arrow_table(self):
        """Test st._arrow_table."""
        from streamlit.type_util import bytes_to_data_frame

        df = pd.DataFrame([[1, 2], [3, 4]], columns=["col1", "col2"])

        st._arrow_table(df)

        proto = self.get_delta_from_queue().new_element.arrow_table
        pd.testing.assert_frame_equal(bytes_to_data_frame(proto.data), df)

    def test_st_text(self):
        """Test st.text."""
        st.text("some text")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.text.body, "some text")

    def test_st_text_with_help(self):
        """Test st.text with help."""
        st.text("some text", help="help text")
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.text.body, "some text")
        self.assertEqual(el.text.help, "help text")

    def test_st_caption_with_help(self):
        """Test st.caption with help."""
        st.caption("some caption", help="help text")
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.help, "help text")

    def test_st_latex_with_help(self):
        """Test st.latex with help."""
        st.latex(
            r"""
            a + ar + a r^2 + a r^3 + \cdots + a r^{n-1} =
            \sum_{k=0}^{n-1} ar^k =
            a \left(\frac{1-r^{n}}{1-r}\right)
            """,
            help="help text",
        )
        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.markdown.help, "help text")

    def test_st_time_input(self):
        """Test st.time_input."""
        value = datetime.time(8, 45)
        st.time_input("Set an alarm for", value)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.time_input.default, "08:45")
        self.assertEqual(el.time_input.step, datetime.timedelta(minutes=15).seconds)

    def test_st_time_input_with_step(self):
        """Test st.time_input with step."""
        value = datetime.time(9, 00)
        st.time_input("Set an alarm for", value, step=datetime.timedelta(minutes=5))

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.time_input.default, "09:00")
        self.assertEqual(el.time_input.step, datetime.timedelta(minutes=5).seconds)

    def test_st_time_input_exceptions(self):
        """Test st.time_input exceptions."""
        value = datetime.time(9, 00)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=True)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=(90, 0))
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=1)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=59)
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=datetime.timedelta(hours=24))
        with self.assertRaises(StreamlitAPIException):
            st.time_input("Set an alarm for", value, step=datetime.timedelta(days=1))

    def test_st_legacy_vega_lite_chart(self):
        """Test st._legacy_vega_lite_chart."""
        pass

    def test_set_query_params_sends_protobuf_message(self):
        """Test valid st.set_query_params sends protobuf message."""
        st.experimental_set_query_params(x="a")
        message = self.get_message_from_queue(0)
        self.assertEqual(message.page_info_changed.query_string, "x=a")

    def test_set_query_params_exceptions(self):
        """Test invalid st.set_query_params raises exceptions."""
        with self.assertRaises(StreamlitAPIException):
            st.experimental_set_query_params(embed="True")
        with self.assertRaises(StreamlitAPIException):
            st.experimental_set_query_params(embed_options="show_colored_line")

    def test_get_query_params_after_set_query_params(self):
        """Test valid st.set_query_params sends protobuf message."""
        p_set = dict(x=["a"])
        st.experimental_set_query_params(**p_set)
        p_get = st.experimental_get_query_params()
        self.assertEqual(p_get, p_set)
