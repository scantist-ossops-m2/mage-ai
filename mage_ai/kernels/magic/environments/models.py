from __future__ import annotations

import asyncio
import json
import os
import pickle
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import joblib

from mage_ai.kernels.magic.environments.enums import EnvironmentType, EnvironmentUUID
from mage_ai.kernels.magic.environments.pipeline import Pipeline
from mage_ai.kernels.magic.environments.utils import decrypt_secret, encrypt_secret
from mage_ai.settings.repo import get_repo_path, get_variables_dir
from mage_ai.shared.dates import now
from mage_ai.shared.files import (
    exists_async,
    getsize_async,
    makedirs_async,
    read_async,
    safe_delete_dir_async,
    write_async,
)
from mage_ai.shared.models import BaseDataClass
from mage_ai.shared.path_fixer import remove_base_repo_directory_name

MESSAGES_FILENAME = 'messages'
LOCALS_FILENAME = 'locals.pkl'
OUTPUT_FILENAME = 'output.pkl'
OUTPUT_FILENAME = 'output.pkl'
VARIABLES_FILENAME = 'variables.joblib'
ENVIRONMENT_VARIABLES_FILENAME = 'environment_variables.joblib'


@dataclass
class Environment(BaseDataClass):
    environment_variables: Optional[Dict] = None
    type: Optional[EnvironmentType] = EnvironmentType.CODE
    uuid: Optional[str] = EnvironmentUUID.EXECUTION
    variables: Optional[Dict] = None

    def __post_init__(self):
        self.serialize_attribute_enum('type', EnvironmentType)

    @property
    def namespace(self) -> str:
        if self.type and self.uuid:
            return os.path.join(str(self.type), self.uuid)
        return ''

    async def run_process(
        self,
        kernel: Any,
        message: str,
        message_request_uuid: Optional[str] = None,
        output_path: Optional[str] = None,
        process_options: Optional[Dict] = None,
    ) -> Any:
        output_manager = OutputManager.load(
            namespace=self.namespace,
            path=remove_base_repo_directory_name(output_path or get_repo_path()),
            uuid=(message_request_uuid or str(now(True))),
        )

        if EnvironmentType.PIPELINE == self.type and self.uuid:
            process = await Pipeline(
                self.uuid,
                kernel,
                output_manager,
                environment_variables=self.environment_variables,
                variables=self.variables,
            ).run_process(
                message,
                message_request_uuid=message_request_uuid,
                **(process_options or {}),
            )
        else:
            process = kernel.run(
                message,
                message_request_uuid=message_request_uuid,
                output_manager=output_manager,
                **(process_options or {}),
            )

        return process


@dataclass
class ExecutionOutput(BaseDataClass):
    uuid: str
    namespace: str
    path: str
    absolute_path: Optional[str] = None
    environment: Optional[Environment] = None
    messages: Optional[List[Dict]] = field(default_factory=list)
    output: Optional[Any] = None

    def __post_init__(self):
        self.serialize_attribute_class('environment', Environment)
        if not self.environment and self.namespace:
            env_type, env_uuid = os.path.split(self.namespace)
            self.environment = Environment.load(type=env_type, uuid=env_uuid)

    async def delete(self):
        await OutputManager.load(
            namespace=self.namespace,
            path=self.path,
            uuid=self.uuid,
        ).delete()


@dataclass
class OutputManager(BaseDataClass):
    namespace: str
    path: str
    uuid: str

    @classmethod
    async def load_with_messages(
        cls, path: str, namespace: str, limit: Optional[int] = None
    ) -> List[ExecutionOutput]:
        absolute_path = os.path.join(get_variables_dir(), path, namespace)
        if not await exists_async(absolute_path):
            return []

        paths = sorted(
            [fp for fp in os.listdir(absolute_path) if not fp.startswith('.')],
            key=lambda x: x.lower(),
        )
        if limit is not None:
            paths = paths[:limit]

        execution_outputs = await asyncio.gather(*[
            cls.load(
                namespace=namespace,
                path=path,
                uuid=os.path.basename(fpath),
            ).build_output()
            for fpath in paths
        ])
        return execution_outputs

    async def build_output(self) -> ExecutionOutput:
        file_path = os.path.join(self.absolute_path, MESSAGES_FILENAME)
        messages = []
        if await exists_async(file_path):
            text = await read_async(file_path)
            if text:
                for line in text.split('\n'):
                    if line.strip():
                        data = json.loads(line)
                        messages.append(data)

        return ExecutionOutput.load(
            absolute_path=self.absolute_path,
            messages=messages,
            namespace=self.namespace,
            path=self.path,
            uuid=self.uuid,
        )

    @property
    def absolute_path(self) -> str:
        return os.path.join(get_variables_dir(), self.path, self.namespace, self.uuid)

    async def exists(self) -> bool:
        return await exists_async(self.absolute_path) and not await getsize_async(
            self.absolute_path
        )

    async def delete(self, if_empty: Optional[bool] = None) -> None:
        if await exists_async(self.absolute_path) and (
            not if_empty or not await getsize_async(self.absolute_path)
        ):
            await safe_delete_dir_async(self.absolute_path)

    async def append_message(self, data: str, filename: Optional[str] = None) -> None:
        await self.__write(filename or MESSAGES_FILENAME, data, flush=True, mode='a')

    async def store_local_variables(self, data: Any, filename: Optional[str] = None) -> None:
        await self.__store_object(filename or LOCALS_FILENAME, data)

    async def store_output(self, data: Any, filename: Optional[str] = None) -> None:
        await self.__store_object(filename or OUTPUT_FILENAME, data)

    async def store_variables(self, data: Dict, filename: Optional[str] = None) -> None:
        await self.__store_object(filename or VARIABLES_FILENAME, data)

    async def store_environment_variables(
        self, data: Dict, filename: Optional[str] = None
    ) -> None:
        await self.__store_object(filename or ENVIRONMENT_VARIABLES_FILENAME, data)

    async def read_encrypted_dictionary(self, filename: str, ckey: Optional[str] = None) -> Dict:
        text = await read_async(os.path.join(self.absolute_path, filename))
        data = {}
        for key, value in json.loads(text):
            data[key] = decrypt_secret(value.encode(), ckey) if isinstance(value, str) else value
        return data

    async def __store_object(self, filename: str, data: Any) -> None:
        await makedirs_async(self.absolute_path)
        with open(os.path.join(self.absolute_path, filename), 'wb') as file:
            pickle.dump(data, file)

    async def __store_encrypted_dictionary(
        self, filename: str, data: Dict, ckey: Optional[str] = None
    ) -> None:
        await makedirs_async(self.absolute_path)
        data_encrypted = {}
        for key, value in data.items():
            data_encrypted[key] = encrypt_secret(value, ckey) if isinstance(value, str) else value

        joblib.dump(
            data_encrypted,
            os.path.join(self.absolute_path, filename),
        )

    async def __write(
        self, filename: str, data: str, flush: Optional[bool] = None, mode: str = 'w'
    ) -> None:
        await makedirs_async(os.path.dirname(self.absolute_path))
        await write_async(
            os.path.join(self.absolute_path, filename),
            data,
            flush=flush,
            mode=mode,
            overwrite=True,
        )