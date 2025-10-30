import json
import logging
from typing import Any, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config as CONFIG

from .key_manager import ApiKeyManager

logger = logging.getLogger(__name__)


google_key_manager = ApiKeyManager(CONFIG.GOOGLE_API_KEY.split(','))


class BaseLLM:
    """
    Stateless LLM 基礎類別
    - 自動處理 API key 的獲取和釋放
    - 子類別只需實作 chain 建立和 response 處理
    """

    def __init__(self, prompt: str, input_vars=None):
        self.prompt = prompt
        self.input_vars = input_vars or []

    def invoke(self, input: dict, config=None, **kwargs):
        while True:
            try:
                return self.invoke_once(input, config, **kwargs)
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg:
                    continue
                else:
                    logger.exception('LLM 呼叫失敗')
                    raise

    def invoke_once(self, input: dict, config=None, **kwargs):
        """
        統一的 invoke_once 實作
        - 自動獲取和釋放 API key
        - 調用子類別的 _build_chain 和 _process_response
        """
        api_key = google_key_manager.get()
        try:
            llm = ChatGoogleGenerativeAI(
                model=CONFIG.LLM_MODEL,
                max_retries=1,
                api_key=api_key,
            )
            chain = self._build_chain(llm)
            response = chain.invoke(input, config, **kwargs)
            return self._process_response(response)

        finally:
            google_key_manager.release(api_key)

    def _build_chain(self, llm: BaseChatModel):
        raise NotImplementedError

    def _process_response(self, response: BaseMessage):
        raise NotImplementedError


class StatelessJsonLLM(BaseLLM):
    """
    JSON response 的 Stateless LLM，支援 Pydantic 模型驗證。支援自動重試 JSON 解析失敗。
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        prompt: str,
        response_model=None,
        response_model_placeholder: str = 'format_instructions',
        input_vars=None,
    ):
        super().__init__(prompt, input_vars)
        self.response_model = response_model
        self.response_model_placeholder = response_model_placeholder

    def invoke(self, input: dict, config=None, **kwargs):
        for attempt in range(self.MAX_RETRIES):
            try:
                return super().invoke(input, config, **kwargs)
            except json.JSONDecodeError:
                logger.debug(f'JSON 解析失敗，重試中... ({attempt + 1}/{self.MAX_RETRIES})')
                continue

    def _build_chain(self, llm: BaseChatModel):
        return create_json_chain(
            model=llm,
            prompt_template=self.prompt,
            response_model=self.response_model,
            response_model_placeholder=self.response_model_placeholder,
            input_vars=self.input_vars,
        )

    def _process_response(self, response: BaseMessage):
        parsed_response = parse_json_response(response)
        if self.response_model:
            return self.response_model(**parsed_response)
        return parsed_response


class StatelessTextLLM(BaseLLM):
    """
    純文字 response 的 Stateless LLM
    """

    def _build_chain(self, llm: BaseChatModel):
        prompt = PromptTemplate(
            template=self.prompt,
            input_variables=self.input_vars,
        )
        return prompt | llm

    def _process_response(self, response: BaseMessage) -> str:
        return response.content


def create_json_chain(
    model: BaseChatModel,
    prompt_template: str,
    response_model=None,
    response_model_placeholder: str = 'format_instructions',
    input_vars=None,
):
    """
    創建標準的 JSON 輸出 LLM chain
    """

    if input_vars is None:
        input_vars = []

    partial_vars = {}
    if response_model:
        if response_model_placeholder not in prompt_template:
            raise ValueError(
                f'Prompt template must contain the placeholder '
                f"'{response_model_placeholder}' for format instructions."
            )

        parser = JsonOutputParser(pydantic_object=response_model)
        partial_vars['format_instructions'] = parser.get_format_instructions()

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=input_vars,
        partial_variables=partial_vars,
    )

    return prompt | model


def parse_json_response(response: BaseMessage) -> Dict[str, Any]:
    """
    解析 LLM 的 JSON 回應，處理常見格式問題
    """

    if not response or not response.content:
        raise ValueError('LLM returned empty response')

    content = response.content.strip()

    # 移除可能的 markdown 包裝
    if content.startswith('```json'):
        content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
    elif content.startswith('```'):
        content = content[3:]
        if content.endswith('```'):
            content = content[:-3]

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f'JSON parse error. Raw content: {repr(content)}')
        raise ValueError(f'Unable to parse LLM JSON response: {str(e)}')
