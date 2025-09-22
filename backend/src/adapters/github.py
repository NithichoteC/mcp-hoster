"""
GitHub MCP Server Adapter
Auto-discovers and configures MCP servers from GitHub repositories
"""
import os
import re
import json
import tempfile
import shutil
from typing import Dict, Any, Optional, List
from pathlib import Path
import httpx
from loguru import logger

class GitHubAdapter:
    """Adapter for discovering and configuring MCP servers from GitHub"""

    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.session = httpx.AsyncClient()

    async def analyze_repository(self, github_url: str) -> Dict[str, Any]:
        """Analyze GitHub repository to extract MCP server configuration"""
        try:
            # Parse GitHub URL
            repo_info = self._parse_github_url(github_url)
            if not repo_info:
                raise ValueError("Invalid GitHub URL")

            logger.info(f"Analyzing repository: {repo_info['owner']}/{repo_info['repo']}")

            # Get repository information
            repo_data = await self._get_repo_data(repo_info["owner"], repo_info["repo"])

            # Get repository files
            files = await self._get_repo_files(repo_info["owner"], repo_info["repo"])

            # Analyze for MCP server type
            server_config = await self._detect_mcp_server_type(repo_data, files, repo_info)

            return server_config

        except Exception as e:
            logger.error(f"Failed to analyze repository {github_url}: {e}")
            raise

    def _parse_github_url(self, url: str) -> Optional[Dict[str, str]]:
        """Parse GitHub URL to extract owner and repo"""
        patterns = [
            r"https://github\.com/([^/]+)/([^/]+)/?",
            r"git@github\.com:([^/]+)/([^/]+)\.git",
            r"([^/]+)/([^/]+)"  # Simple owner/repo format
        ]

        for pattern in patterns:
            match = re.match(pattern, url.strip())
            if match:
                owner, repo = match.groups()
                # Remove .git suffix if present
                repo = repo.replace(".git", "")
                return {"owner": owner, "repo": repo}

        return None

    async def _get_repo_data(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository metadata from GitHub API"""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        response = await self.session.get(url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _get_repo_files(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """Get repository file list recursively"""
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        response = await self.session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("tree", [])

    async def _get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Get content of a specific file"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        response = await self.session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Decode base64 content
        import base64
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content

    async def _detect_mcp_server_type(
        self,
        repo_data: Dict[str, Any],
        files: List[Dict[str, Any]],
        repo_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Detect MCP server type and generate configuration"""

        file_names = [f["path"] for f in files if f["type"] == "blob"]

        # Check for Python MCP server
        if any(f.endswith((".py",)) for f in file_names):
            return await self._analyze_python_mcp_server(repo_data, files, repo_info)

        # Check for Node.js MCP server
        elif "package.json" in file_names:
            return await self._analyze_nodejs_mcp_server(repo_data, files, repo_info)

        # Check for specific known servers
        elif any("n8n" in f.lower() for f in file_names):
            return await self._analyze_n8n_mcp_server(repo_data, repo_info)

        # Generic MCP server
        else:
            return await self._analyze_generic_mcp_server(repo_data, files, repo_info)

    async def _analyze_python_mcp_server(
        self,
        repo_data: Dict[str, Any],
        files: List[Dict[str, Any]],
        repo_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze Python-based MCP server"""
        try:
            # Look for main entry point
            entry_points = [
                "main.py",
                "server.py",
                "app.py",
                "__main__.py"
            ]

            main_file = None
            for entry in entry_points:
                if entry in [f["path"] for f in files]:
                    main_file = entry
                    break

            if not main_file:
                # Look for Python files in src/ or root
                py_files = [f["path"] for f in files if f["path"].endswith(".py")]
                if py_files:
                    main_file = py_files[0]  # Use first Python file

            # Check for requirements.txt or pyproject.toml
            has_requirements = "requirements.txt" in [f["path"] for f in files]
            has_pyproject = "pyproject.toml" in [f["path"] for f in files]

            # Generate configuration
            config = {
                "name": repo_data.get("name", repo_info["repo"]),
                "description": repo_data.get("description", "Python MCP Server"),
                "command": "python",
                "args": [main_file] if main_file else ["server.py"],
                "env": {},
                "setup_commands": []
            }

            # Add setup commands if needed
            if has_requirements:
                config["setup_commands"].append("pip install -r requirements.txt")
            elif has_pyproject:
                config["setup_commands"].append("pip install .")

            return config

        except Exception as e:
            logger.error(f"Failed to analyze Python MCP server: {e}")
            raise

    async def _analyze_nodejs_mcp_server(
        self,
        repo_data: Dict[str, Any],
        files: List[Dict[str, Any]],
        repo_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze Node.js-based MCP server"""
        try:
            # Get package.json content
            package_content = await self._get_file_content(
                repo_info["owner"],
                repo_info["repo"],
                "package.json"
            )
            package_data = json.loads(package_content)

            # Determine entry point
            main_script = package_data.get("main", "index.js")
            scripts = package_data.get("scripts", {})

            # Check for start script
            if "start" in scripts:
                command = "npm"
                args = ["start"]
            elif "mcp" in scripts:
                command = "npm"
                args = ["run", "mcp"]
            else:
                command = "node"
                args = [main_script]

            config = {
                "name": package_data.get("name", repo_info["repo"]),
                "description": package_data.get("description", "Node.js MCP Server"),
                "command": command,
                "args": args,
                "env": {},
                "setup_commands": ["npm install"]
            }

            return config

        except Exception as e:
            logger.error(f"Failed to analyze Node.js MCP server: {e}")
            raise

    async def _analyze_n8n_mcp_server(
        self,
        repo_data: Dict[str, Any],
        repo_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze n8n-specific MCP server"""
        return {
            "name": "n8n-mcp",
            "description": "n8n workflow automation MCP server",
            "command": "npx",
            "args": ["@n8n-mcp/server"],
            "env": {
                "N8N_API_URL": "",  # To be configured by user
                "N8N_API_KEY": ""   # To be configured by user
            },
            "setup_commands": []
        }

    async def _analyze_generic_mcp_server(
        self,
        repo_data: Dict[str, Any],
        files: List[Dict[str, Any]],
        repo_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Analyze generic MCP server"""
        file_names = [f["path"] for f in files]

        # Try to detect language and setup
        if "Dockerfile" in file_names:
            command = "docker"
            args = ["run", "--rm", "-i", f"{repo_info['owner']}/{repo_info['repo']}"]
            setup_commands = [f"docker build -t {repo_info['owner']}/{repo_info['repo']} ."]
        elif "go.mod" in file_names:
            command = "go"
            args = ["run", "."]
            setup_commands = ["go mod download"]
        elif "Cargo.toml" in file_names:
            command = "cargo"
            args = ["run"]
            setup_commands = []
        else:
            # Default fallback
            command = "echo"
            args = ["MCP server type not detected"]
            setup_commands = []

        return {
            "name": repo_data.get("name", repo_info["repo"]),
            "description": repo_data.get("description", "Generic MCP Server"),
            "command": command,
            "args": args,
            "env": {},
            "setup_commands": setup_commands
        }

    async def download_and_setup(self, github_url: str, target_dir: str) -> str:
        """Download repository and set up for local execution"""
        try:
            repo_info = self._parse_github_url(github_url)
            if not repo_info:
                raise ValueError("Invalid GitHub URL")

            # Create target directory
            repo_path = Path(target_dir) / repo_info["repo"]
            repo_path.mkdir(parents=True, exist_ok=True)

            # Download repository as ZIP
            zip_url = f"https://github.com/{repo_info['owner']}/{repo_info['repo']}/archive/refs/heads/main.zip"

            response = await self.session.get(zip_url)
            response.raise_for_status()

            # Extract ZIP
            zip_path = repo_path / "repo.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Extract and cleanup
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(repo_path)

            zip_path.unlink()  # Remove ZIP file

            # Find extracted directory and move contents up
            extracted_dirs = [d for d in repo_path.iterdir() if d.is_dir()]
            if extracted_dirs:
                extracted_dir = extracted_dirs[0]
                for item in extracted_dir.iterdir():
                    shutil.move(str(item), str(repo_path / item.name))
                extracted_dir.rmdir()

            logger.info(f"Repository downloaded to: {repo_path}")
            return str(repo_path)

        except Exception as e:
            logger.error(f"Failed to download repository: {e}")
            raise

    async def get_popular_mcp_servers(self) -> List[Dict[str, Any]]:
        """Get list of popular MCP servers from GitHub"""
        try:
            # Search for MCP servers
            search_queries = [
                "mcp server",
                "model context protocol",
                "fastmcp",
                "mcp-server"
            ]

            servers = []
            for query in search_queries:
                url = f"https://api.github.com/search/repositories"
                params = {
                    "q": query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10
                }
                headers = {}
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"

                response = await self.session.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for repo in data.get("items", []):
                        if repo["html_url"] not in [s["url"] for s in servers]:
                            servers.append({
                                "name": repo["name"],
                                "description": repo["description"],
                                "url": repo["html_url"],
                                "stars": repo["stargazers_count"],
                                "language": repo["language"],
                                "updated_at": repo["updated_at"]
                            })

            # Sort by stars and return top 20
            servers.sort(key=lambda x: x["stars"], reverse=True)
            return servers[:20]

        except Exception as e:
            logger.error(f"Failed to get popular MCP servers: {e}")
            return []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()

# Example usage
async def discover_mcp_servers():
    """Discover and list available MCP servers"""
    async with GitHubAdapter() as adapter:
        servers = await adapter.get_popular_mcp_servers()
        return servers