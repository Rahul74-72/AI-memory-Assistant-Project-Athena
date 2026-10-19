"""Verify the final archive manifest and SQLite snapshots without extracting paths."""
import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('archive',type=Path)
    args=parser.parse_args()
    checked=0
    with zipfile.ZipFile(args.archive) as archive, tempfile.TemporaryDirectory(prefix='athena-backup-check-') as temporary:
        if archive.testzip():
            raise ValueError('ZIP integrity failed')
        manifest=json.loads(archive.read('BACKUP-MANIFEST.json'))
        for index,item in enumerate(manifest):
            name=PurePosixPath(item['path'])
            if name.is_absolute() or '..' in name.parts:
                raise ValueError('Invalid archive path')
            content=archive.read(item['path'])
            if hashlib.sha256(content).hexdigest()!=item['sha256']:
                raise ValueError('Hash mismatch: '+item['path'])
            if name.suffix in {'.db','.sqlite','.sqlite3'}:
                restored=Path(temporary)/f'{index}.db'
                restored.write_bytes(content)
                connection=sqlite3.connect(restored)
                try:
                    assert connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                finally:
                    connection.close()
            checked+=1
    print(f'Verified {checked} manifest hashes and all included SQLite snapshots.')


if __name__=='__main__':main()
