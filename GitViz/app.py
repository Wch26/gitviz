"""GitViz - AI-driven Git Repository Visualizer

Flask backend providing a RESTful API for Git operations,
serving a single-page frontend for visual repository management.
"""

import os
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file

from git_ops import GitOps, GitError
import traceback

app = Flask(__name__)

# ── Force JSON errors (no HTML error pages) ────────────

@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON for ALL errors so the frontend never gets HTML."""
    tb = traceback.format_exc()
    print(f"[GitViz FATAL] {tb}")
    response = jsonify({
        'error': str(e),
        'type': type(e).__name__,
    })
    response.status_code = getattr(e, 'code', 500)
    return response

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({'error': 'Method not allowed'}), 405

# ── Configuration ───────────────────────────────────────

# Directory for temporary files (archives, etc.)
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'gitviz')
os.makedirs(TEMP_DIR, exist_ok=True)

# In-memory session: tracks the currently open repository
session = {
    'repo_path': None,
    'git': GitOps(),
}

# ── Helper ──────────────────────────────────────────────

def require_repo():
    """Ensure a repository is loaded; return error JSON if not."""
    if not session['repo_path'] or not session['git'].repo_path:
        return jsonify({'error': 'No repository open'}), 400
    return None

# ── API Routes ──────────────────────────────────────────

# Root: serve the SPA
@app.route('/')
def index():
    return render_template('index.html')

# ── Repository scanning ─────────────────────────────────

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """Scan a directory for git repositories."""
    data = request.get_json() or {}
    path = data.get('path', '')

    if not path:
        return jsonify({'error': 'Path is required'}), 400

    # Normalize path for Windows
    try:
        path = os.path.abspath(os.path.expanduser(path))
    except Exception:
        pass

    print(f"[GitViz] Scanning: {path}")
    if not os.path.isdir(path):
        return jsonify({'error': f'Directory not found: {path}', 'repos': [], 'count': 0}), 200

    git = GitOps()
    try:
        repos = git.find_git_repos(path, max_depth=2)
        print(f"[GitViz] Scan found {len(repos)} repos")
        return jsonify({'repos': repos, 'count': len(repos)})
    except Exception as e:
        print(f"[GitViz] Scan error: {traceback.format_exc()}")
        return jsonify({'error': str(e), 'repos': [], 'count': 0}), 500


@app.route('/api/check', methods=['POST'])
def api_check():
    """Check if a specific path is a git repository."""
    data = request.get_json() or {}
    path = data.get('path', '')

    if not path:
        return jsonify({'error': 'Path is required'}), 400
    if not os.path.isdir(path):
        return jsonify({'error': f'Directory not found: {path}'}), 404

    git = GitOps()
    is_repo = git.is_git_repo(path)
    if is_repo:
        return jsonify({'is_repo': True, 'path': path})
    else:
        return jsonify({'is_repo': False, 'path': path})


@app.route('/api/scan/quick', methods=['GET'])
def api_scan_quick():
    """Quick scan: try to find git repos in common directories."""
    import subprocess
    common_dirs = [
        os.getcwd(),
        os.path.expanduser('~'),
        os.path.join(os.path.expanduser('~'), 'Desktop'),
    ]
    # On Windows, also try these
    if os.name == 'nt':
        common_dirs.extend([
            'C:\\Users',
            os.path.join('C:\\Users', os.environ.get('USERNAME', 'ch')),
        ])

    git = GitOps()
    all_repos = []
    seen = set()

    for d in common_dirs:
        try:
            d = os.path.abspath(d)
        except Exception:
            continue
        if not d or not os.path.isdir(d):
            continue
        try:
            print(f"[GitViz] Quick scan: {d}")
            repos = git.find_git_repos(d, max_depth=1)
            for r in repos:
                if r not in seen:
                    all_repos.append(r)
                    seen.add(r)
        except Exception as e:
            print(f"[GitViz] Scan skipped {d}: {e}")

    print(f"[GitViz] Quick scan complete: {len(all_repos)} repos")
    return jsonify({'repos': all_repos, 'count': len(all_repos)})


@app.route('/api/open', methods=['POST'])
def api_open():
    """Open a repository for the session."""
    data = request.get_json() or {}
    path = data.get('path', '')

    print(f"[GitViz] Opening repo: '{path}'")

    if not path:
        return jsonify({'error': 'Path is required'}), 400

    # Normalize path
    try:
        path = os.path.abspath(os.path.expanduser(path))
    except Exception:
        pass

    if not os.path.isdir(path):
        return jsonify({'error': f'Directory not found: {path}'}), 400

    git = GitOps()
    if not git.is_git_repo(path):
        return jsonify({'error': f'Not a git repository: {path}'}), 400

    # Open the repo
    session['repo_path'] = path
    session['git'] = GitOps(path)

    try:
        info = session['git'].get_repo_info()
        print(f"[GitViz] Repo opened: {info.get('name', '?')} ({info.get('current_branch', '?')}) — {info.get('commit_count', 0)} commits")
        recent_repos = _update_recent_repos(path)
        return jsonify({
            'status': 'ok',
            'info': info,
            'recent_repos': recent_repos,
        })
    except GitError as e:
        print(f"[GitViz ERROR] get_repo_info failed: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"[GitViz FATAL] api_open: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# ── Repository information ──────────────────────────────

@app.route('/api/repo/info', methods=['GET'])
def api_repo_info():
    """Get repository overview information."""
    err = require_repo()
    if err:
        return err
    try:
        return jsonify(session['git'].get_repo_info())
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/branches', methods=['GET'])
def api_repo_branches():
    """List all branches."""
    err = require_repo()
    if err:
        return err
    try:
        return jsonify({'branches': session['git'].get_branches()})
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/log', methods=['GET'])
def api_repo_log():
    """Get commit log (paginated)."""
    err = require_repo()
    if err:
        return err
    try:
        max_count = request.args.get('count', 50, type=int)
        page = request.args.get('page', 1, type=int)
        commits = session['git'].get_commit_log(max_count=max_count, page=page)
        return jsonify({
            'commits': commits,
            'count': len(commits),
            'page': page,
        })
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/status', methods=['GET'])
def api_repo_status():
    """Get working directory status."""
    err = require_repo()
    if err:
        return err
    try:
        return jsonify({'changes': session['git'].get_status()})
    except GitError as e:
        return jsonify({'error': str(e)}), 500

# ── Commit operations ───────────────────────────────────

@app.route('/api/repo/commit/<hash>', methods=['GET'])
def api_commit_detail(hash):
    """Get detailed information about a specific commit."""
    err = require_repo()
    if err:
        return err
    try:
        detail = session['git'].get_commit_detail(hash)
        if not detail:
            return jsonify({'error': 'Commit not found'}), 404
        return jsonify(detail)
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/commit/<hash>/archive', methods=['POST'])
def api_commit_archive(hash):
    """Create a ZIP archive of the repo at a specific commit (returns info)."""
    err = require_repo()
    if err:
        return err
    try:
        result = session['git'].archive_commit(hash, TEMP_DIR)
        return jsonify(result)
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/commit/<hash>/download', methods=['GET'])
def api_commit_download(hash):
    """Download a ZIP archive via browser download."""
    err = require_repo()
    if err:
        return err
    try:
        # Get commit message for better filename
        try:
            detail = session['git'].get_commit_detail(hash)
            commit_msg = detail['message'][:40].replace('/', '_').replace('\\', '_') if detail else ''
        except Exception:
            commit_msg = ''

        result = session['git'].archive_commit(hash, TEMP_DIR)

        # Build a nice download filename: RepoName-abc1234-CommitMessage.zip
        repo_name = Path(session['repo_path']).name
        if commit_msg:
            download_name = f'{repo_name}-{hash[:7]}-{commit_msg}.zip'
        else:
            download_name = f'{repo_name}-{hash[:7]}.zip'
        # Remove any characters unsafe for filenames
        safe_name = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in download_name).strip()

        return send_file(
            result['path'],
            as_attachment=True,
            download_name=safe_name,
            mimetype='application/zip'
        )
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/commit/<hash>/cleanup', methods=['POST'])
def api_commit_cleanup(hash):
    """Clean up the archive file after download."""
    err = require_repo()
    if err:
        return err
    try:
        # Delete any zip files in TEMP_DIR for this commit
        import glob
        patterns = [
            os.path.join(TEMP_DIR, f'*-{hash[:7]}.zip'),
            os.path.join(TEMP_DIR, f'*-{hash[:7]}-*.zip'),
        ]
        for pattern in patterns:
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except OSError:
                    pass
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ── Reset / Checkout ────────────────────────────────────

@app.route('/api/repo/reset', methods=['POST'])
def api_repo_reset():
    """Reset the repository to a specific commit."""
    err = require_repo()
    if err:
        return err
    data = request.get_json() or {}
    commit_hash = data.get('hash', '')
    mode = data.get('mode', 'soft')

    if not commit_hash:
        return jsonify({'error': 'Commit hash is required'}), 400

    try:
        result = session['git'].reset_to_commit(commit_hash, mode)
        return jsonify(result)
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/checkout', methods=['POST'])
def api_repo_checkout():
    """Switch to a branch."""
    err = require_repo()
    if err:
        return err
    data = request.get_json() or {}
    branch = data.get('branch', '')

    if not branch:
        return jsonify({'error': 'Branch name is required'}), 400

    try:
        result = session['git'].checkout_branch(branch)
        info = session['git'].get_repo_info()
        return jsonify({**result, 'info': info})
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/branch/create', methods=['POST'])
def api_branch_create():
    """Create a new branch."""
    err = require_repo()
    if err:
        return err
    data = request.get_json() or {}
    name = data.get('name', '')
    base = data.get('base', 'HEAD')

    if not name:
        return jsonify({'error': 'Branch name is required'}), 400

    try:
        result = session['git'].create_branch(name, base)
        return jsonify(result)
    except GitError as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/repo/branch/delete', methods=['POST'])
def api_branch_delete():
    """Delete a branch."""
    err = require_repo()
    if err:
        return err
    data = request.get_json() or {}
    name = data.get('name', '')
    force = data.get('force', False)

    if not name:
        return jsonify({'error': 'Branch name is required'}), 400

    try:
        result = session['git'].delete_branch(name, force)
        return jsonify(result)
    except GitError as e:
        return jsonify({'error': str(e)}), 500

# ── Stash ───────────────────────────────────────────────

@app.route('/api/repo/stash', methods=['GET'])
def api_stash_list():
    """List stashes."""
    err = require_repo()
    if err:
        return err
    try:
        return jsonify({'stashes': session['git'].get_stash_list()})
    except GitError as e:
        return jsonify({'error': str(e)}), 500

# ── Recent repos ────────────────────────────────────────

RECENT_REPOS_FILE = os.path.join(TEMP_DIR, 'recent_repos.json')


def _get_recent_repos():
    """Load recent repositories list."""
    try:
        if os.path.exists(RECENT_REPOS_FILE):
            with open(RECENT_REPOS_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _update_recent_repos(path):
    """Add a path to recent repositories (deduplicated, max 10)."""
    repos = _get_recent_repos()
    # Remove if exists
    repos = [r for r in repos if r != path]
    # Add to front
    repos.insert(0, path)
    # Keep only 10
    repos = repos[:10]
    try:
        with open(RECENT_REPOS_FILE, 'w') as f:
            json.dump(repos, f)
    except OSError:
        pass
    return repos


@app.route('/api/recent', methods=['GET'])
def api_recent():
    """Get list of recently opened repositories."""
    return jsonify({'repos': _get_recent_repos()})


# ── Main ────────────────────────────────────────────────

if __name__ == '__main__':
    print("=" * 55)
    print("  GitViz — Git Repository Visualizer")
    print("  Open your browser to http://127.0.0.1:5000")
    print("=" * 55)
    app.run(host='127.0.0.1', port=5000, debug=True)
