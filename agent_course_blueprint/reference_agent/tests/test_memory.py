"""Tests for memory and persistence module."""

import pytest
import tempfile
from pathlib import Path

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


class TestCheckpoint:
    """Tests for Checkpoint dataclass."""
    
    def test_checkpoint_creation(self):
        """Test creating a checkpoint."""
        checkpoint = Checkpoint(
            run_id="test_run",
            step_count=5,
            state_snapshot={"status": "running"},
            task={"goal": "test task"},
        )
        assert checkpoint.run_id == "test_run"
        assert checkpoint.step_count == 5
        assert checkpoint.state_snapshot["status"] == "running"
    
    def test_checkpoint_serialization(self):
        """Test checkpoint to_dict and from_dict."""
        checkpoint = Checkpoint(
            run_id="test_run",
            step_count=5,
            state_snapshot={"status": "running"},
            task={"goal": "test task"},
        )
        data = checkpoint.to_dict()
        restored = Checkpoint.from_dict(data)
        assert restored.run_id == checkpoint.run_id
        assert restored.step_count == checkpoint.step_count


class TestCheckpointStore:
    """Tests for CheckpointStore."""
    
    def test_in_memory_store(self):
        """Test in-memory checkpoint storage."""
        store = CheckpointStore()
        checkpoint = Checkpoint(
            run_id="test_run",
            step_count=5,
            state_snapshot={},
            task={},
        )
        store.save(checkpoint)
        loaded = store.load("test_run")
        assert loaded is not None
        assert loaded.run_id == "test_run"
    
    def test_file_based_store(self):
        """Test file-based checkpoint storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CheckpointStore(tmpdir)
            checkpoint = Checkpoint(
                run_id="test_run",
                step_count=5,
                state_snapshot={},
                task={},
            )
            store.save(checkpoint)
            
            # Create new store instance to test loading
            store2 = CheckpointStore(tmpdir)
            loaded = store2.load("test_run")
            assert loaded is not None
            assert loaded.run_id == "test_run"
    
    def test_checkpoint_not_found(self):
        """Test loading non-existent checkpoint."""
        store = CheckpointStore()
        loaded = store.load("nonexistent")
        assert loaded is None
    
    def test_delete_checkpoint(self):
        """Test deleting a checkpoint."""
        store = CheckpointStore()
        checkpoint = Checkpoint(
            run_id="test_run",
            step_count=5,
            state_snapshot={},
            task={},
        )
        store.save(checkpoint)
        assert store.exists("test_run")
        
        deleted = store.delete("test_run")
        assert deleted is True
        assert not store.exists("test_run")
    
    def test_list_checkpoints(self):
        """Test listing all checkpoints."""
        store = CheckpointStore()
        for i in range(3):
            checkpoint = Checkpoint(
                run_id=f"run_{i}",
                step_count=i,
                state_snapshot={},
                task={},
            )
            store.save(checkpoint)
        
        checkpoints = store.list_checkpoints()
        assert len(checkpoints) == 3
        assert "run_0" in checkpoints
        assert "run_1" in checkpoints
        assert "run_2" in checkpoints


class TestMemoryRecord:
    """Tests for MemoryRecord."""
    
    def test_memory_creation(self):
        """Test creating a memory record."""
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="Python is a programming language",
            source="conversation",
        )
        assert memory.id == "mem_1"
        assert memory.memory_type == MemoryType.SEMANTIC
        assert memory.content == "Python is a programming language"
    
    def test_memory_touch(self):
        """Test updating access metadata."""
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="test",
            source="test",
        )
        assert memory.access_count == 0
        memory.touch()
        assert memory.access_count == 1
        assert memory.last_accessed is not None
    
    def test_memory_serialization(self):
        """Test memory to_dict and from_dict."""
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.USER,
            content="User prefers Python",
            source="conversation",
            importance=0.8,
            tags=["preference", "python"],
        )
        data = memory.to_dict()
        restored = MemoryRecord.from_dict(data)
        assert restored.id == memory.id
        assert restored.memory_type == memory.memory_type
        assert restored.importance == memory.importance
        assert restored.tags == memory.tags


class TestMemoryStore:
    """Tests for MemoryStore."""
    
    def test_in_memory_store(self):
        """Test in-memory memory storage."""
        store = MemoryStore()
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="test",
            source="test",
        )
        store.add(memory)
        loaded = store.get("mem_1")
        assert loaded is not None
        assert loaded.id == "mem_1"
    
    def test_file_based_store(self):
        """Test file-based memory storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(tmpdir)
            memory = MemoryRecord(
                id="mem_1",
                memory_type=MemoryType.SEMANTIC,
                content="test",
                source="test",
            )
            store.add(memory)
            
            # Create new store instance to test loading
            store2 = MemoryStore(tmpdir)
            loaded = store2.get("mem_1")
            assert loaded is not None
            assert loaded.id == "mem_1"
    
    def test_get_by_type(self):
        """Test retrieving memories by type."""
        store = MemoryStore()
        for i in range(3):
            store.add(MemoryRecord(
                id=f"semantic_{i}",
                memory_type=MemoryType.SEMANTIC,
                content=f"semantic {i}",
                source="test",
            ))
        for i in range(2):
            store.add(MemoryRecord(
                id=f"episodic_{i}",
                memory_type=MemoryType.EPISODIC,
                content=f"episodic {i}",
                source="test",
            ))
        
        semantic = store.get_by_type(MemoryType.SEMANTIC)
        assert len(semantic) == 3
        
        episodic = store.get_by_type(MemoryType.EPISODIC)
        assert len(episodic) == 2
    
    def test_search_memories(self):
        """Test searching memories by content."""
        store = MemoryStore()
        store.add(MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="Python is great",
            source="test",
        ))
        store.add(MemoryRecord(
            id="mem_2",
            memory_type=MemoryType.SEMANTIC,
            content="Java is okay",
            source="test",
        ))
        
        results = store.search("Python")
        assert len(results) == 1
        assert results[0].id == "mem_1"
    
    def test_invalidate_memory(self):
        """Test invalidating a memory."""
        store = MemoryStore()
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="test",
            source="test",
        )
        store.add(memory)
        
        invalidated = store.invalidate("mem_1")
        assert invalidated is True
        
        # Should not be retrievable
        loaded = store.get("mem_1")
        assert loaded is None
        
        # But should exist in full list
        all_memories = store.list_all(include_invalidated=True)
        assert len(all_memories) == 1
    
    def test_delete_memory(self):
        """Test permanently deleting a memory."""
        store = MemoryStore()
        memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.SEMANTIC,
            content="test",
            source="test",
        )
        store.add(memory)
        
        deleted = store.delete("mem_1")
        assert deleted is True
        
        all_memories = store.list_all(include_invalidated=True)
        assert len(all_memories) == 0
    
    def test_count_memories(self):
        """Test counting memories."""
        store = MemoryStore()
        for i in range(5):
            store.add(MemoryRecord(
                id=f"mem_{i}",
                memory_type=MemoryType.SEMANTIC,
                content=f"test {i}",
                source="test",
            ))
        
        assert store.count() == 5
        assert store.count(MemoryType.SEMANTIC) == 5
        assert store.count(MemoryType.EPISODIC) == 0


class TestMemoryWritePolicy:
    """Tests for MemoryWritePolicy."""
    
    def test_importance_threshold(self):
        """Test importance threshold filtering."""
        # Enable episodic storage for this test
        policy = MemoryWritePolicy(min_importance=0.5, auto_store_episodes=True)
        
        low_importance = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content="test",
            source="test",
            importance=0.3,
        )
        high_importance = MemoryRecord(
            id="mem_2",
            memory_type=MemoryType.EPISODIC,
            content="test",
            source="test",
            importance=0.7,
        )
        
        assert not policy.should_store(low_importance)
        assert policy.should_store(high_importance)
    
    def test_user_memory_auto_store(self):
        """Test automatic storage of user memories."""
        policy = MemoryWritePolicy(auto_store_user=True, min_importance=0.0)
        
        user_memory = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.USER,
            content="User preference",
            source="test",
            importance=0.1,
        )
        
        assert policy.should_store(user_memory)
    
    def test_episodic_memory_policy(self):
        """Test episodic memory storage policy."""
        policy_auto = MemoryWritePolicy(auto_store_episodes=True, min_importance=0.0)
        policy_manual = MemoryWritePolicy(auto_store_episodes=False, min_importance=0.0)
        
        episodic = MemoryRecord(
            id="mem_1",
            memory_type=MemoryType.EPISODIC,
            content="Event",
            source="test",
            importance=0.1,
        )
        
        assert policy_auto.should_store(episodic)
        assert not policy_manual.should_store(episodic)


class TestMemoryReadPolicy:
    """Tests for MemoryReadPolicy."""
    
    def test_filter_by_importance(self):
        """Test filtering by importance."""
        policy = MemoryReadPolicy(min_importance=0.5)
        
        memories = [
            MemoryRecord(id="1", memory_type=MemoryType.SEMANTIC, content="low", source="test", importance=0.3),
            MemoryRecord(id="2", memory_type=MemoryType.SEMANTIC, content="high", source="test", importance=0.7),
        ]
        
        filtered = policy.filter_and_rank(memories)
        assert len(filtered) == 1
        assert filtered[0].id == "2"
    
    def test_max_memories_limit(self):
        """Test maximum memories limit."""
        policy = MemoryReadPolicy(max_memories=2, min_importance=0.0)
        
        memories = [
            MemoryRecord(id=f"{i}", memory_type=MemoryType.SEMANTIC, content=f"mem {i}", source="test", importance=0.5)
            for i in range(5)
        ]
        
        filtered = policy.filter_and_rank(memories)
        assert len(filtered) == 2
    
    def test_ranking_by_importance(self):
        """Test ranking by importance."""
        policy = MemoryReadPolicy(max_memories=10, min_importance=0.0, prefer_recent=False)
        
        memories = [
            MemoryRecord(id="1", memory_type=MemoryType.SEMANTIC, content="low", source="test", importance=0.3),
            MemoryRecord(id="2", memory_type=MemoryType.SEMANTIC, content="high", source="test", importance=0.9),
            MemoryRecord(id="3", memory_type=MemoryType.SEMANTIC, content="mid", source="test", importance=0.6),
        ]
        
        ranked = policy.filter_and_rank(memories)
        assert ranked[0].id == "2"  # Highest importance
        assert ranked[1].id == "3"
        assert ranked[2].id == "1"


class TestForgettingPolicy:
    """Tests for ForgettingPolicy."""
    
    def test_age_based_forgetting(self):
        """Test forgetting based on age."""
        from datetime import datetime, timedelta
        
        policy = ForgettingPolicy(max_age_days=30)
        
        # Create old memory
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        old_memory = MemoryRecord(
            id="old",
            memory_type=MemoryType.SEMANTIC,
            content="old",
            source="test",
            created_at=old_date,
        )
        
        # Create new memory
        new_memory = MemoryRecord(
            id="new",
            memory_type=MemoryType.SEMANTIC,
            content="new",
            source="test",
        )
        
        assert policy.should_forget(old_memory)
        assert not policy.should_forget(new_memory)
    
    def test_importance_based_forgetting(self):
        """Test forgetting based on importance."""
        policy = ForgettingPolicy(low_importance_threshold=0.3)
        
        low_importance = MemoryRecord(
            id="low",
            memory_type=MemoryType.SEMANTIC,
            content="low",
            source="test",
            importance=0.1,
        )
        high_importance = MemoryRecord(
            id="high",
            memory_type=MemoryType.SEMANTIC,
            content="high",
            source="test",
            importance=0.8,
        )
        
        assert policy.should_forget(low_importance)
        assert not policy.should_forget(high_importance)
    
    def test_apply_forgetting(self):
        """Test applying forgetting to multiple memories."""
        policy = ForgettingPolicy(low_importance_threshold=0.5)
        
        memories = [
            MemoryRecord(id="1", memory_type=MemoryType.SEMANTIC, content="low", source="test", importance=0.2),
            MemoryRecord(id="2", memory_type=MemoryType.SEMANTIC, content="high", source="test", importance=0.8),
            MemoryRecord(id="3", memory_type=MemoryType.SEMANTIC, content="mid", source="test", importance=0.4),
        ]
        
        to_forget = policy.apply_forgetting(memories)
        assert "1" in to_forget
        assert "3" in to_forget
        assert "2" not in to_forget
    
    def test_conflict_resolution(self):
        """Test conflict resolution between memories."""
        policy = ForgettingPolicy()
        
        old_memory = MemoryRecord(
            id="old",
            memory_type=MemoryType.SEMANTIC,
            content="old info",
            source="test",
            importance=0.5,
        )
        new_memory = MemoryRecord(
            id="new",
            memory_type=MemoryType.SEMANTIC,
            content="new info",
            source="test",
            importance=0.7,
        )
        
        # New is more important, should keep new
        kept = policy.resolve_conflict(old_memory, new_memory)
        assert kept.id == "new"
        
        # Old is much more important (more than 1.5x new), should keep old
        old_memory.importance = 1.0  # 1.0 > 0.7 * 1.5 = 1.05 is false, but close
        new_memory.importance = 0.5  # Now 1.0 > 0.5 * 1.5 = 0.75 is true
        kept = policy.resolve_conflict(old_memory, new_memory)
        assert kept.id == "old"
