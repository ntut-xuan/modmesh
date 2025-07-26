# Copyright (c) 2025, Han-Xuan Huang <c1ydehhx@gmail.com>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# - Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# - Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# - Neither the name of the copyright holder nor the names of its contributors
#   may be used to endorse or promote products derived from this software
#   without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from typing import Any, Callable
from dataclasses import dataclass


@dataclass
class ProfilingsFunctionResult:
    name: str
    total_time: float
    count: float
    children: list


@dataclass
class ProfilingColumnData:
    column_name: str
    column_data: list[float | str]


class ProfilingTableBuilder:
    """
    The table builder for `ProfilingResultPrinter`.

    It accept the list of `ProfilingColumnData` as attribute.
    The column width is 30 in default,
    the user can adjust it by modified `column_width`.

    The `ProfilingColumnData` list will be convert as row datas
    and used to generate rows by `generate_result_row_by_row`.

    Attributes:
        column_datas (list[ProfilingColumnData]):
            The column data represent list of `ProfilingColumnData`.
        column_width (int):
            The column width.
    """
    def __init__(
        self,
        column_datas: list[ProfilingColumnData] = [],
        column_width: int = 30,
    ):
        self.column_datas = column_datas
        self.column_width = column_width

        self.row_datas = []

        row_count = len(self.column_datas[0].column_data)
        for i in range(row_count):
            row_data = []

            for j in range(len(self.column_datas)):
                row_data.append(self.column_datas[j].column_data[i])

            self.row_datas.append(row_data)

    def generate_header(self):
        """
        Generate the header with the width specific from user.

        It will be the format like:
        `| func     | column A | column B | ... |`
        """
        return (
            "| "
            + " | ".join(
                [
                    data.column_name.ljust(self.column_width)
                    for data in self.column_datas
                ]
            )
            + " |\n"
        )

    def generate_horizontal_lines(self):
        """
        Generate the horizontal lines with the width specific from user.

        It will be the format like:
        `| -------- | -------- | -------- | ... |`
        """
        return (
            "| "
            + " | ".join(
                ["".ljust(self.column_width, "-") for _ in self.column_datas]
            )
            + " |\n"
        )

    def generate_result_row_by_row(self):
        """
        Generate the result row with the width specific from user.

        It will be the format like:
        `| func A   | 30       | 40       | ... |`
        """
        result = ""

        if len(self.column_datas) == 0:
            return result

        for row_datas in self.row_datas:
            result += (
                "| "
                + " | ".join(
                    [str(data).ljust(self.column_width) for data in row_datas]
                )
                + " |\n"
            )

        return result

    def generate_table_str(self):
        """
        Generate the table that combines header, horizontal lines and rows.

        It will be the format like:
        ```
        | func     | column A | column B | ... |
        | -------- | -------- | -------- | ... |
        | func A   | 30       | 40       | ... |
        ```
        """
        return (
            self.generate_header()
            + self.generate_horizontal_lines()
            + self.generate_result_row_by_row()
        )


class ProfilingResultPrinter:
    """
    A printer that formats and displays profiling results in a table.

    The profiling result should be a list of dictionaries.

    Each dictionary must contain at least the following keys:
        - "name": Name of the function (str)
        - "total_time": Total execution time in seconds (float)
        - "count": Number of times the function was called (int)
        - "children": A list of child profiling results (list)

    Example:
    ```
        [
            {
                "name": "numpy_arange_100",
                "total_time": 0.002083,
                "count": 1,
                "children": []
            },
            {
                "name": "numpy_arange_1000",
                "total_time": 0.004096,
                "count": 1,
                "children": []
            }
        ]
    ```

    Attributes:
        profiling_results (list[dict[str, Any]]):
            The list of profiling data dictionaries,
            typically generated by a profiler.
    """

    def __init__(self, profiling_results: list[dict[str, Any]] = []):

        if profiling_results is None:
            raise ValueError("Profiling results cannot be None.")

        self.profiling_results: list[ProfilingsFunctionResult] = [
            ProfilingsFunctionResult(**result) for result in profiling_results
        ]
        self.column_datas: list[ProfilingColumnData] = []

        self.column_datas.append(
            ProfilingColumnData(
                "func",
                [
                    profiling_result.name
                    for profiling_result in self.profiling_results
                ],
            )
        )

    def __getitem__(self, function_name: str) -> ProfilingsFunctionResult:
        """
        Get the result object based on function name.

        Attributes:
            function_name (str):
                The specific function name.
                If function name is absent in profiling result,
                it will raise ValueError.

        Returns:
            ProfilingsFunctionResult: The result.
        """
        result = list(
            filter(lambda x: x.name == function_name, self.profiling_results)
        )

        if len(result) == 0:
            raise ValueError(
                "The result with specific function name is absent."
            )

        return list(result)[0]

    def add_column(
        self,
        column_name: str,
        callable: Callable[[ProfilingsFunctionResult], str | float],
    ):
        """
        Add a new column to the output table, computed using a lambda function.

        The provided function should accept a single
        `ProfilingsFunctionResult` object and return either a string or a float
        to be displayed in the column.

        Example:
            To add a column showing total time, use:
                `add_column("Total Time", lambda r: r.total_time)`

        Attributes:
            column_name (str):
                The name of the column to be added.
            callable (Callable[[ProfilingsFunctionResult], str | float]):
                A lambda or function that calculate value for column.
        """
        self.column_datas.append(
            ProfilingColumnData(
                column_name,
                [
                    callable(profiling_result)
                    for profiling_result in self.profiling_results
                ],
            )
        )

    def print_result(self, column_width=30):
        """
        Print the table.

        Attributes:
            column_width (int):
                The width of column.
        """
        builder = ProfilingTableBuilder(self.column_datas, column_width)
        print(builder.generate_table_str())


# vim: set ff=unix fenc=utf8 et sw=4 ts=4 sts=4:
