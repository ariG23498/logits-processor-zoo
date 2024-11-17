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

from typing import List, Optional
from transformers import PreTrainedTokenizer
import torch


class ForceLastPhraseLogitsProcessor:
    """
    A logits processor which forces LLMs to use the given phrase before they finalize their answers.
    Most common use cases can be providing references, thanking user with context etc.
    WARNING: Create a new object before every model.generate call to reset iterators.

    Parameters
    ----------
    phrase (str): The phrase to be generated by LLM before the end of its speech.
    tokenizer (PreTrainedTokenizer): The tokenizer used by the LLM.
    batch_size (int): Number of prompts in the batch.
    """
    def __init__(self, phrase: str, tokenizer: PreTrainedTokenizer, batch_size: int):
        self.eos_token_id = tokenizer.eos_token_id
        self.phrase_tokens = tokenizer.encode(phrase, add_special_tokens=False)
        self.iterators = torch.zeros(batch_size, dtype=torch.int32)

    def __call__(self, req_ids_batch: List[int], logits_batch: List[torch.Tensor],
                 ids_batch: List[List[List[int]]], stream_ptr,
                 client_ids_batch: List[Optional[int]]):

        with torch.cuda.stream(torch.cuda.ExternalStream(stream_ptr)):
            for i in range(logits_batch.shape[1]):
                it = self.iterators[i].item()
                if logits_batch[:, i, :].argmax() == self.eos_token_id and it == 0:
                    logits_batch[:, i, self.phrase_tokens[it]] = logits_batch[:, i].max() + 1
                    self.iterators[i] += 1
                elif len(self.phrase_tokens) > it > 0:
                    logits_batch[:, i, self.phrase_tokens[it]] = logits_batch[:, i].max() + 1
                    self.iterators[i] += 1