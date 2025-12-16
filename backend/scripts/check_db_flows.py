from sqlmodel import Session, select, create_engine
import os
import sys

# Add backend to path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.flow import Flow
from app.models.flow_version import FlowVersion

# Adjust path to find database.db in backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_file_name = os.path.join(BASE_DIR, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def check_data():
    print(f"Checking database at {sqlite_file_name}...")
    with Session(engine) as session:
        flows = session.exec(select(Flow)).all()
        print(f"\nFound {len(flows)} Flows:")
        for flow in flows:
            print(f" - ID: {flow.id}, Name: '{flow.name}', Archived: {flow.is_archived}, Updated: {flow.updated_at}")

        versions = session.exec(select(FlowVersion)).all()
        print(f"\nFound {len(versions)} FlowVersions:")
        
        # Check for orphans
        flow_ids = {f.id for f in flows}
        orphans = []
        for v in versions:
            if v.flow_id not in flow_ids:
                orphans.append(v)
            # print(f" - Version ID: {v.id}, Flow ID: {v.flow_id}, Locked: {v.is_locked}")
        
        print(f"Total Versions: {len(versions)}")
        if orphans:
            print(f"\nWARNING: Found {len(orphans)} ORPHAN versions (Flow ID not found in Flow table):")
            for o in orphans:
                print(f" - Orphan Version ID: {o.id}, Flow ID: {o.flow_id}, Created: {o.created_at}, Data Len: {len(o.data)}")
        else:
            print("\nNo orphan versions found (all versions belong to existing flows).")

if __name__ == "__main__":
    check_data()
