from sqlmodel import Session, select, create_engine
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models.flow import Flow
from app.models.flow_version import FlowVersion

# Database setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_file_name = os.path.join(BASE_DIR, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def test_delete_logic():
    print(f"Testing delete logic on DB: {sqlite_file_name}")
    with Session(engine) as session:
        # 1. Create Dummy Flow
        flow = Flow(name="Test Delete Bug", data="{}", created_at=datetime.utcnow())
        session.add(flow)
        session.commit()
        session.refresh(flow)
        flow_id = flow.id
        print(f"Created Flow ID: {flow_id}")

        # 2. Create Dummy Version
        version = FlowVersion(flow_id=flow_id, data="{}", created_at=datetime.utcnow(), is_locked=True)
        session.add(version)
        session.commit()
        session.refresh(version)
        version_id = version.id
        print(f"Created Version ID: {version_id} (Locked=True)")

        # 3. Simulate Delete Version Logic (Singular)
        # Verify strict API logic: check lock first
        print("Attempting to delete locked version (Singular)...")
        v_to_del = session.get(FlowVersion, version_id)
        if v_to_del.is_locked:
            print(" -> Blocked by lock (Expected)")
        else:
            session.delete(v_to_del)
            session.commit()
            print(" -> Deleted (Unexpected for locked)")

        # Verify Flow still exists
        f_check = session.get(Flow, flow_id)
        if f_check:
            print(f"Flow {flow_id} still exists.")
        else:
            print(f"CRITICAL: Flow {flow_id} was deleted!")

        # 4. Simulate Bulk Delete Logic
        print("Attempting to delete locked version (Bulk via DB logic)...")
        # Logic mirroring delete_flow_versions in flows.py
        versions_to_del = session.exec(select(FlowVersion).where(FlowVersion.id.in_([version_id]))).all()
        for v in versions_to_del:
            if v.is_locked:
                 print(f" -> Version {v.id} is locked. Bulk delete should fail/raise 400.")
            else:
                 session.delete(v)
        
        # Verify Flow still exists
        f_check = session.get(Flow, flow_id)
        if f_check:
            print(f"Flow {flow_id} still exists.")
        else:
            print(f"CRITICAL: Flow {flow_id} was deleted!")

        # 5. Simulate Unlocking and Deleting
        print("Unlocking version...")
        version.is_locked = False
        session.add(version)
        session.commit()
        
        print("Deleting unlocked version...")
        session.delete(version)
        session.commit()
        print(" -> Deleted version.")

        # Verify Flow still exists
        f_check = session.get(Flow, flow_id)
        if f_check:
            print(f"Flow {flow_id} still exists (Correct).")
        else:
            print(f"CRITICAL: Flow {flow_id} was deleted after version delete!")
            
        # Cleanup
        session.delete(f_check)
        session.commit()
        print("Cleanup complete.")

if __name__ == "__main__":
    test_delete_logic()
