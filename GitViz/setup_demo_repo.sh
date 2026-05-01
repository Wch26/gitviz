#!/bin/bash
# ============================================================
# GitViz Demo Repository Creator
# Creates a rich test repository with branches, merges, and tags
# ============================================================

REPO_NAME="gitviz-demo-repo"
REPO_DIR="./$REPO_NAME"

echo "🚀 Creating demo repository: $REPO_NAME"

# Remove if exists
rm -rf "$REPO_DIR"

# Initialize
git init "$REPO_DIR"
cd "$REPO_DIR"

# Configure
git config user.name "Alice Zhang"
git config user.email "alice@example.com"

# ─── Phase 1: Initial project setup ───────────────────
echo "📦 Phase 1: Project initialization"

cat > README.md << 'EOF'
# My Awesome Project

A web application built with modern technologies.
EOF

cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>My App</title></head>
<body><h1>Hello World</h1></body>
</html>
EOF

git add README.md index.html
git commit -m "🎉 Initial commit: project scaffolding"

git config user.name "Bob Chen"
git config user.email "bob@example.com"

cat > package.json << 'EOF'
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
EOF

mkdir -p src
cat > src/index.js << 'EOF'
const express = require('express');
const app = express();
app.get('/', (req, res) => res.send('Hello World'));
app.listen(3000);
EOF

git add package.json src/index.js
git commit -m "✨ Add Node.js project setup with Express"

# ─── Phase 2: Feature development ─────────────────────
echo "🔧 Phase 2: Feature development"

git config user.name "Alice Zhang"
git config user.email "alice@example.com"

# Create a feature branch
git checkout -b feature/user-auth

cat > src/auth.js << 'EOF'
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
EOF

cat > src/user.js << 'EOF'
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
EOF

git add src/auth.js src/user.js
git commit -m "✨ Add user authentication service with JWT"

# Update README
cat > README.md << 'EOF'
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
EOF

git add README.md
git commit -m "📝 Update README with features and setup instructions"

# Switch back to main and merge feature branch
git checkout main
git merge feature/user-auth --no-ff -m "🔀 Merge feature/user-auth: add authentication system"

# ─── Phase 3: Additional features ─────────────────────
echo "🧪 Phase 3: More features"

git checkout -b feature/api-routes

cat > src/routes.js << 'EOF'
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
EOF

cat > src/database.js << 'EOF'
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
EOF

git add src/routes.js src/database.js
git commit -m "✨ Add API routes and database module"

git config user.name "Bob Chen"
git config user.email "bob@example.com"

cat > tests/auth.test.js << 'EOF'
const AuthService = require('../src/auth');

describe('AuthService', () => {
  it('should generate a valid JWT token', () => {
    const auth = new AuthService('test-secret');
    const token = auth.generateToken('user-1');
    expect(token).toBeDefined();
  });
});
EOF

mkdir -p tests
git add tests/auth.test.js
git commit -m "✅ Add unit tests for authentication"

# Merge to main
git checkout main
git merge feature/api-routes --no-ff -m "🔀 Merge feature/api-routes: add REST API and database"

# ─── Phase 4: Fixes and polish ────────────────────────
echo "🐛 Phase 4: Bug fixes"

git checkout -b fix/login-bug

cat > src/auth.js << 'EOF'
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
EOF

git add src/auth.js
git commit -m "🐛 Fix: add input validation to prevent NPE in AuthService"

git checkout main
git merge fix/login-bug --no-ff -m "🔀 Merge fix/login-bug: add input validation"

# ─── Phase 5: Tag a release ──────────────────────────
echo "🏷️ Phase 5: Tag release"

git tag -a v1.0.0 -m "🚀 Release v1.0.0: Initial stable release"

# ─── Show results ─────────────────────────────────────
echo ""
echo "✅ Demo repository created: $REPO_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Branch: main (with feature/user-auth, feature/api-routes, fix/login-bug merged)"
echo "Total commits: $(git rev-list --count HEAD)"
echo "Branches:"
git branch -a
echo ""
echo "Log preview:"
git log --oneline --graph --all
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Run the following to start GitViz:"
echo "  cd .."
echo "  pip install flask"
echo "  python app.py"
echo "  # Open http://localhost:5000"
