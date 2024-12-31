import json
import logging
import os

import anthropic
import openai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with LLM providers."""

    def __init__(self, provider: str, model_name: str) -> None:
        """Initialize LLM client.

        Args:
            provider: LLM provider ('openai' or 'anthropic')
            model_name: Name of the model to use

        """
        self.provider = provider.lower()
        self.model_name = model_name

        logger.info(
            f"Initializing LLMClient with provider={provider}, model={model_name}"
        )

        # Load environment variables from .env file in current directory
        if load_dotenv(os.getcwd()+"/.env"):
            logger.info("Successfully loaded .env file")
        else:
            logger.warning(f"No .env file found in current directory {os.getcwd()}")

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment")
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = openai.OpenAI(api_key=api_key)
            logger.info("Successfully initialized OpenAI client")
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not found in environment")
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Successfully initialized Anthropic client")
        else:
            logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")

    def get_response(
        self,
        prompt: str,
        system_prompt: str = "",
        json_response: bool = True,
        temperature: float = 0.1,
        max_tokens: int = 1000,
    ) -> dict | str:
        """Get raw response from LLM.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Dictionary containing the structured recommendations

        """
        logger.info(f"Getting response using {self.provider}")
        logger.debug(f"Prompt: {prompt[:200]}...")  # Log first 200 chars of prompt

        if self.provider == "openai":
            return self._get_openai_response(
                prompt, system_prompt, json_response, temperature
            )
        elif self.provider == "anthropic":
            return self._get_anthropic_response(
                prompt, system_prompt, json_response, temperature, max_tokens
            )
        else:
            logger.error(f"Unsupported provider: {self.provider}")
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_openai_response(
        self,
        prompt: str,
        system_prompt: str = "",
        json_response: bool = True,
        temperature: float = 0.2,
    ) -> dict:
        """Get response from OpenAI API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        logger.info(f"Making OpenAI API call with model {self.model_name}")

        if json_response:
            # First try with strict JSON output
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )

            logger.debug(
                f"Raw OpenAI response: {response.choices[0].message.content[:200]}..."
            )

            try:
                result = json.loads(response.choices[0].message.content)
                logger.info("Successfully parsed OpenAI response as JSON")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse OpenAI response as JSON: {e!s}")
                logger.warning("Attempting to extract JSON from response")

                # If JSON parsing fails, try to extract JSON from the response
                content = response.choices[0].message.content
                # Try to find JSON object in the response
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    logger.info("Successfully extracted and parsed JSON from response")
                    return result
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
            )
            logger.debug(
                f"Raw OpenAI response: {response.choices[0].message.content[:200]}..."
            )
            return response.choices[0].message.content

    def _get_anthropic_response(
        self,
        prompt: str,
        system_prompt: str = "",
        json_response: bool = True,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> dict | str:
        """Get response from Anthropic API."""
        system_prompt = """{system_prompt}

        Human: {prompt}

        Assistant: Here are my responses:"""

        logger.info(f"Making Anthropic API call with model {self.model_name}")

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": system_prompt.format(
                        prompt=prompt, system_prompt=system_prompt
                    ),
                }
            ],
        )

        logger.debug(f"Raw Anthropic response: {response.content[0].text[:200]}...")

        if json_response:
            # Extract JSON from the response
            json_str = response.content[0].text
            # Find the start of the JSON object
            start_idx = json_str.find("{")
            if start_idx == -1:
                logger.error("No JSON object found in Anthropic response")
                raise ValueError("No JSON object found in response")
            json_str = json_str[start_idx:]
            result = json.loads(json_str)
            logger.info("Successfully parsed Anthropic response as JSON")
            return result
        return response.content[0].text
