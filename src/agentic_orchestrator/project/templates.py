"""
Project templates for different technology stacks.

Provides boilerplate code and configuration for:
- Next.js + TypeScript + Tailwind CSS
- Python FastAPI
- Solidity (Hardhat)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Supported technology stacks
SUPPORTED_STACKS = {
    "frontend": ["nextjs", "react", "vue"],
    "backend": ["fastapi", "express", "django"],
    "database": ["postgresql", "sqlite", "mongodb"],
    "blockchain": ["ethereum", "solana"],
}


@dataclass
class TemplateFile:
    """A template file to be generated."""
    path: str
    content: str
    is_binary: bool = False


@dataclass
class StackTemplate:
    """Template for a technology stack."""
    name: str
    files: List[TemplateFile]
    dependencies: Dict[str, str]
    dev_dependencies: Dict[str, str]
    scripts: Dict[str, str]


class TemplateManager:
    """
    Manages project templates for different technology stacks.

    Usage:
        manager = TemplateManager()
        files = manager.get_template_files("nextjs")
        for file in files:
            write_file(file.path, file.content)
    """

    def __init__(self, projects_dir: str = "projects"):
        """
        Initialize the template manager.

        Args:
            projects_dir: Base directory for generated projects
        """
        self.projects_dir = Path(projects_dir)

    def get_template_files(
        self,
        frontend: Optional[str] = None,
        backend: Optional[str] = None,
        database: Optional[str] = None,
        blockchain: Optional[str] = None,
    ) -> List[TemplateFile]:
        """
        Get template files for the specified stack.

        Args:
            frontend: Frontend framework (nextjs, react, vue)
            backend: Backend framework (fastapi, express, django)
            database: Database type (postgresql, sqlite, mongodb)
            blockchain: Blockchain platform (ethereum, solana)

        Returns:
            List of TemplateFile objects
        """
        files = []

        # Always include base project files
        files.extend(self._get_base_files())

        # Add stack-specific files
        if frontend:
            files.extend(self._get_frontend_files(frontend))

        if backend:
            files.extend(self._get_backend_files(backend, database))

        if blockchain:
            files.extend(self._get_blockchain_files(blockchain))

        return files

    def _get_base_files(self) -> List[TemplateFile]:
        """Get base project files common to all stacks."""
        return [
            TemplateFile(
                path=".gitignore",
                content="""# Dependencies
node_modules/
__pycache__/
*.py[cod]
.venv/
venv/

# Build outputs
.next/
dist/
build/
*.egg-info/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
*.sqlite
*.db
coverage/
.pytest_cache/
""",
            ),
            TemplateFile(
                path=".moss-project.json",
                content="""{
  "version": "1.0.0",
  "generator": "moss-ao",
  "createdAt": "",
  "planId": "",
  "techStack": {}
}
""",
            ),
            TemplateFile(
                path="docs/api.md",
                content="""# API Documentation

## Overview

This document describes the API endpoints for the project.

## Endpoints

_To be documented during development._

## Authentication

_To be defined._

## Error Handling

_To be defined._
""",
            ),
        ]

    def _get_frontend_files(self, framework: str) -> List[TemplateFile]:
        """Get frontend template files."""
        if framework == "nextjs":
            return self._get_nextjs_files()
        elif framework == "react":
            return self._get_react_files()
        elif framework == "vue":
            return self._get_vue_files()
        return []

    def _get_nextjs_files(self) -> List[TemplateFile]:
        """Get Next.js template files."""
        return [
            TemplateFile(
                path="src/frontend/package.json",
                content="""{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "postcss": "^8.4.31",
    "tailwindcss": "^3.3.5",
    "typescript": "^5.0.0"
  }
}
""",
            ),
            TemplateFile(
                path="src/frontend/tsconfig.json",
                content="""{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
""",
            ),
            TemplateFile(
                path="src/frontend/tailwind.config.ts",
                content="""import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
export default config
""",
            ),
            TemplateFile(
                path="src/frontend/src/app/layout.tsx",
                content="""import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Project',
  description: 'Generated by MOSS.AO',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
""",
            ),
            TemplateFile(
                path="src/frontend/src/app/page.tsx",
                content="""export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome</h1>
        <p className="text-gray-600">Project generated by MOSS.AO</p>
      </div>
    </main>
  )
}
""",
            ),
            TemplateFile(
                path="src/frontend/src/app/globals.css",
                content="""@tailwind base;
@tailwind components;
@tailwind utilities;
""",
            ),
            TemplateFile(
                path="src/frontend/next.config.js",
                content="""/** @type {import('next').NextConfig} */
const nextConfig = {}
module.exports = nextConfig
""",
            ),
        ]

    def _get_react_files(self) -> List[TemplateFile]:
        """Get React (Vite) template files."""
        return [
            TemplateFile(
                path="src/frontend/package.json",
                content="""{
  "name": "frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0"
  }
}
""",
            ),
            TemplateFile(
                path="src/frontend/src/App.tsx",
                content="""function App() {
  return (
    <div className="app">
      <h1>Welcome</h1>
      <p>Project generated by MOSS.AO</p>
    </div>
  )
}

export default App
""",
            ),
            TemplateFile(
                path="src/frontend/src/main.tsx",
                content="""import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
            ),
            TemplateFile(
                path="src/frontend/index.html",
                content="""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Project</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
            ),
        ]

    def _get_vue_files(self) -> List[TemplateFile]:
        """Get Vue template files."""
        return [
            TemplateFile(
                path="src/frontend/package.json",
                content="""{
  "name": "frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0"
  }
}
""",
            ),
            TemplateFile(
                path="src/frontend/src/App.vue",
                content="""<script setup lang="ts">
</script>

<template>
  <div class="app">
    <h1>Welcome</h1>
    <p>Project generated by MOSS.AO</p>
  </div>
</template>

<style scoped>
.app {
  text-align: center;
  padding: 2rem;
}
</style>
""",
            ),
        ]

    def _get_backend_files(
        self,
        framework: str,
        database: Optional[str] = None,
    ) -> List[TemplateFile]:
        """Get backend template files."""
        if framework == "fastapi":
            return self._get_fastapi_files(database)
        elif framework == "express":
            return self._get_express_files(database)
        elif framework == "django":
            return self._get_django_files(database)
        return []

    def _get_fastapi_files(self, database: Optional[str] = None) -> List[TemplateFile]:
        """Get FastAPI template files."""
        db_url = "sqlite:///./app.db"
        if database == "postgresql":
            db_url = "postgresql://user:password@localhost/dbname"
        elif database == "mongodb":
            db_url = "mongodb://localhost:27017/dbname"

        return [
            TemplateFile(
                path="src/backend/requirements.txt",
                content="""fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
alembic>=1.12.0
httpx>=0.24.0
""",
            ),
            TemplateFile(
                path="src/backend/pyproject.toml",
                content="""[project]
name = "backend"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
""",
            ),
            TemplateFile(
                path="src/backend/app/__init__.py",
                content='"""Backend application package."""\n',
            ),
            TemplateFile(
                path="src/backend/app/main.py",
                content=f'''"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="API",
    description="Generated by MOSS.AO",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {{"message": "Welcome to the API"}}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {{"status": "healthy"}}
''',
            ),
            TemplateFile(
                path="src/backend/app/config.py",
                content=f'''"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "API"
    debug: bool = False
    database_url: str = "{db_url}"

    class Config:
        env_file = ".env"


settings = Settings()
''',
            ),
            TemplateFile(
                path="src/backend/app/models/__init__.py",
                content='"""Database models."""\n',
            ),
            TemplateFile(
                path="src/backend/app/routers/__init__.py",
                content='"""API routers."""\n',
            ),
            TemplateFile(
                path="src/backend/tests/__init__.py",
                content='"""Test package."""\n',
            ),
            TemplateFile(
                path="src/backend/tests/test_main.py",
                content='''"""Tests for main application."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
''',
            ),
        ]

    def _get_express_files(self, database: Optional[str] = None) -> List[TemplateFile]:
        """Get Express.js template files."""
        return [
            TemplateFile(
                path="src/backend/package.json",
                content="""{
  "name": "backend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "start": "node dist/index.js",
    "dev": "ts-node-dev --respawn src/index.ts",
    "build": "tsc",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "@types/express": "^4.17.20",
    "@types/cors": "^2.8.15",
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0",
    "ts-node-dev": "^2.0.0"
  }
}
""",
            ),
            TemplateFile(
                path="src/backend/src/index.ts",
                content="""import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Welcome to the API' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
""",
            ),
            TemplateFile(
                path="src/backend/tsconfig.json",
                content="""{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
""",
            ),
        ]

    def _get_django_files(self, database: Optional[str] = None) -> List[TemplateFile]:
        """Get Django template files."""
        return [
            TemplateFile(
                path="src/backend/requirements.txt",
                content="""django>=4.2.0
djangorestframework>=3.14.0
django-cors-headers>=4.3.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
""",
            ),
            TemplateFile(
                path="src/backend/manage.py",
                content='''#!/usr/bin/env python
"""Django management script."""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
''',
            ),
        ]

    def _get_blockchain_files(self, platform: str) -> List[TemplateFile]:
        """Get blockchain template files."""
        if platform == "ethereum":
            return self._get_hardhat_files()
        elif platform == "solana":
            return self._get_anchor_files()
        return []

    def _get_hardhat_files(self) -> List[TemplateFile]:
        """Get Hardhat (Ethereum) template files."""
        return [
            TemplateFile(
                path="contracts/package.json",
                content="""{
  "name": "contracts",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "compile": "hardhat compile",
    "test": "hardhat test",
    "deploy": "hardhat run scripts/deploy.ts"
  },
  "devDependencies": {
    "@nomicfoundation/hardhat-toolbox": "^3.0.0",
    "hardhat": "^2.19.0"
  }
}
""",
            ),
            TemplateFile(
                path="contracts/hardhat.config.ts",
                content="""import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

const config: HardhatUserConfig = {
  solidity: "0.8.20",
  networks: {
    hardhat: {},
  },
};

export default config;
""",
            ),
            TemplateFile(
                path="contracts/contracts/Contract.sol",
                content="""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Contract
 * @dev Base contract generated by MOSS.AO
 */
contract Contract {
    string public name;
    address public owner;

    event NameChanged(string newName);

    constructor(string memory _name) {
        name = _name;
        owner = msg.sender;
    }

    function setName(string memory _name) public {
        require(msg.sender == owner, "Only owner can set name");
        name = _name;
        emit NameChanged(_name);
    }
}
""",
            ),
            TemplateFile(
                path="contracts/scripts/deploy.ts",
                content="""import { ethers } from "hardhat";

async function main() {
  const Contract = await ethers.getContractFactory("Contract");
  const contract = await Contract.deploy("MyContract");
  await contract.waitForDeployment();

  console.log("Contract deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
""",
            ),
            TemplateFile(
                path="contracts/test/Contract.test.ts",
                content="""import { expect } from "chai";
import { ethers } from "hardhat";

describe("Contract", function () {
  it("Should set the right name", async function () {
    const Contract = await ethers.getContractFactory("Contract");
    const contract = await Contract.deploy("Test");

    expect(await contract.name()).to.equal("Test");
  });
});
""",
            ),
        ]

    def _get_anchor_files(self) -> List[TemplateFile]:
        """Get Anchor (Solana) template files."""
        return [
            TemplateFile(
                path="contracts/Anchor.toml",
                content="""[features]
seeds = false
skip-lint = false

[programs.localnet]
program = "..."

[registry]
url = "https://api.apr.dev"

[provider]
cluster = "Localnet"
wallet = "~/.config/solana/id.json"
""",
            ),
            TemplateFile(
                path="contracts/programs/program/src/lib.rs",
                content="""use anchor_lang::prelude::*;

declare_id!("...");

#[program]
pub mod program {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        msg!("Greetings from: {:?}", ctx.program_id);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize {}
""",
            ),
        ]

    def create_project_structure(
        self,
        project_name: str,
        files: List[TemplateFile],
    ) -> Path:
        """
        Create project directory structure with template files.

        Args:
            project_name: Name of the project (will be slugified)
            files: List of template files to create

        Returns:
            Path to the created project directory
        """
        # Slugify project name
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "-"
            for c in project_name.lower()
        ).strip("-")

        project_dir = self.projects_dir / safe_name

        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create files
        for file in files:
            file_path = project_dir / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file.is_binary:
                file_path.write_bytes(file.content.encode() if isinstance(file.content, str) else file.content)
            else:
                file_path.write_text(file.content)

        return project_dir
