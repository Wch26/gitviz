"""Git operations wrapper - uses subprocess for maximum compatibility."""

import subprocess
import os
import json
from pathlib import Path
from datetime import datetime


class GitError(Exception):
    pass


class GitOps:
    """Wrapper around git CLI commands."""

    def __init__(self, repo_path=None):
        self.repo_path = repo_path

    # ── Helpers ──────────────────────────────────────────

    def _run(self, args, timeout=30):
        """Run a git command in the repo directory. Returns output as string."""
        if not self.repo_path:
            raise GitError("No repository path set")
        cmd = ['git', '-c', 'color.ui=never'] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                cwd=self.repo_path, timeout=timeout
            )
        except FileNotFoundError:
            raise GitError("Git is not installed or not found in PATH")
        except subprocess.TimeoutExpired:
            raise GitError(f"Git command timed out: {' '.join(cmd)}")
        if result.returncode != 0:
            err = (result.stderr or '').strip()[:500]
            print(f"[GitViz ERROR] git {' '.join(args)} failed: {err}")
            raise GitError(f"Git error: {err}")
        return (result.stdout or '').rstrip('\n')

    def _run_simple(self, args, cwd, timeout=10):
        """Run a git command in an arbitrary directory (for repo detection)."""
        try:
            result = subprocess.run(
                ['git', '-c', 'color.ui=never'] + args,
                capture_output=True, text=True,
                encoding='utf-8', errors='replace',
                cwd=cwd, timeout=timeout
            )
            stdout = (result.stdout or '').strip()
            return result.returncode == 0, stdout
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False, ""

    # ── Repo detection ──────────────────────────────────

    def is_git_repo(self, path):
        """Check if *path* is inside a git repository."""
        ok, _ = self._run_simple(['rev-parse', '--git-dir'], path)
        return ok

    def find_git_repos(self, root_path, max_depth=2):
        """Walk *root_path* and find directories that contain a .git folder."""
        found = []
        try:
            root = Path(root_path)
            if not root.is_dir():
                return found
        except (OSError, PermissionError, ValueError) as e:
            print(f"[GitViz] find_git_repos: can't access {root_path}: {e}")
            return found

        # Check the given directory first
        try:
            if (root / '.git').is_dir() or self.is_git_repo(str(root)):
                found.append(str(root.resolve()))
                return found  # if it's a repo, don't look deeper
        except (OSError, PermissionError):
            pass

        # Walk immediate subdirectories (depth 1)
        try:
            for item in root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    try:
                        if (item / '.git').is_dir() or self.is_git_repo(str(item)):
                            found.append(str(item.resolve()))
                    except (OSError, PermissionError):
                        continue
                    if max_depth > 1 and len(found) < 20:
                        # Check one more level
                        try:
                            for sub in item.iterdir():
                                if sub.is_dir() and not sub.name.startswith('.'):
                                    try:
                                        if (sub / '.git').is_dir() or self.is_git_repo(str(sub)):
                                            found.append(str(sub.resolve()))
                                    except (OSError, PermissionError):
                                        continue
                        except (OSError, PermissionError):
                            continue
        except (OSError, PermissionError) as e:
            print(f"[GitViz] find_git_repos: iterdir error for {root_path}: {e}")

        return found[:50]

    # ── Repo info ────────────────────────────────────────

    def get_repo_info(self):
        """Return basic information about the repository (safe - all calls wrapped)."""
        # Current branch
        try:
            current_branch = self._run(['rev-parse', '--abbrev-ref', 'HEAD'])
        except GitError:
            current_branch = 'unknown'

        # Count total commits
        try:
            commit_count = int(self._run(['rev-list', '--count', '--all']))
        except (GitError, ValueError):
            commit_count = 0

        # Get HEAD commit info
        last_commit = None
        try:
            last = self._run(
                ['log', '-1', '--format=%H||%an||%ae||%ad||%s', '--date=format:%Y-%m-%d %H:%M']
            )
            if last:
                parts = last.split('||', 4)
                if len(parts) >= 5:
                    last_commit = {
                        'hash': parts[0],
                        'hash_short': parts[0][:7] if parts[0] else '',
                        'author': parts[1] if len(parts) > 1 else '',
                        'email': parts[2] if len(parts) > 2 else '',
                        'date': parts[3] if len(parts) > 3 else '',
                        'message': parts[4] if len(parts) > 4 else '',
                    }
        except (GitError, IndexError):
            pass

        # Branches
        try:
            branches = self.get_branches()
        except GitError:
            branches = []

        # Remote URL
        try:
            remote = self._run(['remote', 'get-url', 'origin'])
        except GitError:
            remote = ''

        # Has uncommitted changes
        try:
            status = self.get_status()
            has_uncommitted = len(status) > 0
        except GitError:
            has_uncommitted = False

        return {
            'name': Path(self.repo_path).name,
            'path': self.repo_path,
            'current_branch': current_branch,
            'branches': branches,
            'commit_count': commit_count,
            'last_commit': last_commit,
            'remote': remote,
            'has_uncommitted': has_uncommitted,
        }

    def get_branches(self):
        """Return list of branches with metadata."""
        output = self._run([
            'branch', '-a',
            '--format=%(refname:short)||%(upstream:short)||%(objectname:short)'
        ])
        branches = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('||', 2)
            name = parts[0]
            is_remote = name.startswith('remotes/')
            display_name = name.replace('remotes/', '', 1) if is_remote else name
            branches.append({
                'name': name,
                'display_name': display_name,
                'is_remote': is_remote,
                'upstream': parts[1] if len(parts) > 1 else '',
                'short_hash': parts[2] if len(parts) > 2 else '',
            })
        return branches

    def get_current_branch(self):
        """Get current branch name."""
        return self._run(['rev-parse', '--abbrev-ref', 'HEAD'])

    # ── Commit log ───────────────────────────────────────

    def get_commit_log(self, max_count=50, page=1):
        """Get commit history as a list of dicts (newest first)."""
        skip = (page - 1) * max_count
        fmt = '%H||%P||%an||%ae||%ad||%s||%D'

        # Build args — skip only when > 0
        cmd_args = ['log', f'--max-count={max_count}', f'--format={fmt}']
        if skip > 0:
            cmd_args.append(f'--skip={skip}')
        cmd_args.append('--date=format:%Y-%m-%d %H:%M:%S')
        cmd_args.append('--all')

        try:
            raw = self._run(cmd_args)
        except GitError as e:
            print(f"[GitViz ERROR] get_commit_log git command failed: {e}")
            return []

        print(f"[GitViz] git log raw output: {len(raw)} bytes, first 300 chars:")
        print(f"[GitViz]   {raw[:300]}")

        commits = []
        for line in raw.split('\n'):
            line = line.strip()
            if not line:
                continue
            line = line.replace('\r', '')
            parts = line.split('||', 6)
            if len(parts) < 6:
                print(f"[GitViz WARN] Skipping malformed log line (len={len(parts)}): {line[:100]}")
                continue

            ref_names = parts[6] if len(parts) > 6 else ''
            labels = self._parse_refs(ref_names)
            parents = [p for p in parts[1].split() if p]

            # Check if this commit is HEAD
            is_head = any(r.get('type') == 'HEAD' for r in labels)

            commits.append({
                'hash': parts[0],
                'hash_short': parts[0][:7],
                'parents': parents,
                'parent_count': len(parents),
                'is_merge': len(parents) > 1,
                'is_head': is_head,
                'author': parts[2],
                'email': parts[3],
                'date': parts[4],
                'message': parts[5],
                'refs': labels,
                'index': len(commits),
            })

        print(f"[GitViz] Parsed {len(commits)} commits")
        return commits

    def _parse_refs(self, ref_string):
        """Parse git ref string into structured labels."""
        if not ref_string:
            return []
        labels = []
        for ref in ref_string.split(', '):
            ref = ref.strip()
            if not ref:
                continue
            if ref.startswith('tag: '):
                labels.append({'type': 'tag', 'name': ref[5:]})
            elif ' -> ' in ref:
                # HEAD -> branch-name
                parts = ref.split(' -> ')
                if parts[0] == 'HEAD':
                    labels.append({'type': 'HEAD', 'name': parts[-1]})
                else:
                    labels.append({'type': 'branch', 'name': parts[-1]})
            else:
                labels.append({'type': 'branch', 'name': ref})
        return labels

    # ── Commit detail ────────────────────────────────────

    def get_commit_detail(self, commit_hash):
        """Get detailed information about a specific commit."""
        fmt = '%H||%P||%an||%ae||%ad||%s||%D||%b'
        try:
            info = self._run([
                'show', '--stat', f'--format={fmt}',
                '--date=format:%Y-%m-%d %H:%M:%S', commit_hash
            ])
        except GitError as e:
            print(f"[GitViz ERROR] get_commit_detail({commit_hash}) failed: {e}")
            return None

        # Windows compatibility: normalize line endings
        info = info.replace('\r\n', '\n').replace('\r', '')
        lines = info.split('\n')
        if not lines:
            return None

        header_parts = lines[0].split('||', 7)
        if len(header_parts) < 6:
            print(f"[GitViz WARN] Malformed commit detail header: {lines[0][:100]}")
            return None

        parents = [p for p in header_parts[1].split() if p]
        body = header_parts[7] if len(header_parts) > 7 else ''

        # Parse stat lines for changed files
        files = []
        diff_start = 0
        for i, line in enumerate(lines[1:], 1):
            stripped = line.strip()
            if stripped.startswith('diff --git'):
                diff_start = i
                break
            if '|' in stripped and any(c.isdigit() for c in stripped.split('|')[-1]):
                parts = stripped.rsplit('|', 1)
                files.append({
                    'path': parts[0].strip(),
                    'changes': parts[1].strip(),
                })

        # Get actual diff
        diff_text = ''
        if diff_start > 0:
            diff_lines = lines[diff_start:]
            # Take first 200 lines max
            diff_text = '\n'.join(diff_lines[:200])
            if len(diff_lines) > 200:
                diff_text += '\n\n... (diff truncated)'

        return {
            'hash': header_parts[0],
            'hash_short': header_parts[0][:7],
            'parents': parents,
            'parent_count': len(parents),
            'is_merge': len(parents) > 1,
            'author': header_parts[2],
            'email': header_parts[3],
            'date': header_parts[4],
            'message': header_parts[5],
            'refs': self._parse_refs(header_parts[6] if len(header_parts) > 6 else ''),
            'body': body[:500],
            'files': files,
            'diff': diff_text[:10000],
        }

    def get_diff_for_file(self, commit_hash, file_path):
        """Get the diff of a single file in a commit."""
        try:
            return self._run([
                'show', commit_hash, '--', file_path
            ])
        except GitError:
            return ''

    def get_file_at_revision(self, commit_hash, file_path):
        """Get the content of a file at a specific revision."""
        try:
            return self._run(['show', f'{commit_hash}:{file_path}'])
        except GitError:
            return ''

    # ── Archive ──────────────────────────────────────────

    def archive_commit(self, commit_hash, output_dir):
        """Create a ZIP archive of the repo at a specific commit.

        Returns the path to the created archive.
        """
        os.makedirs(output_dir, exist_ok=True)
        repo_name = Path(self.repo_path).name
        archive_name = f'{repo_name}-{commit_hash[:7]}.zip'
        output_path = os.path.join(output_dir, archive_name)

        self._run([
            'archive', '--format=zip',
            f'--output={output_path}',
            commit_hash
        ])
        size = os.path.getsize(output_path)
        return {
            'path': output_path,
            'name': archive_name,
            'size': size,
            'size_display': self._format_size(size),
        }

    # ── Reset ────────────────────────────────────────────

    def reset_to_commit(self, commit_hash, mode='soft'):
        """Reset HEAD to a specific commit.

        Args:
            mode: 'soft' (keep changes staged), 'mixed' (keep changes unstaged),
                  'hard' (discard all changes)
        """
        if mode not in ('soft', 'mixed', 'hard'):
            raise GitError("Mode must be 'soft', 'mixed', or 'hard'")

        # Get info about the target commit before reset
        target_info = self._run([
            'log', '-1', f'--format=%h %s', commit_hash
        ])

        self._run(['reset', f'--{mode}', commit_hash])

        mode_descriptions = {
            'soft': '保留所有更改在工作区（已暂存）',
            'mixed': '保留所有更改在工作区（未暂存）',
            'hard': '丢弃所有更改',
        }

        return {
            'status': 'success',
            'mode': mode,
            'mode_description': mode_descriptions.get(mode, mode),
            'target': target_info,
            'message': f"已{mode}重置到 {target_info}",
        }

    # ── Status ───────────────────────────────────────────

    def get_status(self):
        """Get working tree status (porcelain format)."""
        output = self._run(['status', '--porcelain'])
        changes = []
        for line in output.split('\n'):
            if not line.strip():
                continue
            xy = line[:2]
            path = line[3:]
            change_type = self._interpret_status(xy)
            changes.append({
                'index_status': xy[0],
                'worktree_status': xy[1],
                'path': path,
                'type': change_type,
            })
        return changes

    def _interpret_status(self, xy):
        """Interpret git status codes."""
        mapping = {
            ('M', ' '): 'modified (staged)',
            ('A', ' '): 'added (staged)',
            ('D', ' '): 'deleted (staged)',
            ('R', ' '): 'renamed (staged)',
            ('C', ' '): 'copied (staged)',
            (' ', 'M'): 'modified',
            (' ', 'D'): 'deleted',
            ('?', '?'): 'untracked',
            ('!', '!'): 'ignored',
            ('U', 'U'): 'unmerged',
            ('M', 'M'): 'modified (staged & unstaged)',
        }
        return mapping.get((xy[0], xy[1]), f'status:{xy}')

    # ── Branch operations ────────────────────────────────

    def checkout_branch(self, branch_name):
        """Switch to an existing branch."""
        self._run(['checkout', branch_name])
        return {
            'status': 'success',
            'branch': branch_name,
            'message': f"已切换到分支 {branch_name}",
        }

    def create_branch(self, branch_name, base='HEAD'):
        """Create a new branch."""
        self._run(['branch', branch_name, base])
        return {
            'status': 'success',
            'branch': branch_name,
            'base': base,
            'message': f"已创建分支 {branch_name} (基于 {base})",
        }

    def delete_branch(self, branch_name, force=False):
        """Delete a branch."""
        flag = '-D' if force else '-d'
        self._run(['branch', flag, branch_name])
        return {
            'status': 'success',
            'branch': branch_name,
            'message': f"已删除分支 {branch_name}",
        }

    def get_branch_diff(self, branch_a, branch_b):
        """Get commit difference between two branches."""
        ahead = self._run(['rev-list', '--count', f'{branch_b}..{branch_a}'])
        behind = self._run(['rev-list', '--count', f'{branch_a}..{branch_b}'])
        return {
            'branch_a': branch_a,
            'branch_b': branch_b,
            'ahead': int(ahead),
            'behind': int(behind),
        }

    # ── Stash ────────────────────────────────────────────

    def get_stash_list(self):
        """Get list of stashes."""
        try:
            output = self._run(['stash', 'list', '--format=%gd||%gs'])
        except GitError:
            return []
        stashes = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('||', 1)
            stashes.append({
                'ref': parts[0],
                'message': parts[1] if len(parts) > 1 else '',
            })
        return stashes

    # ── Log (for graph data) ────────────────────────────

    def get_raw_log(self, max_count=100):
        """Minimal log for building the graph topology."""
        fmt = '%H||%P'
        try:
            output = self._run([
                'log', f'--max-count={max_count}',
                f'--format={fmt}', '--all'
            ])
        except GitError:
            return []

        nodes = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('||', 1)
            h = parts[0]
            parents = [p for p in parts[1].split() if p] if len(parts) > 1 else []
            nodes.append({'hash': h, 'parents': parents})
        return nodes

    # ── Helpers ──────────────────────────────────────────

    @staticmethod
    def _format_size(size_bytes):
        """Format byte size to human-readable string."""
        if size_bytes < 1024:
            return f'{size_bytes} B'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} KB'
        else:
            return f'{size_bytes / (1024 * 1024):.1f} MB'
