from torch import nn
from transformers import AutoModel, AutoTokenizer, AutoConfig
import json
from typing import List, Dict
import os
import numpy as np
import logging

class Auto(nn.Module):
    """Huggingface AutoModel to generate token embeddings.
    Loads the correct class, e.g. BERT / RoBERTa etc.
    """
    def __init__(self, model_name_or_path: str, max_seq_length: int = 128, model_args: Dict = {}):
        super(Auto, self).__init__()
        self.config_keys = ['max_seq_length']
        self.max_seq_length = max_seq_length

        config = AutoConfig.from_pretrained(model_name_or_path, **model_args)
        self.auto_model = AutoModel.from_pretrained(model_name_or_path, config=config)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.cls_token_id = self.tokenizer.convert_tokens_to_ids([self.tokenizer.cls_token])[0]
        self.sep_token_id = self.tokenizer.convert_tokens_to_ids([self.tokenizer.sep_token])[0]

    def forward(self, features):
        """Returns token_embeddings, cls_token"""
        output_states = self.auto_model(**features)
        output_tokens = output_states[0]
        cls_tokens = output_tokens[:, 0, :]  # CLS token is first token
        features.update({'token_embeddings': output_tokens, 'cls_token_embeddings': cls_tokens, 'attention_mask': features['attention_mask']})

        if len(output_states) > 2:
            hidden_states = output_states[2]
            features.update({'all_layer_embeddings': hidden_states})

        return features

    def get_word_embedding_dimension(self) -> int:
        return self.auto_model.config.hidden_size

    def tokenize(self, text: str) -> List[int]:
        """
        Tokenizes a text and maps tokens to token-ids
        """
        return self.tokenizer.convert_tokens_to_ids(self.tokenizer.tokenize(text))

    def get_sentence_features(self, tokens: List[int], pad_seq_length: int):
        """
        Convert tokenized sentence in its embedding ids, segment ids and mask

        :param tokens:
            a tokenized sentence
        :param pad_seq_length:
            the maximal length of the sequence. Cannot be greater than self.sentence_transformer_config.max_seq_length
        :return: embedding ids, segment ids and mask for the sentence
        """
        pad_seq_length = min(pad_seq_length, self.max_seq_length) + 3 #Add space for special tokens
        return self.tokenizer.prepare_for_model(tokens, max_length=pad_seq_length, pad_to_max_length=True, return_tensors='pt')

    def get_config_dict(self):
        return {key: self.__dict__[key] for key in self.config_keys}

    def save(self, output_path: str):
        self.auto_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        with open(os.path.join(output_path, 'sentence_bert_config.json'), 'w') as fOut:
            json.dump(self.get_config_dict(), fOut, indent=2)

    @staticmethod
    def load(input_path: str):
        with open(os.path.join(input_path, 'sentence_bert_config.json')) as fIn:
            config = json.load(fIn)
        return Auto(model_name_or_path=input_path, **config)





