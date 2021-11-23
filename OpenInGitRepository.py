import os
import re
import subprocess
import webbrowser
from urllib.parse import urlparse

import sublime
import sublime_plugin


class OpenInGitRepositoryCommand(sublime_plugin.WindowCommand):
    def run(self):
        project_root = self._get_project_root()
        remote_url = self._get_remote_url(project_root)
        remote_url = self._normalize_remote_url(remote_url)
        project_file_path = self._get_file_project_path(project_root)
        line_suffix = self._get_line_suffix()
        remote_file_url = self._get_remote_file_url(
            remote_url,
            project_root,
            project_file_path,
            line_suffix
        )
        webbrowser.open(remote_file_url)

    def is_enabled(self):
        file_name = self.window.active_view().file_name()
        project_root = self._get_project_root()
        return (file_name and len(file_name) > 0 and project_root is not None)

    def _get_project_root(self):
        file_path = self.window.active_view().file_name()
        dir_path = os.path.dirname(file_path)
        if not self._is_git_repository(dir_path):
            return None
        output = subprocess.check_output(
            ['git', '-C', dir_path, 'rev-parse', '--show-toplevel'])
        return output.decode('utf-8').strip()

    def _is_git_repository(self, path):
        exit_code = subprocess.call(
            ['git', '-C', path, 'rev-parse'], stdout=open(os.devnull, 'w'),
            stderr=subprocess.STDOUT)
        return exit_code == 0

    def _get_current_branch(self, project_root):
        output = subprocess.check_output(
            ['git', '-C', project_root, 'rev-parse', '--abbrev-ref', 'HEAD'])
        return output.decode('utf-8').strip()

    def _get_remote_url(self, path):
        output = subprocess.check_output(['git', '-C', path, 'remote', '-v'])
        output = output.decode('utf-8')
        if not output:
            return None
        match = re.match(r'[\w-]+\s(.+)(?= )', output)
        return match.group(1)

    def _normalize_remote_url(self, url):
        if url.startswith('https://'):
            return re.sub(r'\.git$', '', url)
        url_parts = re.match(r'^\w+@(.+):(.+?)(?!.git)?$', url)
        url_host = url_parts.group(1)
        url_path = re.sub(r'\.git$', '', url_parts.group(2))
        return 'https://' + url_host + '/' + url_path

    def _get_file_project_path(self, project_path):
        file_path = self.window.active_view().file_name()
        return re.sub(project_path, '', file_path)[1:]

    def _get_line_suffix(self):
        view = self.window.active_view()
        selection = view.sel()[0]
        start = view.rowcol(selection.begin())[0] + 1
        end = view.rowcol(selection.end())[0] + 1
        if start == end:
            return "#L%s" % (start) if start != 1 else ""
        return "#L%s-L%s" % (start, end)

    def _get_remote_file_url(
            self, remote_url, project_root, project_file_path, line_suffix):
        host = urlparse(remote_url).netloc
        branch = self._get_current_branch(project_root)
        path_modifiers = {
            'bitbucket.org': 'src'
        }
        path_modifier = path_modifiers.get(host, 'blob')
        return '/'.join([
            remote_url,
            path_modifier,
            branch,
            project_file_path + line_suffix])
