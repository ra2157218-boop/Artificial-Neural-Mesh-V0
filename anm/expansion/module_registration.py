# ============================================================
# ANM V0-OpenSource — MODULE REGISTRATION SYSTEM
#  Part of Self-Improvement Pipeline (Stage 3.11)
# ============================================================

from __future__ import annotations
from typing import Dict, Any, Optional, List
import os
import json
import re
import shutil
from pathlib import Path


class ModuleRegistration:
    """
    Module Registration System for Self-Improvement Pipeline.
    
    Responsibilities:
      - Dynamically adds new domain to Router.VALID_DOMAINS
      - Updates TrueWoT to include new domain in graph
      - Registers specialist in Router's specialist dict
      - Updates configuration files
      - Creates backup before modifications
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / ".anm_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def register_new_module(
        self,
        new_domain: str,
        module_path: str,
        specialist_class_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new specialist module in ANM.
        
        Args:
            new_domain: Domain name (e.g., "geology")
            module_path: Path to the module file
            specialist_class_name: Name of the specialist class (e.g., "GeologyLLM")
        
        Returns:
            Dict with registration status and updated file paths
        """
        if specialist_class_name is None:
            specialist_class_name = f"{new_domain.capitalize()}LLM"
        
        registration_results = {}
        
        # 1. Update Router.VALID_DOMAINS
        router_result = self._update_router(new_domain)
        registration_results["router"] = router_result
        
        # 2. Update Router.__init__ to include new specialist
        router_init_result = self._update_router_init(new_domain, specialist_class_name)
        registration_results["router_init"] = router_init_result
        
        # 3. Update config/settings.py
        config_result = self._update_config(new_domain)
        registration_results["config"] = config_result
        
        # 4. Update TrueWoT (if needed)
        wot_result = self._update_wot(new_domain)
        registration_results["wot"] = wot_result
        
        # 5. Create registration manifest
        manifest_result = self._create_manifest(new_domain, module_path, specialist_class_name)
        registration_results["manifest"] = manifest_result
        
        success = all(
            r.get("success", False) for r in registration_results.values()
        )
        
        return {
            "success": success,
            "new_domain": new_domain,
            "module_path": module_path,
            "specialist_class_name": specialist_class_name,
            "registration_results": registration_results,
        }
    
    def _backup_file(self, file_path: Path) -> Path:
        """Create a backup of a file before modification."""
        backup_path = self.backup_dir / f"{file_path.name}.backup"
        if file_path.exists():
            shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _update_router(self, new_domain: str) -> Dict[str, Any]:
        """Update Router.VALID_DOMAINS to include new domain."""
        router_file = self.project_root / "anm" / "router" / "router.py"
        
        if not router_file.exists():
            return {"success": False, "error": "Router file not found"}
        
        self._backup_file(router_file)
        
        try:
            with open(router_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Find VALID_DOMAINS set
            pattern = r'(VALID_DOMAINS\s*=\s*\{[^}]+)'
            match = re.search(pattern, content, re.MULTILINE)
            
            if match:
                # Add new domain before closing brace
                old_domains = match.group(0)
                if f'"{new_domain}"' not in old_domains:
                    new_domains = old_domains.rstrip("}") + f'\n        "{new_domain}",\n    }}'
                    content = content.replace(old_domains, new_domains)
                    
                    with open(router_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    return {"success": True, "updated": True}
                else:
                    return {"success": True, "updated": False, "note": "Domain already exists"}
            else:
                return {"success": False, "error": "Could not find VALID_DOMAINS"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_router_init(self, new_domain: str, specialist_class_name: str) -> Dict[str, Any]:
        """Update Router.__init__ to initialize new specialist."""
        router_file = self.project_root / "anm" / "router" / "router.py"
        
        if not router_file.exists():
            return {"success": False, "error": "Router file not found"}
        
        try:
            with open(router_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check if import exists
            import_pattern = f"from anm.specialists.{new_domain}_llm import {specialist_class_name}"
            if import_pattern not in content:
                # Add import at top (after other specialist imports)
                import_section = f"from anm.specialists.{new_domain}_llm import {specialist_class_name}"
                # Find a good place to insert (after other specialist imports)
                lines = content.split("\n")
                insert_idx = None
                for i, line in enumerate(lines):
                    if "from anm.specialists" in line and "import" in line:
                        insert_idx = i + 1
                        break
                
                if insert_idx:
                    lines.insert(insert_idx, import_section)
                    content = "\n".join(lines)
            
            # Add specialist initialization in __init__
            init_pattern = rf'(self\.\w+\s*=\s*ParallelSpecialistAdapter\([^)]+\))'
            # Find where to insert (after other specialists, before executive modules)
            lines = content.split("\n")
            insert_idx = None
            for i, line in enumerate(lines):
                if "self.facts = ParallelSpecialistAdapter" in line:
                    insert_idx = i + 1
                    break
            
            if insert_idx:
                specialist_init = f'''        self.{new_domain} = ParallelSpecialistAdapter(
            {specialist_class_name},
            n_workers=self.parallel_workers,
            name="{new_domain}",
        )'''
                lines.insert(insert_idx, specialist_init)
                content = "\n".join(lines)
            
            # Add to all_specialists dict
            all_specialists_pattern = r'(all_specialists:\s*Dict\[str,\s*Any\]\s*=\s*\{[^}]+)'
            match = re.search(all_specialists_pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                old_dict = match.group(0)
                if f'"{new_domain}": self.{new_domain}' not in old_dict:
                    # Add before closing brace
                    new_dict = old_dict.rstrip("}") + f'\n            "{new_domain}": self.{new_domain},\n        }}'
                    content = content.replace(old_dict, new_dict)
            
            with open(router_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {"success": True, "updated": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_config(self, new_domain: str) -> Dict[str, Any]:
        """Update config/settings.py to include new domain model."""
        config_file = self.project_root / "anm" / "config" / "settings.py"
        
        if not config_file.exists():
            return {"success": False, "error": "Config file not found"}
        
        self._backup_file(config_file)
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add model config
            model_config_name = f"MODEL_{new_domain.upper()}"
            if model_config_name not in content:
                # Find where to insert (after other model configs)
                lines = content.split("\n")
                insert_idx = None
                for i, line in enumerate(lines):
                    if "MODEL_BIOLOGY" in line:
                        insert_idx = i + 1
                        break
                
                if insert_idx:
                    model_line = f'MODEL_{new_domain.upper():<20} = "deepseek-r1:1.5b"'
                    lines.insert(insert_idx, model_line)
                    content = "\n".join(lines)
            
            with open(config_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {"success": True, "updated": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _update_wot(self, new_domain: str) -> Dict[str, Any]:
        """Update TrueWoT to include new domain (if needed)."""
        # TrueWoT is typically domain-agnostic, so this might not need changes
        # But we can log that the domain is available
        return {
            "success": True,
            "note": "TrueWoT is domain-agnostic, no changes needed",
        }
    
    def _create_manifest(
        self, new_domain: str, module_path: str, specialist_class_name: str
    ) -> Dict[str, Any]:
        """Create a registration manifest file."""
        manifest_dir = self.project_root / "anm" / "expansion" / "manifests"
        manifest_dir.mkdir(exist_ok=True)
        
        manifest_file = manifest_dir / f"{new_domain}_manifest.json"
        
        manifest = {
            "domain": new_domain,
            "module_path": module_path,
            "specialist_class_name": specialist_class_name,
            "registered_at": str(Path(module_path).stat().st_mtime) if os.path.exists(module_path) else "unknown",
            "status": "registered",
        }
        
        try:
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
            return {"success": True, "manifest_path": str(manifest_file)}
        except Exception as e:
            return {"success": False, "error": str(e)}
