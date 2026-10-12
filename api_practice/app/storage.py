"""Document storage behind a small repository class.

TinyDB is a file-backed JSON document database: no server to install, but the
same document-shaped thinking as MongoDB or DynamoDB. Routes only talk to
`ObservationRepo`, so swapping the backend touches this file alone.
"""

import uuid
from pathlib import Path

from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

Obs = Query()


class DuplicateError(Exception):
    pass


class ObservationRepo:
    def __init__(self, db_path: str):
        if db_path == ":memory:":
            self.db = TinyDB(storage=MemoryStorage)
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.db = TinyDB(db_path, indent=2)
        self.table = self.db.table("observations")

    def create(self, doc: dict) -> dict:
        # Natural key: one report per station per timestamp. In DynamoDB this
        # would be the partition key (station) + sort key (observed_at).
        if self.table.contains((Obs.station == doc["station"]) & (Obs.observed_at == doc["observed_at"])):
            raise DuplicateError(f"{doc['station']} already has a report at {doc['observed_at']}")
        doc = {"id": uuid.uuid4().hex, **doc}
        self.table.insert(doc)
        return doc

    def get(self, obs_id: str) -> dict | None:
        return self.table.get(Obs.id == obs_id)

    def list(self, station=None, since=None, until=None, limit=20, offset=0) -> tuple[list[dict], int]:
        cond = Obs.id.exists()
        if station:
            cond &= Obs.station == station
        # ISO-8601 strings in the same timezone sort correctly as plain strings.
        if since:
            cond &= Obs.observed_at >= since
        if until:
            cond &= Obs.observed_at <= until
        docs = sorted(self.table.search(cond), key=lambda d: d["observed_at"], reverse=True)
        return docs[offset : offset + limit], len(docs)

    def update(self, obs_id: str, changes: dict) -> dict | None:
        if not self.table.update(changes, Obs.id == obs_id):
            return None
        return self.get(obs_id)

    def delete(self, obs_id: str) -> bool:
        return bool(self.table.remove(Obs.id == obs_id))

    def close(self):
        self.db.close()
