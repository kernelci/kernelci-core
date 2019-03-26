import kernelci.configs

def test_build_configs_parsing():
    """ Verify build-configs.yaml """
    configs = kernelci.configs.builds_from_yaml("build-configs.yaml")
    assert len(configs) == 4
    for key in ['build_configs', 'build_environments', 'fragments', 'trees']:
        assert key in configs
        assert len(configs[key]) > 0

def test_build_configs_parsing_minimal():
    configs = kernelci.configs.builds_from_yaml("tests/configs/minimal.yaml")
    assert 'agross' in configs['build_configs']
    assert 'agross' in configs['trees']
    assert 'gcc-7' in configs['build_environments']
    assert len(configs['fragments']) == 0

def test_build_configs_parsing_empty_architecture():
    configs = kernelci.configs.builds_from_yaml("tests/configs/empty-architecture.yaml")
    assert len(configs) == 4

def test_architecture_init_name_only():
    architecture = kernelci.configs.Architecture("arm")
    assert architecture.name == 'arm'
    assert architecture.base_defconfig == 'defconfig'
    assert architecture.extra_configs == []
    assert architecture.fragments == []
    assert architecture._filters == [] # filters does not have a property..
