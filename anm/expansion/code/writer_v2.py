# ============================================================
# ANM V0-OpenSource — CODE WRITER V2 (MAXIMUM LEVEL)
#  Template Engine • AST Generation • Auto-Testing • Git Integration
# ============================================================

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import os
import json

from anm.expansion.code.validator import CodeValidator, ValidationResult
from anm.expansion.code.git_integration import GitIntegration


class CodeWriterV2:
    """
    MAXIMUM LEVEL Code Writer with full validation and Git integration.
    
    Features:
    - Template-based code generation
    - AST validation before writing
    - Automatic linting and fixing
    - Type stub generation
    - Test file generation
    - Git integration with safety checkpoints
    - Rollback capability
    """
    
    def __init__(
        self,
        base_path: str = "anm/specialists",
        validate: bool = True,
        use_git: bool = True,
    ):
        self.base_path = Path(base_path)
        self.validator = CodeValidator() if validate else None
        self.git = GitIntegration() if use_git else None
    
    def create_specialist_module(
        self,
        domain: str,
        code_output: str,
        research_data: Dict[str, Any],
        create_tests: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a complete specialist module with validation.
        """
        # Create safety checkpoint
        if self.git and self.git.is_git_repo():
            checkpoint = self.git.create_safety_checkpoint(domain)
        else:
            checkpoint = None
        
        module_dir = self.base_path / domain
        module_dir.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        validation_results = {}
        
        try:
            # Generate module code
            module_code = self._generate_module_code(domain, code_output, research_data)
            
            # Validate module code
            if self.validator:
                validation = self.validator.validate(module_code, f"{domain}_llm.py")
                validation_results["module"] = validation
                
                if not validation.valid:
                    # Try auto-fix
                    fixed_code, fixes = self.validator.auto_fix(module_code)
                    if fixes:
                        module_code = fixed_code
                        validation = self.validator.validate(module_code, f"{domain}_llm.py")
                        validation_results["module_after_fix"] = validation
            
            # Write module file
            module_path = module_dir / f"{domain}_llm.py"
            module_path.write_text(module_code)
            created_files.append(str(module_path))
            
            # Generate and write training script
            training_code = self._generate_training_script(domain, research_data)
            if self.validator:
                validation_results["training"] = self.validator.validate(training_code, "train.py")
            
            training_path = module_dir / "train.py"
            training_path.write_text(training_code)
            created_files.append(str(training_path))
            
            # Generate __init__.py
            init_code = self._generate_init(domain)
            init_path = module_dir / "__init__.py"
            init_path.write_text(init_code)
            created_files.append(str(init_path))
            
            # Generate tests if requested
            if create_tests:
                test_dir = module_dir / "tests"
                test_dir.mkdir(exist_ok=True)
                
                test_code = self._generate_tests(domain)
                test_path = test_dir / f"test_{domain}_llm.py"
                test_path.write_text(test_code)
                created_files.append(str(test_path))
                
                test_init = test_dir / "__init__.py"
                test_init.write_text("")
                created_files.append(str(test_init))
            
            # Create data directory
            (module_dir / "data").mkdir(exist_ok=True)
            (module_dir / "checkpoints").mkdir(exist_ok=True)
            
            # Generate README
            readme_code = self._generate_readme(domain, research_data)
            readme_path = module_dir / "README.md"
            readme_path.write_text(readme_code)
            created_files.append(str(readme_path))
            
            # Commit to git
            if self.git and self.git.is_git_repo():
                commit_result = self.git.commit(
                    f"[ANM-Expansion] Add {domain} specialist module",
                    files=created_files,
                )
            else:
                commit_result = None
            
            return {
                "success": True,
                "module_dir": str(module_dir),
                "module_path": str(module_path),
                "training_script_path": str(training_path),
                "created_files": created_files,
                "validation": {
                    k: {"valid": v.valid, "errors": len(v.errors), "warnings": len(v.warnings)}
                    for k, v in validation_results.items()
                },
                "checkpoint": checkpoint,
                "commit": commit_result,
            }
            
        except Exception as e:
            # Rollback on failure
            if checkpoint and self.git:
                self.git.rollback(checkpoint["checkpoint_id"], hard=True)
            
            return {
                "success": False,
                "error": str(e),
                "rollback_performed": checkpoint is not None,
            }
    
    def _generate_module_code(
        self, domain: str, code_output: str, research_data: Dict[str, Any]
    ) -> str:
        """Generate specialist module code."""
        domain_cap = domain.capitalize()
        
        return f'''# ============================================================
# ANM V0-OpenSource — {domain_cap.upper()} SPECIALIST (Auto-Generated)
#  Domain: {domain}
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional, List
import subprocess


class {domain_cap}LLM:
    """
    {domain_cap} domain specialist for ANM V0-OpenSource.
    
    Auto-generated by ANM Self-Improvement Pipeline.
    This specialist handles queries related to {domain}.
    """
    
    DOMAIN_KEYWORDS = {json.dumps(research_data.get("keywords", [domain]))}
    
    def __init__(
        self,
        model_name: str = "deepseek-r1:1.5b",
    ) -> None:
        self.model = model_name
        self.system_prefix = self._build_system_prefix()
    
    def _build_system_prefix(self) -> str:
        return f"""You are the {domain_cap} SPECIALIST of ANM V0-OpenSource.

Your role is to provide expert knowledge and reasoning in the {domain} domain.
You operate as part of a multi-specialist system (TrueWoT).
You DO NOT provide final user-facing answers directly.

DOMAIN EXPERTISE:
- Core concepts in {domain}
- Technical terminology and jargon
- Best practices and methodologies
- Current research and developments

BEHAVIOR:
- Provide accurate, well-reasoned responses
- Cite sources when possible
- Acknowledge uncertainty when present
- Hand off to other specialists when appropriate

Always end with: WOT_REQUEST: <DOMAIN or NONE>
"""
    
    def run(self, wot_packet: str) -> str:
        """
        Main entry point called by Router / TrueWoT.
        
        Args:
            wot_packet: WoT packet containing query and context
        
        Returns:
            Specialist reasoning and WOT_REQUEST
        """
        prompt = (
            self.system_prefix
            + "\\n\\n--- WoT PACKET ---\\n"
            + wot_packet
            + "\\n\\nProvide {domain} domain reasoning and end with WOT_REQUEST."
        )
        
        try:
            proc = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
            
            output = proc.stdout.decode("utf-8", errors="ignore")
            
            # Ensure WOT_REQUEST line exists
            if "WOT_REQUEST:" not in output:
                output += "\\n\\nWOT_REQUEST: NONE"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"[{domain_cap}LLM ERROR: Timeout]\\n\\nWOT_REQUEST: GENERAL"
        except Exception as e:
            return f"[{domain_cap}LLM ERROR: {{e}}]\\n\\nWOT_REQUEST: GENERAL"
    
    def get_domain_keywords(self) -> List[str]:
        """Return keywords for this domain."""
        return self.DOMAIN_KEYWORDS
    
    def can_handle(self, query: str) -> float:
        """
        Return confidence score for handling a query.
        
        Args:
            query: User query
        
        Returns:
            Confidence score 0.0-1.0
        """
        query_lower = query.lower()
        matches = sum(1 for kw in self.DOMAIN_KEYWORDS if kw.lower() in query_lower)
        return min(matches * 0.2, 1.0)
'''
    
    def _generate_training_script(self, domain: str, research_data: Dict[str, Any]) -> str:
        """Generate training script."""
        return f'''# ============================================================
# ANM V0-OpenSource — {domain.upper()} SPECIALIST TRAINING SCRIPT
# ============================================================

"""
Training script for {domain} specialist module.
Uses LoRA/QLoRA for efficient fine-tuning.
"""

from pathlib import Path
import json
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from anm.expansion.training.trainer import LoRATrainer, TrainingConfig
from anm.expansion.training.data_pipeline import DataPipeline


# Configuration
DOMAIN = "{domain}"
DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "checkpoints"


def prepare_data():
    """Prepare training data."""
    pipeline = DataPipeline(output_dir=str(DATA_DIR / "processed"))
    
    # Process raw data
    raw_data_path = DATA_DIR / "raw"
    if raw_data_path.exists():
        result = pipeline.process(
            input_paths=[str(raw_data_path)],
            domain=DOMAIN,
            augment=True,
        )
        return result
    else:
        print(f"No raw data found at {{raw_data_path}}")
        return None


def train():
    """Run training."""
    # Configure training
    config = TrainingConfig(
        base_model="deepseek-r1:1.5b",
        lora_r=16,
        lora_alpha=32,
        use_qlora=True,
        epochs=3,
        batch_size=4,
        learning_rate=2e-4,
    )
    
    # Initialize trainer
    trainer = LoRATrainer(config=config, output_dir=str(OUTPUT_DIR))
    
    # Prepare data
    data_result = prepare_data()
    if data_result is None:
        print("Skipping training - no data available")
        return None
    
    # Run training
    train_path = data_result["output_paths"].get("train")
    eval_path = data_result["output_paths"].get("val")
    
    result = trainer.train(
        train_data_path=train_path,
        eval_data_path=eval_path,
    )
    
    return result


if __name__ == "__main__":
    result = train()
    if result:
        print(f"Training completed: {{result}}")
'''
    
    def _generate_init(self, domain: str) -> str:
        """Generate __init__.py."""
        domain_cap = domain.capitalize()
        return f'''# {domain_cap} Specialist Module (Auto-Generated)

from anm.specialists.{domain}.{domain}_llm import {domain_cap}LLM

__all__ = ["{domain_cap}LLM"]
'''
    
    def _generate_tests(self, domain: str) -> str:
        """Generate test file."""
        domain_cap = domain.capitalize()
        return f'''# ============================================================
# ANM V0-OpenSource — {domain.upper()} SPECIALIST TESTS
# ============================================================

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from anm.specialists.{domain}.{domain}_llm import {domain_cap}LLM


class Test{domain_cap}LLM:
    """Tests for {domain_cap}LLM specialist."""
    
    @pytest.fixture
    def specialist(self):
        return {domain_cap}LLM()
    
    def test_initialization(self, specialist):
        """Test specialist initializes correctly."""
        assert specialist is not None
        assert specialist.model == "deepseek-r1:1.5b"
    
    def test_system_prefix(self, specialist):
        """Test system prefix is generated."""
        prefix = specialist.system_prefix
        assert "{domain}" in prefix.lower() or "{domain_cap}" in prefix
        assert "WOT_REQUEST" in prefix
    
    def test_domain_keywords(self, specialist):
        """Test domain keywords exist."""
        keywords = specialist.get_domain_keywords()
        assert isinstance(keywords, list)
        assert len(keywords) > 0
    
    def test_can_handle(self, specialist):
        """Test can_handle returns confidence score."""
        # Test with domain keyword
        score = specialist.can_handle("{domain}")
        assert 0.0 <= score <= 1.0
        
        # Test with unrelated query
        score = specialist.can_handle("xyz123random")
        assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    def _generate_readme(self, domain: str, research_data: Dict[str, Any]) -> str:
        """Generate README."""
        domain_cap = domain.capitalize()
        return f"""# {domain_cap} Specialist Module

Auto-generated by ANM Self-Improvement Pipeline V2.

## Overview

This specialist module handles queries related to **{domain}**.

## Files

- `{domain}_llm.py` - Main specialist class
- `train.py` - LoRA/QLoRA training script
- `data/` - Training data directory
- `checkpoints/` - Model checkpoints
- `tests/` - Unit tests

## Usage

```python
from anm.specialists.{domain}.{domain}_llm import {domain_cap}LLM

specialist = {domain_cap}LLM()
result = specialist.run(wot_packet)
```

## Training

1. Place training data in `data/raw/`
2. Run training:
```bash
cd anm/specialists/{domain}
python train.py
```

## Testing

```bash
cd anm/specialists/{domain}/tests
pytest test_{domain}_llm.py -v
```

## Research Data

```json
{json.dumps(research_data, indent=2)}
```

---
*Generated by ANM Self-Improvement Pipeline V2*
"""
