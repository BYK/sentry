from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sentry.taskworker.models import PendingTasks
    from sentry.taskworker.service.models import RpcTask


@dataclasses.dataclass
class RetryState:
    """Retry state that is persisted as part of a task"""

    attempts: int
    discard_after_attempt: int | None
    deadletter_after_attempt: int | None
    kind: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_task(cls, task: PendingTasks | RpcTask) -> RetryState:
        return cls(
            attempts=task.retry_attempts,
            discard_after_attempt=task.discard_after_attempt,
            deadletter_after_attempt=task.deadletter_after_attempt,
            kind=task.retry_kind,
        )


class Retry:
    __times: int | None
    __on: Sequence[type] | None
    __ignore: Sequence[type] | None
    __deadletter: bool | None
    __discard: bool | None

    """Used with tasks to define the retry policy for a task"""

    def __init__(
        self,
        times: int | None = None,
        on: Sequence[type] | None = None,
        ignore: Sequence[type] | None = None,
        deadletter: bool | None = None,
        discard: bool | None = None,
    ):
        self.__times = times
        self.__on = on
        self.__ignore = ignore
        self.__deadletter = deadletter
        self.__discard = discard

    def should_retry(self, state: RetryState, exc: Exception) -> bool:
        # No more attempts left
        if state.attempts >= self.__times:
            return False
        # No retries for types on the ignore list
        if self.__ignore and isinstance(exc, self.__ignore):
            return False
        # In the retry allow list
        if self.__on and isinstance(exc, self.__on):
            return True
        # TODO add logging/assertion for no funny business
        return False

    def initial_state(self) -> RetryState:
        return RetryState(
            attempts=0,
            discard_after_attempt=self.__times if self.__discard else None,
            deadletter_after_attempt=self.__times if self.__deadletter else None,
            kind="sentry.taskworker.retry.Retry",
        )


FALLBACK_RETRY = Retry(times=3, deadletter=True)
