"""Tests for the configuration loading and merging system"""

from pathlib import Path

import pytest

from cppython.configuration import ConfigurationLoader


class TestConfigurationLoader:
    """Tests for ConfigurationLoader class"""

    def test_load_pyproject_only(self, tmp_path: Path) -> None:
        """Test loading configuration from pyproject.toml only"""
        pyproject_path = tmp_path / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
install-path = ".cppython"
dependencies = ["fmt>=10.0.0"]
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(tmp_path)
        config = loader.load_cppython_table()

        assert config is not None
        assert config['install-path'] == '.cppython'
        assert config['dependencies'] == ['fmt>=10.0.0']

    def test_load_cppython_toml(self, tmp_path: Path) -> None:
        """Test loading configuration from cppython.toml"""
        pyproject_path = tmp_path / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
""",
            encoding='utf-8',
        )

        cppython_path = tmp_path / 'cppython.toml'
        cppython_path.write_text(
            """
[cppython]
install-path = ".cppython"
dependencies = ["fmt>=10.0.0"]
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(tmp_path)
        config = loader.load_cppython_table()

        assert config is not None
        assert config['install-path'] == '.cppython'
        assert config['dependencies'] == ['fmt>=10.0.0']

    def test_load_with_global_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading with global configuration"""
        # Create a fake home directory with global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[cppython]
install-path = "/global/install"
tool-path = "global-tools"

[cppython.providers.conan]
remotes = ["global-remote"]
""",
            encoding='utf-8',
        )

        # Mock Path.home() to return fake home
        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Create project with minimal config
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
dependencies = ["fmt>=10.0.0"]
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is not None
        # Project config overrides global
        assert config['dependencies'] == ['fmt>=10.0.0']
        # Global config provides defaults
        assert config['install-path'] == '/global/install'
        assert config['tool-path'] == 'global-tools'
        assert config['providers']['conan']['remotes'] == ['global-remote']

    def test_local_overrides_highest_priority(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that .cppython.toml has highest priority and overrides all other config sources"""
        # Create fake home with global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[cppython]
install-path = "/global/install"
build-path = "global-build"

[cppython.providers.conan]
remotes = ["global-remote"]
profile_dir = "global-profiles"
""",
            encoding='utf-8',
        )

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Create project
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
dependencies = ["fmt>=10.0.0"]
build-path = "project-build"
""",
            encoding='utf-8',
        )

        # Create local overrides (highest priority)
        local_override_path = project_root / '.cppython.toml'
        local_override_path.write_text(
            """
install-path = "/local/install"
build-path = "local-build"

[providers.conan]
profile_dir = "/local/profiles"
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is not None
        # Local overrides have highest priority - overrides project config
        assert config['build-path'] == 'local-build'
        # Project config is preserved for non-overridden fields
        assert config['dependencies'] == ['fmt>=10.0.0']

        # Local override has highest priority
        assert config['install-path'] == '/local/install'

        # Provider settings: local override takes precedence
        assert config['providers']['conan']['profile_dir'] == '/local/profiles'
        # Global remote preserved since not overridden
        assert config['providers']['conan']['remotes'] == ['global-remote']

    def test_conflicting_configs_error(self, tmp_path: Path) -> None:
        """Test that using both pyproject.toml and cppython.toml raises error"""
        pyproject_path = tmp_path / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
install-path = ".cppython"
""",
            encoding='utf-8',
        )

        cppython_path = tmp_path / 'cppython.toml'
        cppython_path.write_text(
            """
[cppython]
install-path = "/other/path"
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(tmp_path)

        with pytest.raises(ValueError, match='both pyproject.toml and cppython.toml'):
            loader.load_cppython_table()

    def test_deep_merge(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test deep merging of nested dictionaries across all config layers"""
        # Global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[cppython.providers.conan]
remotes = ["global-remote"]
profile_dir = "global-profiles"
skip_upload = false

[cppython.providers.vcpkg]
some_setting = "global-value"
""",
            encoding='utf-8',
        )

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Project config
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython.providers.conan]
remotes = ["project-remote"]

[tool.cppython.providers.vcpkg]
another_setting = "project-value"
""",
            encoding='utf-8',
        )

        # Local overrides
        local_override_path = project_root / '.cppython.toml'
        local_override_path.write_text(
            """
[providers.conan]
profile_dir = "/custom/profiles"

[providers.vcpkg]
some_setting = "override-value"
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is not None
        # Project config overrides everything for conan remotes
        assert config['providers']['conan']['remotes'] == ['project-remote']
        # Local override affects global, then project merges
        assert config['providers']['conan']['profile_dir'] == '/custom/profiles'
        assert config['providers']['conan']['skip_upload'] is False

        # vcpkg: deep merge across all layers
        assert config['providers']['vcpkg']['some_setting'] == 'override-value'
        assert config['providers']['vcpkg']['another_setting'] == 'project-value'

    def test_list_override_in_project_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that project config list values override global completely"""
        # Global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[cppython]
dependencies = ["fmt>=10.0.0", "spdlog>=1.12.0"]
""",
            encoding='utf-8',
        )

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Project config
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
dependencies = ["catch2>=3.0.0"]
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is not None
        # Project list replaces global entirely
        assert config['dependencies'] == ['catch2>=3.0.0']

    def test_config_source_info(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test config_source_info returns correct existence flags"""
        # Create fake home with global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text('[cppython]\ninstall-path = "/path"', encoding='utf-8')

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Create project
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text('[project]\nname = "test"', encoding='utf-8')

        local_override_path = project_root / '.cppython.toml'
        local_override_path.write_text('install-path = "/local"', encoding='utf-8')

        loader = ConfigurationLoader(project_root)
        info = loader.config_source_info()

        assert info['global_config'] is True
        assert info['pyproject'] is True
        assert info['cppython'] is False
        assert info['local_overrides'] is True

    def test_no_cppython_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when no CPPython configuration exists anywhere"""
        # No global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Project with no cppython config
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is None

    def test_only_local_overrides(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test local overrides when no global or project config exists"""
        # No global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Project with only local overrides
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"
""",
            encoding='utf-8',
        )

        local_override_path = project_root / '.cppython.toml'
        local_override_path.write_text(
            """
install-path = "/custom/path"

[providers.conan]
remotes = ["my-remote"]
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(project_root)
        config = loader.load_cppython_table()

        assert config is not None
        assert config['install-path'] == '/custom/path'
        assert config['providers']['conan']['remotes'] == ['my-remote']

    def test_global_config_missing_cppython_table(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that global config.toml without [cppython] table raises error"""
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[other]
some_value = "value"
""",
            encoding='utf-8',
        )

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text('[project]\nname = "test"', encoding='utf-8')

        loader = ConfigurationLoader(project_root)

        with pytest.raises(ValueError, match='must contain a \\[cppython\\] table'):
            loader.load_global_config()

    def test_cppython_toml_missing_cppython_table(self, tmp_path: Path) -> None:
        """Test that cppython.toml without [cppython] table raises error"""
        pyproject_path = tmp_path / 'pyproject.toml'
        pyproject_path.write_text('[project]\nname = "test"', encoding='utf-8')

        cppython_path = tmp_path / 'cppython.toml'
        cppython_path.write_text(
            """
[other]
some_value = "value"
""",
            encoding='utf-8',
        )

        loader = ConfigurationLoader(tmp_path)

        with pytest.raises(ValueError, match='must contain a \\[cppython\\] table'):
            loader.load_cppython_config()

    def test_get_project_data(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test get_project_data returns merged data in pyproject format"""
        # Global config
        fake_home = tmp_path / 'home'
        fake_home.mkdir()
        global_config_dir = fake_home / '.cppython'
        global_config_dir.mkdir()
        global_config_path = global_config_dir / 'config.toml'
        global_config_path.write_text(
            """
[cppython]
install-path = "/global/install"
""",
            encoding='utf-8',
        )

        monkeypatch.setattr(Path, 'home', lambda: fake_home)

        # Project config
        project_root = tmp_path / 'project'
        project_root.mkdir()
        pyproject_path = project_root / 'pyproject.toml'
        pyproject_path.write_text(
            """
[project]
name = "test-project"
version = "1.0.0"

[tool.cppython]
dependencies = ["fmt>=10.0.0"]
""",
            encoding='utf-8',
        )

        # Local overrides
        local_override_path = project_root / '.cppython.toml'
        local_override_path.write_text('install-path = "/custom/path"', encoding='utf-8')

        loader = ConfigurationLoader(project_root)
        project_data = loader.get_project_data()

        assert project_data['project']['name'] == 'test-project'
        # Project config has priority
        assert project_data['tool']['cppython']['dependencies'] == ['fmt>=10.0.0']
        # Local override affects global, then merged with project
        assert project_data['tool']['cppython']['install-path'] == '/custom/path'
