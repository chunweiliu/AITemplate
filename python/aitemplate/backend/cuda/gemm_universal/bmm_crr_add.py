#  Copyright (c) Meta Platforms, Inc. and affiliates.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

"""
Codegen for bmm_crr_add, which computes A @ B + bias + C.
A[ColMajor], B[RowMajor], bias / C[RowMajor]
"""

from ... import registry
from ...common import gemm_common
from . import bmm_common, bmm_crr, common

# pylint: disable=C0103,C0415,W0613,C0301,R1705,R1703


@registry.reg("cuda.bmm_crr_add.config")
def bmm_crr_add_config(func_attrs, dtype="float16"):
    return bmm_crr.bmm_crr_config(func_attrs, dtype)


@registry.reg("cuda.bmm_crr_add.gen_profiler")
def gen_profiler(func_attrs, workdir, profiler_filename, dim_info_dict):
    a_dims = bmm_common.reverse_dim_info_mapping(
        dim_info_dict, gemm_common.Source.INPUT, 0
    )
    b_dims = bmm_common.reverse_dim_info_mapping(
        dim_info_dict, gemm_common.Source.INPUT, 1
    )
    c_dims = bmm_common.reverse_dim_info_mapping(
        dim_info_dict, gemm_common.Source.OUTPUT, 0
    )

    args_parser = bmm_common.ARGS_PARSER_TEMPLATE.render(
        a_dims=a_dims, b_dims=b_dims, c_dims=c_dims
    )

    default_mm_info = bmm_common.get_default_problem_info(
        bmm_crr.PROBLEM_ARGS,
        bias_ptr="d_ptr",
        alpha_value=func_attrs.get("alpha", 1),
        beta_value=1,
    )
    a_shapes = func_attrs["input_accessors"][0].original_shapes
    b_shapes = func_attrs["input_accessors"][1].original_shapes
    d_shapes = func_attrs["input_accessors"][2].original_shapes
    bmm_common._update_stride_info(default_mm_info, a_shapes, b_shapes, d_shapes)

    problem_args = bmm_common.PROBLEM_ARGS_TEMPLATE.render(
        mm_info=default_mm_info,
    )

    return bmm_common.gen_profiler(
        func_attrs,
        workdir,
        profiler_filename,
        dim_info_dict,
        common.SRC_TEMPLATE,
        problem_args,
        args_parser,
    )


@registry.reg("cuda.bmm_crr_add.gen_function")
def gen_function(
    func_attrs,
    exec_cond_template,
    dim_info_dict,
):
    default_mm_info = bmm_common.get_default_problem_info(
        bmm_crr.PROBLEM_ARGS,
        bias_ptr="d_ptr",
        alpha_value=func_attrs.get("alpha", 1),
        beta_value=1,
    )
    (
        problem_args,
        input_addr_calculator,
        output_addr_calculator,
    ) = bmm_common.make_function_strided_args(
        func_attrs, dim_info_dict, default_mm_info, is_permute=False
    )
    return bmm_common.gen_function(
        func_attrs,
        exec_cond_template,
        problem_args,
        dim_info_dict,
        input_addr_calculator=input_addr_calculator,
        output_addr_calculator=output_addr_calculator,
    )


@registry.reg("cuda.bmm_crr_add.func_decl")
def gen_function_decl(func_attrs):
    return bmm_common.gen_function_decl(func_attrs)


@registry.reg("cuda.bmm_crr_add.func_call")
def gen_function_call(func_attrs, indent="  "):
    return bmm_common.gen_function_call(func_attrs, indent)


@registry.reg("cuda.bmm_crr_add.filter")
def function_filter(cfg, func_attrs, ab_alignment):
    return common.function_filter(cfg, func_attrs, ab_alignment)
