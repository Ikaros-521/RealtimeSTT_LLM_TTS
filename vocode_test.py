import asyncio
import signal

import vocode
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
)
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
# from vocode.streaming.agent.zhipu_agent import ZHIPUAgent
# from vocode.streaming.models.agent import ZHIPUAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import AzureSynthesizerConfig
from vocode.streaming.synthesizer.azure_synthesizer import AzureSynthesizer
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber

# these can also be set as environment variables
vocode.setenv(
    OPENAI_API_KEY="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",
    ZHIPU_API_KEY="sk-",
    DEEPGRAM_API_KEY="e9bdeee820fd3652ff813e85d3cdd3a9d270524c",
    AZURE_SPEECH_KEY="e7a205b2d39949f3a2447405ab39fb1b",
    AZURE_SPEECH_REGION="japanwest",
)


async def main():
    microphone_input, speaker_output = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=True,
    )

    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=DeepgramTranscriber(
            DeepgramTranscriberConfig.from_input_device(
                microphone_input, endpointing_config=PunctuationEndpointingConfig()
            )
        ),
        agent=ChatGPTAgent(
            ChatGPTAgentConfig(
                initial_message=BaseMessage(text="Hello!"),
                prompt_preamble="Have a pleasant conversation about life",
            ),
        ),
        # agent=ZHIPUAgent(
        #     ZHIPUAgentConfig(
        #         initial_message=BaseMessage(text="Hello!"),
        #         prompt_preamble="Have a pleasant conversation about life",
        #     ),
        #     zhipu_api_key=".AuIX3O5ktKuQVMtC"
        # ),
        synthesizer=AzureSynthesizer(
            AzureSynthesizerConfig.from_output_device(speaker_output)
        ),
    )
    await conversation.start()
    print("Conversation started, press Ctrl+C to end")
    signal.signal(
        signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate())
    )
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    asyncio.run(main())
