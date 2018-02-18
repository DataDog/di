A5_CHECK_DIR = '/etc/dd-agent/checks.d'
A5_CONF_DIR = '/etc/dd-agent/conf.d'
A5_EXE_PATH = '/opt/datadog-agent/agent/agent.py'

A6_CHECK_DIR = '/etc/datadog-agent/checks.d'
A6_CONF_DIR = '/etc/datadog-agent/conf.d'
A6_EXE_PATH = '/opt/datadog-agent/bin/agent/agent'


def get_agent_exe_path(agent_version_major):
    if int(agent_version_major) >= 6:
        return A6_EXE_PATH
    else:
        return A5_EXE_PATH


def get_conf_path(check, agent_version_major):
    if int(agent_version_major) >= 6:
        return '{conf_dir}/{check}.d/{check}.yaml'.format(conf_dir=A6_CONF_DIR, check=check)
    else:
        return '{conf_dir}/{check}.yaml'.format(conf_dir=A5_CONF_DIR, check=check)


def get_conf_example_glob(check, agent_version_major):
    if int(agent_version_major) >= 6:
        return '{conf_dir}/{check}.d/conf*'.format(conf_dir=A6_CONF_DIR, check=check)
    else:
        return '{conf_dir}/{check}*'.format(conf_dir=A5_CONF_DIR, check=check)
