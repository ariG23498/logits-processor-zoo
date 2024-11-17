#
# SPDX-FileCopyrightText: Copyright (c) 1993-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from transformers import PreTrainedTokenizer
from typing import List
import torch


class ForceLastPhraseLogitsProcessor:
    """
    A logits processor which forces LLMs to use the given phrase before they finalize their answers.
    Most common use cases can be providing references, thanking user with context etc.

    Parameters
    ----------
    phrase (str): The phrase to be generated by LLM before the end of its speech.
    tokenizer (PreTrainedTokenizer): The tokenizer used by the LLM.
    """
    def __init__(self, phrase: str, tokenizer: PreTrainedTokenizer):
        self.eos_token_id = tokenizer.eos_token_id
        self.phrase_tokens = tokenizer.encode(phrase, add_special_tokens=False)
        self.index = 0

    def __call__(self, prompt_tokens_ids: List[int], past_token_ids: List[int], scores: torch.Tensor) -> torch.Tensor:
        if scores.argmax() == self.eos_token_id and self.index == 0:
            scores[self.phrase_tokens[self.index]] = scores.max() + 1
            self.index += 1
        elif len(self.phrase_tokens) > self.index > 0:
            scores[self.phrase_tokens[self.index]] = scores.max() + 1
            self.index += 1

        return scores
