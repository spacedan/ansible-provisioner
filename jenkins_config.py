import json
import os
import logging
import xml.etree.cElementTree as ET
from xml.dom import minidom

logger = logging.getLogger('jenkins_config')
hdlr = logging.FileHandler('jenkins_config.log')
formatter = logging. Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

def parse_json(json_file):
    """
    takes the json file and returns the data.
    """
    with open(json_file) as myjson:
        result_json = json.load(myjson)
    return result_json

def write_jenkins_config_xml(data):
    """
    read from the json input file and create a config xml for jenkins
    """
    jenkins_version = data['jenkins_version']
    app_name = data['app']['app_name']
    app_type = data['app']['pipeline']['app_type']

    jenkins_config = open("jenkins_config.xml", "w+")

def write_build_jobs_xml(data):
    """
    """
    build_target = data['app']['pipeline']['build_jobs']['build_target']
    vc_type = data['app']['pipeline']['build_jobs']['version_control']['type']
    vc_url = data['app']['pipeline']['build_jobs']['version_control']['url']
    vc_branch = data['app']['pipeline']['build_jobs']['version_control']['branch']
    app_name = data['app']['app_name']

    project = ET.Element("project")
    actions = ET.SubElement(project, "actions")
    description = ET.SubElement(project, "description")
    keepDependencies = ET.SubElement(project, "keepDependencies")
    properties = ET.SubElement(project, "properties")

    scm = ET.SubElement(project, "scm", **{'class':'hudson.plugins.git.GitSCM', 'plugin':'git@3.7.0'})
    configVersion = ET.SubElement(scm, "configVersion").text = "2"
    userRemoteConfigs = ET.SubElement(scm, "userRemoteConfigs")
    gitRemoteConfig = ET.SubElement(userRemoteConfigs, "hudson.plugins.git.UserRemoteConfig")
    url = ET.SubElement(gitRemoteConfig, "url").text = vc_url.encode("utf-8")

    branches = ET.SubElement(scm, "branches")
    branchSpec = ET.SubElement(branches, "hudson.plugins.git.BranchSpec")
    branchName = ET.SubElement(branchSpec, "name").text = "master"

    generateSubmoduleConfigurations = ET.SubElement(scm, "doGenerateSubmoduleConfigurations").text = "false"
    submoduleCfg = ET.SubElement(scm, "submoduleCfg", **{'class':'list'})
    extensions = ET.SubElement(scm, "extensions")

    canRoam = ET.SubElement(project, "canRoam").text = "true"
    disabled = ET.SubElement(project, "disabled").text = "false"
    blockBuildWhenDownstreamBuilding = ET.SubElement(project, "blockBuildWhenDownstreamBuilding").text = "false"
    blockBuildWhenUpstreamBuilding = ET.SubElement(project, "blockBuildWhenUpstreamBuilding").text = "false"
    triggers = ET.SubElement(project, "triggers")
    concurrentBuild = ET.SubElement(project, "concurrentBuild").text = "false"

    builders = ET.SubElement(project, "builders")
    BapSshBuilderPlugin = ET.SubElement(builders, "jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin", plugin="publish-over-ssh@1.18")
    delegate = ET.SubElement(BapSshBuilderPlugin, "delegate")
    consolePrefix = ET.SubElement(delegate, "consolePrefix").text = "SSH: "
    delegatePlugin = ET.SubElement(delegate, "delegate", plugin="publish-over@0.21")

    publishers = ET.SubElement(delegatePlugin, "publishers")
    bapSshPublisher = ET.SubElement(publishers, "jenkins.plugins.publish__over__ssh.BapSshPublisher", plugin="publish-over-ssh@1.18")
    configName = ET.SubElement(bapSshPublisher, "configName").text = "local.test"
    verbose = ET.SubElement(bapSshPublisher, "verbose").text = "false"
    transfers = ET.SubElement(bapSshPublisher, "transfers")
    bapSshTransfer = ET.SubElement(transfers, "jenkins.plugins.publish__over__ssh.BapSshTransfer")
    remoteDirectory = ET.SubElement(bapSshTransfer, "remoteDirectory").text = ""
    sourceFiles = ET.SubElement(bapSshTransfer, "sourceFiles").text = ""
    excludes = ET.SubElement(bapSshTransfer, "excludes").text = ""
    removePrefix = ET.SubElement(bapSshTransfer, "removePrefix").text = ""
    remoteDirectorySDF = ET.SubElement(bapSshTransfer, "remoteDirectorySDF").text = "false"
    flatten = ET.SubElement(bapSshTransfer, "flatten").text = "false"
    cleanRemote = ET.SubElement(bapSshTransfer, "cleanRemote").text = "false"
    noDefaultExcludes = ET.SubElement(bapSshTransfer, "noDefaultExcludes").text = "false"
    makeEmptyDirs = ET.SubElement(bapSshTransfer, "makeEmptyDirs").text = "false"
    patternSeparator = ET.SubElement(bapSshTransfer, "patternSeparator").text = "[, ]+"
    execCommand = ET.SubElement(bapSshTransfer, "execCommand").text = "git clone https://github.com/spacedan/mage-server.git; cd mage-server; docker-compose up;"
    execTimeout = ET.SubElement(bapSshTransfer, "execTimeout").text = "120000"
    usePty = ET.SubElement(bapSshTransfer, "usePty").text = "false"
    useAgentForwarding = ET.SubElement(bapSshTransfer, "useAgentForwarding").text = "false"

    continueOnError = ET.SubElement(delegatePlugin, "continueOnError").text = "false"
    failOnError = ET.SubElement(delegatePlugin, "failOnError").text = "false"
    alwaysPublishFromMaster = ET.SubElement(delegatePlugin, "alwaysPublishFromMaster").text = "false"
    hostConfigurationAccess = ET.SubElement(delegatePlugin, "hostConfigurationAccess", **{'class':'jenkins.plugins.publish_over_ssh.BapSshPublisherPlugin', 'reference':'../..'})

    prettyxml = minidom.parseString(ET.tostring(project)).toprettyxml(indent="  ")
    filename = "jenkins_configs/jobs/" + app_name + ".xml"
    with open(filename, "w") as f:
        f.write(prettyxml)

def build_jenkins(config_dir):
    """
    """

myjsonfile = "pipeline.json"
json_data = parse_json(myjsonfile)
write_build_jobs_xml(json_data)

