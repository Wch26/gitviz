# GitViz Demo Repository Creator (PowerShell)
# Creates a rich test repository with branches, merges, and tags

$RepoName = "gitviz-demo-repo"
$RepoDir = ".\$RepoName"

Write-Host "🚀 Creating demo repository: $RepoName" -ForegroundColor Cyan

# Remove if exists
if (Test-Path $RepoDir) { Remove-Item -Recurse -Force $RepoDir }

# Initialize
git init $RepoDir
Set-Location $RepoDir

# Configure
git config user.name "Alice Zhang"
git config user.email "alice@example.com"

# ─── Phase 1: Initial project setup ───────────────────
Write-Host "📦 Phase 1: Project initialization"

@"
# My Awesome Project

A web application built with modern technologies.
"@ | Out-File -FilePath README.md -Encoding utf8

@'
<!DOCTYPE html>
<html>
<head><title>My App</title></head>
<body><h1>Hello World</h1></body>
</html>
'@ | Out-File -FilePath index.html -Encoding utf8

git add README.md index.html
git commit -m "🎉 Initial commit: project scaffolding"

git config user.name "Bob Chen"
git config user.email "bob@example.com"

@'
{
  "name": "my-app",
  "version": "0.1.0",
  "description": "My Awesome Project",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "test": "jest"
  }
}
'@ | Out-File -FilePath package.json -Encoding utf8

New-Item -ItemType Directory -Path "src" -Force | Out-Null
@'
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello World'));
app.listen(3000);
'@ | Out-File -FilePath "src/index.js" -Encoding utf8

git add package.json src/index.js
git commit -m "✨ Add Node.js project setup with Express"

# ─── Phase 2: Feature development ─────────────────────
Write-Host "🔧 Phase 2: Feature development"
git config user.name "Alice Zhang"
git config user.email "alice@example.com"

git checkout -b feature/user-auth

@'
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

class AuthService {
  constructor(secret) {
    this.secret = secret;
  }

  async hashPassword(password) {
    return bcrypt.hash(password, 10);
  }

  generateToken(userId) {
    return jwt.sign({ userId }, this.secret, { expiresIn: '7d' });
  }

  verifyToken(token) {
    return jwt.verify(token, this.secret);
  }
}
'@ | Out-File -FilePath "src/auth.js" -Encoding utf8

@'
class User {
  constructor(id, username, email) {
    this.id = id;
    this.username = username;
    this.email = email;
    this.createdAt = new Date();
  }

  toJSON() {
    return { id: this.id, username: this.username, email: this.email };
  }
}

module.exports = User;
'@ | Out-File -FilePath "src/user.js" -Encoding utf8

git add src/auth.js src/user.js
git commit -m "✨ Add user authentication service with JWT"

@"
# My Awesome Project

A web application built with modern technologies.

## Features

- User authentication with JWT
- RESTful API
- PostgreSQL database
- Docker support

## Getting Started

```bash
npm install
npm start
```
"@ | Out-File -FilePath README.md -Encoding utf8

git add README.md
git commit -m "📝 Update README with features and setup instructions"

git checkout main
git merge feature/user-auth --no-ff -m "🔀 Merge feature/user-auth: add authentication system"

# ─── Phase 3: More features ───────────────────────────
Write-Host "🧪 Phase 3: More features"
git checkout -b feature/api-routes

@'
const express = require('express');
const router = express.Router();

router.get('/api/users', (req, res) => {
  res.json({ users: [] });
});

router.post('/api/login', (req, res) => {
  res.json({ token: 'test-token' });
});

router.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() });
});

module.exports = router;
'@ | Out-File -FilePath "src/routes.js" -Encoding utf8

@'
const { Pool } = require('pg');

class Database {
  constructor(config) {
    this.pool = new Pool(config);
  }

  async query(text, params) {
    const result = await this.pool.query(text, params);
    return result.rows;
  }

  async close() {
    await this.pool.end();
  }
}

module.exports = Database;
'@ | Out-File -FilePath "src/database.js" -Encoding utf8

git add src/routes.js src/database.js
git commit -m "✨ Add API routes and database module"

git config user.name "Bob Chen"
git config user.email "bob@example.com"

New-Item -ItemType Directory -Path "tests" -Force | Out-Null
@'
const AuthService = require('../src/auth');

describe('AuthService', () => {
  it('should generate a valid JWT token', () => {
    const auth = new AuthService('test-secret');
    const token = auth.generateToken('user-1');
    expect(token).toBeDefined();
  });
});
'@ | Out-File -FilePath "tests/auth.test.js" -Encoding utf8

git add tests/auth.test.js
git commit -m "✅ Add unit tests for authentication"

git checkout main
git merge feature/api-routes --no-ff -m "🔀 Merge feature/api-routes: add REST API and database"

# ─── Phase 4: Bug fixes ───────────────────────────────
Write-Host "🐛 Phase 4: Bug fixes"
git checkout -b fix/login-bug

@'
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');

class AuthService {
  constructor(secret) {
    if (!secret) throw new Error('Secret is required');
    this.secret = secret;
  }

  async hashPassword(password) {
    if (!password) throw new Error('Password is required');
    return bcrypt.hash(password, 10);
  }

  generateToken(userId) {
    if (!userId) throw new Error('UserId is required');
    return jwt.sign({ userId }, this.secret, { expiresIn: '7d' });
  }

  verifyToken(token) {
    try {
      return jwt.verify(token, this.secret);
    } catch (err) {
      throw new Error('Invalid or expired token');
    }
  }
}

module.exports = AuthService;
'@ | Out-File -FilePath "src/auth.js" -Encoding utf8

git add src/auth.js
git commit -m "🐛 Fix: add input validation to prevent NPE in AuthService"

git checkout main
git merge fix/login-bug --no-ff -m "🔀 Merge fix/login-bug: add input validation"

# ─── Phase 5: Tag release ─────────────────────────────
Write-Host "🏷️ Phase 5: Tag release"
git tag -a v1.0.0 -m "🚀 Release v1.0.0: Initial stable release"

# ─── Show results ─────────────────────────────────────
Write-Host ""
Write-Host "✅ Demo repository created: $RepoDir" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Host "Branch: main (merges from feature branches)"
$commitCount = git rev-list --count HEAD
Write-Host "Total commits: $commitCount"
Write-Host "Branches:"
git branch -a
Write-Host ""
Write-Host "Log preview:"
git log --oneline --graph --all
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Go back
Set-Location ..

Write-Host ""
Write-Host "To start GitViz, run:" -ForegroundColor Yellow
Write-Host "  pip install flask"
Write-Host "  python app.py"
Write-Host "  # Open http://localhost:5000" -ForegroundColor Cyan
