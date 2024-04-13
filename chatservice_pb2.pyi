from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ConnectRequest(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class ConnectResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class MessageRequest(_message.Message):
    __slots__ = ("sender", "receiver", "message")
    SENDER_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    sender: str
    receiver: str
    message: str
    def __init__(self, sender: _Optional[str] = ..., receiver: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...

class MessageResponse(_message.Message):
    __slots__ = ("sender", "receiver", "message")
    SENDER_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    sender: str
    receiver: str
    message: str
    def __init__(self, sender: _Optional[str] = ..., receiver: _Optional[str] = ..., message: _Optional[str] = ...) -> None: ...
