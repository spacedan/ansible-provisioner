import json
import os
import logging
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import parse, tostring
from xml.dom import minidom

logger = logging.getLogger('jenkins_config')
hdlr = logging.FileHandler('jenkins_config.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

"""
take the json file and return the data.
"""
json_file = 'pipeline.json'
logger.info('loading json file '.format(json_file))
with open(json_file) as myjson:
    result_json = json.load(myjson)
json_data = json.load(open(json_file))
build_target = json_data['app']['pipeline']['build_jobs']['build_target']

deploylocal = True
ansibleargs = "-c local"

if build_target != 'localhost':
    deploylocal = False
    ansibleargs = ''

def write_jenkins_config_xml(data):
    """
    read from the json input file and create a config xml for jenkins
    """
    jenkins_version = data['jenkins_version']
    app_name = data['app']['app_name']
    app_type = data['app']['pipeline']['app_type']
    config = parse('jenkins-configs/config.xml')
    root = config.getroot()

    version = config.findall('version')[0]
    version.text = str(jenkins_version)
    first_job = config.find('hudson/views/au.com.centrumsystems.hudson.plugin.buildpipeline.BuildPipelineView/gridBuilder/firstJob')
    first_job.text = '{0}-build'.format(app_name)
    logger.info('writing jenkins config')
    jenkins_config = open("jenkins-configs/config.xml", "w+")

    prettyxml = minidom.parseString(ET.tostring(config)).toprettyxml(indent="  ")
    filename = 'jenkins-configs/config.xml'
    logger.info('writing jenkins config')
    with open(filename, "w") as f:
        f.write(prettyxml)

def write_build_job_xml(data):
    """
    For each of the build jobs, write the config xml with appropriate input
    """
    vc_type = data['app']['pipeline']['build_jobs']['version_control']['type']
    vc_url = data['app']['pipeline']['build_jobs']['version_control']['url']
    vc_branch = data['app']['pipeline']['build_jobs']['version_control']['branch']
    build_target = data['app']['pipeline']['build_jobs']['build_target']
    app_name = data['app']['app_name']

    doc = parse('templates/buildconfig.xml')

    git_url = doc.find('project/scm/UserRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url')
    git_url.text = str(vc_url)

    git_branch = doc.find('project/scm/branches/hudson.plugins.git.BranchSpec/name')
    git_branch.text = str(vc_branch)

    target = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/configName')
    target = str(build_target)

    prettyxml = minidom.parseString(ET.tostring(doc)).toprettyxml(indent="  ")
    directory = 'jenkins-configs/jobs/{0}-build'.format(app_name)
    logger.info('creating job directory: {0}'.format(directory))
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = '{0}/config.xml'.format(directory)
    with open(filename, "w") as f:
        f.write(prettyxml)

def write_unit_test_job_xml(data):
    """
    For each test job in the json, create a job config xml for jenkins
    """
    app_name = data['app']['app_name']
    test_command = data['app']['pipeline']['test_jobs']['unit_test']['test_command']
    test_target = data['app']['pipeline']['deploy_jobs']['deploy_target']

    doc = parse('templates/unittestconfig.xml')

    build_trigger = doc.find('project/triggers/jenkins.triggers.ReverseBuildTrigger/upstreamProjects')
    target = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/configName')
    target = str(test_target)
    command = doc.find('project/builders/jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin/delegate/delegate/publishers/jenkins.plugins.publish__over__ssh.BapSshPublisher/transfers/jenkins.plugins.publish__over__ssh.BapSshTransfer/execCommand')
    command = str(test_command)

    prettyxml = minidom.parseString(ET.tostring(doc)).toprettyxml(indent="  ")
    directory = 'jenkins-configs/jobs/{0}-unit-test'.format(app_name)
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = '{0}/config.xml'.format(directory)
    with open(filename, "w") as f:
        f.write(prettyxml)

def build_jenkins(target, args):
    """
    Run ansible playook command to launch jenkins locally
    """
    os.system('ansible-playbook -i "{0}" "{1}"'.format(target, args))

myjsonfile = 'pipeline.json'
json_data = json.load(open(myjsonfile))
write_jenkins_config_xml(json_data)
write_build_job_xml(json_data)
write_unit_test_job.xml(json_data)


