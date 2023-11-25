# Imports
import json, logging, requests
from typing import Any, Dict, Iterator, List, Optional
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.pydantic_v1 import Field
from langchain.schema.output import GenerationChunk

# Define logger
logger = logging.getLogger(__name__)

class TextGen(LLM):
    model_url: str
    preset: Optional[str] = None
    max_new_tokens: Optional[int] = 250
    do_sample: bool = Field(True, alias="do_sample")
    temperature: Optional[float] = 1.3
    top_p: Optional[float] = 0.1
    typical_p: Optional[float] = 1
    epsilon_cutoff: Optional[float] = 0  # In 1e-4 units
    eta_cutoff: Optional[float] = 0      # In 1e-4 units
    repetition_penalty: Optional[float] = 1.18
    top_k: Optional[float] = 40
    min_length: Optional[int] = 0
    no_repeat_ngram_size: Optional[int] = 0
    num_beams: Optional[int] = 1
    penalty_alpha: Optional[float] = 0
    length_penalty: Optional[float] = 1
    early_stopping: bool = Field(False, alias="early_stopping")
    seed: int = Field(-1, alias="seed")
    add_bos_token: bool = Field(True, alias="add_bos_token")
    truncation_length: Optional[int] = 2048
    ban_eos_token: bool = Field(False, alias="ban_eos_token")
    skip_special_tokens: bool = Field(True, alias="skip_special_tokens")
    stopping_strings: Optional[List[str]] = []
    streaming: bool = False

    @property
    def _default_params(self) -> Dict[str, Any]:
        return {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.do_sample,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "typical_p": self.typical_p,
            "epsilon_cutoff": self.epsilon_cutoff,
            "eta_cutoff": self.eta_cutoff,
            "repetition_penalty": self.repetition_penalty,
            "top_k": self.top_k,
            "min_length": self.min_length,
            "no_repeat_ngram_size": self.no_repeat_ngram_size,
            "num_beams": self.num_beams,
            "penalty_alpha": self.penalty_alpha,
            "length_penalty": self.length_penalty,
            "early_stopping": self.early_stopping,
            "seed": self.seed,
            "add_bos_token": self.add_bos_token,
            "truncation_length": self.truncation_length,
            "ban_eos_token": self.ban_eos_token,
            "skip_special_tokens": self.skip_special_tokens,
            "stopping_strings": self.stopping_strings,}

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {**{"model_url": self.model_url}, **self._default_params}

    @property
    def _llm_type(self) -> str:
        return "textgen"

    def _get_parameters(self, stop: Optional[List[str]] = None) -> Dict[str, Any]:
        if self.stopping_strings and stop is not None:
            raise ValueError("`stop` found in both the input and default params.")
        if self.preset is None:
            params = self._default_params
        else:
            params = {"preset": self.preset}
        params["stop"] = self.stopping_strings or stop or []
        return params

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,) -> str:
        if self.streaming:
            combined_text_output = ""
            for chunk in self._stream(
                prompt=prompt, stop=stop, run_manager=run_manager, **kwargs):
                combined_text_output += chunk.text
            print(prompt + combined_text_output)
            result = combined_text_output

        else:
            url = f"{self.model_url}/api/v1/generate"
            params = self._get_parameters(stop)
            params["stopping_strings"] = params.pop(
                "stop")
            request = params.copy()
            request["prompt"] = prompt
            response = requests.post(url, json=request)
            if response.status_code == 200:
                result = response.json()["results"][0]["text"]
            else:
                print(f"ERROR: response: {response}")
                result = ""
        return result

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,) -> Iterator[GenerationChunk]:
        try:
            import websocket
        except ImportError:
            raise ImportError(
                "The `websocket-client` package is required for streaming.")
        params = {**self._get_parameters(stop), **kwargs}
        params["stopping_strings"] = params.pop(
            "stop")
        url = f"{self.model_url}/api/v1/stream"
        request = params.copy()
        request["prompt"] = prompt
        websocket_client = websocket.WebSocket()
        websocket_client.connect(url)
        websocket_client.send(json.dumps(request))
        while True:
            result = websocket_client.recv()
            result = json.loads(result)
            if result["event"] == "text_stream":
                chunk = GenerationChunk(
                    text=result["text"],
                    generation_info=None,)
                yield chunk.lstrip()
            elif result["event"] == "stream_end":
                websocket_client.close()
                return
            if run_manager:
                run_manager.on_llm_new_token(token=chunk.text)