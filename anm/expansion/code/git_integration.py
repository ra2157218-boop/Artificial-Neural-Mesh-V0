# ============================================================
# ANM V0-OpenSource — GIT INTEGRATION (MAXIMUM LEVEL)
#  Version Control • Rollback • Branch Management • Safety
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import subprocess
import os
import json
import time


@dataclass
class GitCommit:
    """Git commit information."""
    hash: str
    short_hash: str
    message: str
    author: str
    timestamp: str


@dataclass
class GitStatus:
    """Git repository status."""
    clean: bool
    modified_files: List[str]
    untracked_files: List[str]
    staged_files: List[str]
    current_branch: str


class GitIntegration:
    """
    MAXIMUM LEVEL Git Integration.
    
    Features:
    - Automatic commits for code changes
    - Branch management for experiments
    - Rollback capability
    - Change tracking
    - Safety verification before commits
    - Diff generation
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.expansion_branch_prefix = "anm-expansion/"
        
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return (self.repo_path / ".git").exists()
    
    def get_status(self) -> GitStatus:
        """Get current git status."""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            current_branch = result.stdout.strip()
            
            # Get status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            modified = []
            untracked = []
            staged = []
            
            for line in result.stdout.splitlines():
                if line.startswith("??"):
                    untracked.append(line[3:])
                elif line.startswith(" M"):
                    modified.append(line[3:])
                elif line.startswith("M "):
                    staged.append(line[3:])
                elif line.startswith("A "):
                    staged.append(line[3:])
            
            return GitStatus(
                clean=len(modified) == 0 and len(untracked) == 0 and len(staged) == 0,
                modified_files=modified,
                untracked_files=untracked,
                staged_files=staged,
                current_branch=current_branch,
            )
        except Exception:
            return GitStatus(
                clean=True,
                modified_files=[],
                untracked_files=[],
                staged_files=[],
                current_branch="unknown",
            )
    
    def create_expansion_branch(self, domain: str) -> Dict[str, Any]:
        """Create a new branch for expansion."""
        branch_name = f"{self.expansion_branch_prefix}{domain}-{int(time.time())}"
        
        try:
            # Create and checkout branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "branch": branch_name,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def stage_files(self, files: List[str]) -> Dict[str, Any]:
        """Stage files for commit."""
        try:
            for file in files:
                subprocess.run(
                    ["git", "add", file],
                    cwd=self.repo_path,
                    capture_output=True,
                )
            
            return {"success": True, "staged": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a commit with safety verification."""
        # Verify changes before committing
        status = self.get_status()
        
        if status.clean:
            return {
                "success": False,
                "error": "No changes to commit",
            }
        
        try:
            # Stage files if specified
            if files:
                self.stage_files(files)
            else:
                # Stage all changes
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.repo_path,
                    capture_output=True,
                )
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )
                
                return {
                    "success": True,
                    "commit_hash": hash_result.stdout.strip()[:8],
                    "message": message,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_recent_commits(self, limit: int = 10) -> List[GitCommit]:
        """Get recent commits."""
        commits = []
        
        try:
            result = subprocess.run(
                ["git", "log", f"-{limit}", "--format=%H|%h|%s|%an|%ai"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            for line in result.stdout.splitlines():
                parts = line.split("|")
                if len(parts) >= 5:
                    commits.append(GitCommit(
                        hash=parts[0],
                        short_hash=parts[1],
                        message=parts[2],
                        author=parts[3],
                        timestamp=parts[4],
                    ))
        except Exception:
            pass
        
        return commits
    
    def rollback(self, commit_hash: str, hard: bool = False) -> Dict[str, Any]:
        """Rollback to a previous commit."""
        try:
            mode = "--hard" if hard else "--soft"
            result = subprocess.run(
                ["git", "reset", mode, commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "rolled_back_to": commit_hash,
                    "mode": "hard" if hard else "soft",
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def get_diff(self, commit_a: str = "HEAD~1", commit_b: str = "HEAD") -> str:
        """Get diff between commits."""
        try:
            result = subprocess.run(
                ["git", "diff", commit_a, commit_b],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout
        except Exception:
            return ""
    
    def stash_changes(self, message: str = "") -> Dict[str, Any]:
        """Stash current changes."""
        try:
            cmd = ["git", "stash", "push"]
            if message:
                cmd.extend(["-m", message])
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def pop_stash(self) -> Dict[str, Any]:
        """Pop stashed changes."""
        try:
            result = subprocess.run(
                ["git", "stash", "pop"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_safety_checkpoint(self, domain: str) -> Dict[str, Any]:
        """Create a safety checkpoint before major changes."""
        checkpoint_id = f"checkpoint-{domain}-{int(time.time())}"
        
        # Create a tag for easy rollback
        try:
            # First commit any pending changes
            status = self.get_status()
            if not status.clean:
                self.commit(f"[CHECKPOINT] Pre-{domain} expansion state")
            
            # Create tag
            subprocess.run(
                ["git", "tag", checkpoint_id],
                cwd=self.repo_path,
                capture_output=True,
            )
            
            return {
                "success": True,
                "checkpoint_id": checkpoint_id,
                "message": f"Checkpoint created. Rollback with: git reset --hard {checkpoint_id}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
