"""Lab tests for M7 Memory & Persistence."""

import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "reference_agent", "src"))

from agent_course.memory import (
    CheckpointStore,
    Checkpoint,
    MemoryStore,
    MemoryRecord,
    MemoryWritePolicy,
    MemoryReadPolicy,
    ForgettingPolicy,
)
from agent_course.memory.store import MemoryType


def test_checkpoint_save_and_load():
    """Test saving and loading checkpoints."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CheckpointStore(tmpdir)
        
        # Create and save checkpoint
        checkpoint = Checkpoint(
            run_id="test_run_1",
            step_count=5,
            state_snapshot={"status": "running", "data": "test"},
            task={"goal": "Test task"},
        )
        store.save(checkpoint)
        
        # Load and verify
        loaded = store.load("test_run_1")
        assert loaded is not None
        assert loaded.run_id == "test_run_1"
        assert loaded.step_count == 5
        assert loaded.state_snapshot["status"] == "running"


def test_checkpoint_resume_simulation():
    """Test simulating interrupt and resume from checkpoint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = CheckpointStore(tmpdir)
        
        # Simulate first run (interrupted at step 5)
        checkpoint1 = Checkpoint(
            run_id="interrupted_run",
            step_count=5,
            state_snapshot={"progress": 50, "collected": ["a", "b"]},
            task={"goal": "Complete task"},
        )
        store.save(checkpoint1)
        
        # Simulate resume
        loaded = store.load("interrupted_run")
        assert loaded is not None
        assert loaded.step_count == 5
        
        # Continue from step 5
        checkpoint2 = Checkpoint(
            run_id="interrupted_run",
            step_count=10,
            state_snapshot={"progress": 100, "collected": ["a", "b", "c", "d"]},
            task=loaded.task,
        )
        store.save(checkpoint2)
        
        # Verify final state
        final = store.load("interrupted_run")
        assert final.step_count == 10
        assert final.state_snapshot["progress"] == 100


def test_memory_write_policy():
    """Test that memory write policy controls storage."""
    policy = MemoryWritePolicy(
        min_importance=0.5,
        auto_store_user=True,
        auto_store_episodes=False,
    )
    
    # High importance episodic memory
    high_episodic = MemoryRecord(
        id="ep1",
        memory_type=MemoryType.EPISODIC,
        content="Important event",
        source="test",
        importance=0.8,
    )
    
    # Low importance episodic memory
    low_episodic = MemoryRecord(
        id="ep2",
        memory_type=MemoryType.EPISODIC,
        content="Trivial event",
        source="test",
        importance=0.2,
    )
    
    # User memory with high importance (should be stored)
    user_mem = MemoryRecord(
        id="user1",
        memory_type=MemoryType.USER,
        content="User preference",
        source="test",
        importance=0.8,  # High importance
    )
    
    # Episodic auto-store is False, so even high importance won't be stored
    assert not policy.should_store(high_episodic)
    assert not policy.should_store(low_episodic)
    
    # User memory with high importance should be stored
    assert policy.should_store(user_mem)


def test_memory_store_and_retrieve():
    """Test storing and retrieving memories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore(tmpdir)
        
        # Add memories
        store.add(MemoryRecord(
            id="mem1",
            memory_type=MemoryType.SEMANTIC,
            content="Python is a programming language",
            source="conversation",
            importance=0.8,
            tags=["python", "programming"],
        ))
        store.add(MemoryRecord(
            id="mem2",
            memory_type=MemoryType.SEMANTIC,
            content="Java is also a programming language",
            source="conversation",
            importance=0.6,
            tags=["java", "programming"],
        ))
        store.add(MemoryRecord(
            id="mem3",
            memory_type=MemoryType.USER,
            content="User prefers Python",
            source="conversation",
            importance=0.9,
            tags=["preference", "python"],
        ))
        
        # Search for Python-related memories
        results = store.search("Python")
        assert len(results) == 2
        assert any(r.id == "mem1" for r in results)
        assert any(r.id == "mem3" for r in results)
        
        # Get by type
        semantic = store.get_by_type(MemoryType.SEMANTIC)
        assert len(semantic) == 2
        
        user = store.get_by_type(MemoryType.USER)
        assert len(user) == 1


def test_memory_invalidation():
    """Test that invalidated memories are not retrieved."""
    store = MemoryStore()
    
    # Add memories
    store.add(MemoryRecord(
        id="mem1",
        memory_type=MemoryType.SEMANTIC,
        content="Valid memory",
        source="test",
        importance=0.8,
    ))
    store.add(MemoryRecord(
        id="mem2",
        memory_type=MemoryType.SEMANTIC,
        content="Invalid memory",
        source="test",
        importance=0.8,
    ))
    
    # Invalidate one memory
    store.invalidate("mem2")
    
    # Should not be retrievable
    retrieved = store.get("mem2")
    assert retrieved is None
    
    # But should exist in full list
    all_memories = store.list_all(include_invalidated=True)
    assert len(all_memories) == 2
    
    # Active list should only have one
    active_memories = store.list_all(include_invalidated=False)
    assert len(active_memories) == 1


def test_forgetting_policy():
    """Test applying forgetting policy."""
    from datetime import datetime, timedelta
    
    policy = ForgettingPolicy(
        max_age_days=30,
        low_importance_threshold=0.3,
    )
    
    # Create memories with different ages and importance
    old_date = (datetime.now() - timedelta(days=60)).isoformat()
    recent_date = (datetime.now() - timedelta(days=10)).isoformat()
    
    memories = [
        MemoryRecord(
            id="old_low",
            memory_type=MemoryType.SEMANTIC,
            content="Old and low importance",
            source="test",
            importance=0.2,
            created_at=old_date,
        ),
        MemoryRecord(
            id="old_high",
            memory_type=MemoryType.SEMANTIC,
            content="Old but high importance",
            source="test",
            importance=0.8,
            created_at=old_date,  # Still old, will be forgotten due to age
        ),
        MemoryRecord(
            id="recent_low",
            memory_type=MemoryType.SEMANTIC,
            content="Recent but low importance",
            source="test",
            importance=0.2,
            created_at=recent_date,
        ),
        MemoryRecord(
            id="recent_high",
            memory_type=MemoryType.SEMANTIC,
            content="Recent and high importance",
            source="test",
            importance=0.8,
            created_at=recent_date,
        ),
    ]
    
    # Apply forgetting
    to_forget = policy.apply_forgetting(memories)
    
    # Old memories should be forgotten (age > 30 days)
    assert "old_low" in to_forget
    assert "old_high" in to_forget
    
    # Recent low importance should be forgotten (importance < 0.3)
    assert "recent_low" in to_forget
    
    # Recent high importance should be kept
    assert "recent_high" not in to_forget


def test_memory_read_policy():
    """Test memory read policy filtering and ranking."""
    policy = MemoryReadPolicy(
        max_memories=2,
        min_importance=0.5,
        prefer_recent=False,
    )
    
    memories = [
        MemoryRecord(
            id="mem1",
            memory_type=MemoryType.SEMANTIC,
            content="Low importance",
            source="test",
            importance=0.3,
        ),
        MemoryRecord(
            id="mem2",
            memory_type=MemoryType.SEMANTIC,
            content="Medium importance",
            source="test",
            importance=0.6,
        ),
        MemoryRecord(
            id="mem3",
            memory_type=MemoryType.SEMANTIC,
            content="High importance",
            source="test",
            importance=0.9,
        ),
    ]
    
    # Filter and rank
    filtered = policy.filter_and_rank(memories)
    
    # Should only have 2 memories (max_memories)
    assert len(filtered) == 2
    
    # Should be ranked by importance
    assert filtered[0].id == "mem3"  # Highest
    assert filtered[1].id == "mem2"  # Second highest
    
    # Low importance should be filtered out
    assert all(m.id != "mem1" for m in filtered)
