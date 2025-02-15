# chatbot.py
from enum import Enum
from dataclasses import dataclass
from typing import List, Iterable, TypedDict

from gradio.themes.builder_app import history
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.documents import Document
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import MessagesPlaceholder

from langchain.prompts import ChatPromptTemplate

from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from cogvault.config import Config
from cogvault.data_ingestor import ingest_files
from cogvault.file_loader import File

# SYSTEM_PROMPT = """
# You're having a conversation with an user about excerpts of their files. Try to be helpful and answer their questions. If you don't know the answer, say that you don't know and try to ask clarifying questions.
# """.strip()
#
# PROMPT = """
# Here's the information you have about the excerpts of the files:
#
# <context>
# {context}
# </context>
#
# One file can have multiple excerpts.
#
# Please, respond to the question:
#
# <question>
# question: {question}
# </question>
#
#
# Answer(in question's language):
# """
#
# FILE_TEMPLATE = """
# <file>
#     <name>{name}</name>
#     <content>{content}</content>
# </file>
# """.strip()

SYSTEM_PROMPT = """
تو قراره با کاربر در مورد فایل ارايه شده توسط کاربر، مکالمه به زبان فارسی داشته باشی. به سوالات کاربر جواب بده و اگر جواب سوالی را طبق متن ارايه شده نمیدونی، از کاربر بخواه تا منظورشو به وضوح بگه.
""".strip()

PROMPT = """
در اینجا اطلاعاتی در مورد بخش گلچین شده از متن فایل آمده است :

<محتوا>
{context}
</محتوا>

یک فایل یا متن میتونه شامل چندین بخش باشه.

لطفا به پرسش کاربر مطابق زبان کاربر جواب بده:

<سوال>
{question}
</سوال>

جواب:
"""

FILE_TEMPLATE = """
<file>
    <name>{name}</name>
    <content>{content}</content>
</file>
""".strip()
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", PROMPT),
    ]
)

history = []
class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    role: Role
    content: str


@dataclass
class ChunkEvent:
    content: str


@dataclass
class SourcesEvent:
    content: List[Document]


@dataclass
class FinalAnswerEvent:
    content: str


class State(TypedDict):
    question: str
    chat_history: List[BaseMessage]
    context: List[Document]
    answer: str


def _remove_thinking_from_message(message: str) -> str:
    close_tag = "</think>"
    tag_length = len(close_tag)
    return message[message.find(close_tag) + tag_length:].strip()


def create_history(welcome_message=None):
    """Create a chat history, optionally including a welcome message."""
    history = []
    if welcome_message:
        history.append({
            "role": welcome_message.role,  # Assuming role is a string
            "content": welcome_message.content
        })
    return history


class Chatbot:
    def __init__(self, files: List[File]):
        self.files = files
        self.retriever = ingest_files(files)
        # print('chatbot init')
        self.llm = ChatOllama(
            model=Config.Model.NAME,
            temperature=Config.Model.TEMPERATURE,
            verbose=False,
            keep_alive=-1,
        )
        self.workflow = self._create_workflow()
        # print('df')

    def _format_docs(self, docs: List[Document]) -> str:
        passage = "\n\n".join(
            FILE_TEMPLATE.format(name=doc.metadata["source"], content=doc.page_content)
            for doc in docs
        )
        return passage

    def _retrieve(self, state: State):
        context = self.retriever.invoke(state["question"])
        # print("Retrieved Context:", context)  # Debug print
        return {"context": context}

    def _generate(self, state: State):
        messages = PROMPT_TEMPLATE.invoke(
            {
                "question": state["question"],
                "context": self._format_docs(state["context"]),
                "chat_history": state["chat_history"],
            }
        )

        answer = self.llm.invoke(messages)
        # print("Generated Answer:", answer.content)  # Debug print
        return {"answer": answer}

    def _ask_model(
            self, prompt: str, chat_history: List[Message]
    ) -> Iterable[SourcesEvent | ChunkEvent | FinalAnswerEvent]:


        payload = {"question": prompt, "chat_history": history}
        config = {
            "configurable": {"thread_id": 42},
        }
        for event_type, event_data in self.workflow.stream(
                payload,
                config=config,
                stream_mode=["messages"],  # Only stream updates
        ):
            # print("Event Type:", event_type)  # Debug print
            # print("Event Data:", event_data)  # Debug print
            if event_type == "messages":
                chunk, _ = event_data
                yield ChunkEvent(chunk.content)
            # if event_type == "updates":
            #     if "_retrieve" in event_data:
            #         documents = event_data["_retrieve"]["context"]
            #         yield SourcesEvent(documents)
            #     if "_generate" in event_data:
            #         answer = event_data["_generate"]["answer"]
            #         yield FinalAnswerEvent(answer.content)

    def ask(
            self, prompt: str, chat_history: List[Message]
    ) -> Iterable[SourcesEvent | ChunkEvent | FinalAnswerEvent]:
        # print("Asking question:", prompt)  # Debug print
        for event in self._ask_model(prompt, chat_history):
            # print("Yielding event:", event)  # Debug print
            yield event

    # def _create_workflow(self) -> CompiledStateGraph:
    #     graph_builder = StateGraph(State).add_sequence([self._retrieve, self._generate])
    #     graph_builder.add_edge(START, "_retrieve")
    #     return graph_builder.compile()
    def _create_workflow(self) -> CompiledStateGraph:
        graph_builder = StateGraph(State)

        # Add nodes using string identifiers
        graph_builder.add_node("_retrieve", self._retrieve)
        graph_builder.add_node("_generate", self._generate)

        # Define the edges using string identifiers
        graph_builder.add_edge(START, "_retrieve")
        graph_builder.add_edge("_retrieve", "_generate")

        return graph_builder.compile()

    # def _ask_model(
    #     self, prompt: str, chat_history: List[Message]
    # ) -> Iterable[SourcesEvent | ChunkEvent | FinalAnswerEvent]:
    #     history = [
    #         AIMessage(m.content) if isinstance(m, AIMessage) else HumanMessage(m.content)
    #         for m in chat_history
    #     ]
    #
    #     payload = {"question": prompt, "chat_history": history}
    #     config = {
    #         "configurable": {"thread_id": 42},
    #     }
    #     for event_type, event_data in self.workflow.stream(
    #         payload,
    #         config=config,
    #         stream_mode=["messages"],# "messages"], ["updates"], "messages"],
    #     ):
    #         if event_type == "messages":
    #             chunk, _ = event_data
    #             yield ChunkEvent(chunk.content)
    #         if event_type == "updates":
    #             if "_retrieve" in event_data:
    #                 documents = event_data["_retrieve"]["context"]
    #                 yield SourcesEvent(documents)
    #             if "_generate" in event_data:
    #                 answer = event_data["_generate"]["answer"]
    #                 yield FinalAnswerEvent(answer.content)

    def ask(
            self, prompt: str
    ) -> Iterable[SourcesEvent | ChunkEvent | FinalAnswerEvent]:
        # print("Asking question:", prompt)  # Debug print

        # Convert chat_history to BaseMessage objects
        # history = [
        #     AIMessage(content=m.content) if m.role == Role.ASSISTANT else HumanMessage(content=m.content)
        #     for m in chat_history
        # ]

        # Append the user's question to the chat history

        full_response = ""
        # Process the question and get the response
        for event in self._ask_model(prompt, history):
            # print("Yielding event:", event)  # Debug print
            # if isinstance(event, FinalAnswerEvent):
            #     Append the assistant's response to the chat history
                # history.append(AIMessage(content=event.content))
                # chat_history.append(Message(role=Role.ASSISTANT, content=event.content))
                # print("Updated chat history:", chat_history)  # Debug print
            yield event
            # print(event.content)
            full_response += event.content
        # print('full=', full_response)
        history.append(HumanMessage(content=prompt))
        history.append(AIMessage(content= full_response ) )
        print('History=', history)









