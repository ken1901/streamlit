/**
 * Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from "react"
import { mockTheme } from "@streamlit/lib/src/mocks/mockTheme"
import FullScreenWrapper, { FullScreenWrapperProps } from "./FullScreenWrapper"
import { customRenderLibContext } from "@streamlit/lib/src/test_util"
import { LibContextProps } from "src/components/core/LibContext"

describe("FullScreenWrapper", () => {
  const getProps = (
    props: Partial<FullScreenWrapperProps> = {}
  ): FullScreenWrapperProps => ({
    children: jest.fn(),
    width: 100,
    height: 100,
    theme: mockTheme.emotion,
    ...props,
  })

  it("cannot find StyledFullScreenButton when hideFullScreenWidget is true", () => {
    const props = getProps()
    const providerProps = {
      hideFullScreenButtons: true,
    } as Partial<LibContextProps>

    const { queryByTestId } = customRenderLibContext(
      <FullScreenWrapper {...props} />,
      providerProps
    )
    expect(queryByTestId("StyledFullScreenButton")).toBeNull()
  })

  it("can find StyledFullScreenButton with default LibContext", () => {
    const props = getProps()

    const { queryByTestId } = customRenderLibContext(
      <FullScreenWrapper {...props} />,
      {}
    )
    expect(queryByTestId("StyledFullScreenButton")).not.toBeNull()
  })
})
