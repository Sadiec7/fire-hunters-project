"""
ia/time_sync_auditor.py
Módulo auditor de sincronización temporal experimental (Tarea 6.A).
"""

from epistemic_guard import audit_temporal_alignment  # type: ignore

__all__ = ["audit_temporal_alignment"]

if __name__ == "__main__":
    print("time_sync_auditor.py OK ->", audit_temporal_alignment("20013D1"))